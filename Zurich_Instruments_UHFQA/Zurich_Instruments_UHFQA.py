# Copyright (C) 2020 Zurich Instruments
#
# This software may be modified and distributed under the terms
# of the MIT license. See the LICENSE file for details.
"""Labber Driver for the Zurich Instruments UHFQA Quantum Analyzer.

This driver provides a high-level interface of the Zurich Instruments
UHFQA Quantum Analyzer for the scientific measurement software Labber.
It is based on the Zurich Instruments Toolkit (zhinst-toolkit), an
extension of our Python API ziPython for high-level instrument control.
"""

import numpy as np
from BaseDriver import LabberDriver, Error

import zhinst.toolkit as tk

# change this value in case you are not using 'localhost'
HOST = "localhost"


class Driver(LabberDriver):
    """Implement a Labber Driver for the Zurich Instruments UHFQA."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controller = None
        self.last_length = []
        self.sequencer_updated = False
        self.waveforms_updated = []
        self.replace_waveform = False

    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection."""
        # Get the interface selected in UI,
        # restrict to either 'USB' or '1GbE'
        interface = self.comCfg.interface
        if not interface == "USB":
            interface = "1GbE"
        # initialize controller and connect
        self.controller = tk.UHFQA(
            self.comCfg.name, self.comCfg.address[:7], interface=interface, host=HOST
        )
        self.controller.setup()
        self.controller.connect_device()
        # Read the revision numbers after the connection
        # and update Labber controller.
        self.update_labber_controller("Revisions - Data Server")
        self.update_labber_controller("Revisions - Firmware")
        self.update_labber_controller("Revisions - FPGA")
        # Initialize last waveform lengths as 0
        self.last_length = [0] * 8

    def performClose(self, bError=False, options={}):
        """Perform the close instrument connection operation."""
        pass

    def initSetConfig(self):
        """Run before setting values in Set Config."""
        pass

    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform the Set Value instrument operation.

        For numerical quantities, this function returns the
        actual value set by the instrument.
        """
        if quant.set_cmd:
            # if a 'set_cmd' is defined, just set the node
            self.set_node_value(quant, value)
            if quant.datatype == quant.DOUBLE:
                # If the quantity is numerical,
                # read the actual value from the device
                value = self.get_node_value(quant)
        # Update the current local value of the quantity of the driver
        quant.setValue(value)
        # Get the current hardware loop index and total number of
        # points of the hardware loop.
        loop_index, n_HW_loop = self.getHardwareLoopIndex(options)
        # Reset all updated flags to `False`
        if self.isFirstCall(options):
            self.sequencer_updated = False
            self.waveforms_updated = [False] * 2
            self.replace_waveform = False

        # Setup tab
        if quant.name == "Preset - Factory Reset":
            # Load factory preset
            self.controller.factory_reset(sync=True)
        if quant.name == "PQSC - Connect to PQSC":
            # Establish connection to PQSC
            self.connect_to_pqsc(value)

        # sequencer outputs
        if quant.name == "Control - Output 1":
            self.controller.awg.output1(int(value))

        if quant.name == "Control - Output 2":
            self.controller.awg.output2(int(value))

        # sequencer gains
        if quant.name == "Control - Gain 1":
            self.controller.awg.gain1(value)

        if quant.name == "Control - Gain 2":
            self.controller.awg.gain2(value)

        # crosstalk - reset button
        if quant.name == "Crosstalk - Reset":
            self.set_crosstalk_matrix(np.eye(10))

        # integration time
        if quant.name == "Integration - Time":
            self.controller.integration_time(value)
            value = self.controller.integration_time()

        # sequencer start / stop
        if quant.name.endswith("Run"):
            value = self.awg_start_stop(quant, value)

        # all channel parameters
        if quant.name.startswith("Channel"):
            name = quant.name.split(" ")
            i = int(name[1]) - 1
            channel = self.controller.channels[i]
            if name[3] == "Rotation":
                value = channel.rotation(value)
            if name[3] == "Threshold":
                value = channel.threshold(value)
            if name[3] == "Frequency":
                value = channel.readout_frequency(value)
                self.sequencer_updated = True
            if name[3] == "Amplitude":
                value = channel.readout_amplitude(value)
                self.sequencer_updated = True
            if name[3] == "Phase":
                value = channel.phase_shift(value)
                self.sequencer_updated = True
            if name[3] == "Enable":
                channel.enable() if value else channel.disable()
                self.sequencer_updated = True

        # mark sequencer as updated to be recompiled
        if quant.name.startswith("Sequencer") or quant.name in [
            "QA Results - Length",
            "QA Results - HW Averages",
        ]:
            self.sequencer_updated = True

        # sequencer waveform (for 'Simple' sequence)
        if quant.name.startswith("Waveform"):
            ch = int(quant.name[-1]) - 1
            self.waveforms_updated[ch] = True
            if not self.isHardwareLoop(options):
                data = value["y"]
                self.replace_waveform = (
                    True if len(data) == self.last_length[ch] else False
                )
                self.last_length[ch] = len(data)

        if self.isFinalCall(options):
            if self.sequencer_updated:
                # if any sequencers are marked as updated
                if loop_index + 1 == n_HW_loop:
                    self.update_sequencers()
            if any(self.waveforms_updated):
                # queue the waveforms marked as updated to the respective AWG
                self.queue_waveforms(options=options)
            if any(self.waveforms_updated) or self.sequencer_updated:
                # sequencer needs to be recompiled
                if loop_index == 0:
                    self.compile_sequencers()

        # return the value that was set on the device ...
        return value

    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation."""
        if quant.get_cmd:
            # if a 'get_cmd' is defined, use it to return the node value
            value = self.get_node_value(quant)
            # Update the current local value of the quantity of the driver
            quant.setValue(value)
        else:
            # for other quantities, just return current value of control
            value = quant.getValue()

        # Get the current hardware loop index and total number of
        # points of the hardware loop.
        loop_index, n_HW_loop = self.getHardwareLoopIndex(options)

        if quant.name.startswith("Result Vector - QB"):
            # get the result vector
            i = int(quant.name[-2:]) - 1
            data = self.controller.channels[i].result()
            value = quant.getTraceDict(data, x0=0, dx=1)
        if quant.name.startswith("Result Avg - QB"):
            # get the _averaged_ result vector
            i = int(quant.name[-2:]) - 1
            data = self.controller.channels[i].result()
            if self.isHardwareLoop(options):
                value = data[loop_index]
            else:
                value = np.mean(data)
        if quant.name == "Result Demod 1-2":
            # calculate 'demod 1-2' value
            value = self.get_demod_12()
        if quant.name == "QA Monitor - Input 1":
            data = self.controller._get("/qas/0/monitor/inputs/0/wave")
            value = quant.getTraceDict(data, dt=1 / 1.8e9)
        if quant.name == "QA Monitor - Input 2":
            data = self.controller._get("/qas/0/monitor/inputs/1/wave")
            value = quant.getTraceDict(data, dt=1 / 1.8e9)

        return value

    def performArm(self, quant_names, options={}):
        """Perform the instrument arm operation"""
        if self.getValue("QA Results - Enable"):
            self.controller._set("/qas/0/result/enable", 1)
            self.controller.arm()
        if self.getValue("Sequencer - Trigger Mode") in [
            "Receive Trigger",
            "ZSync Trigger",
        ]:
            self.controller.awg.run()

    def update_labber_controller(self, quant_name):
        """Read the quantity from device and update the Labber controller."""
        value = self.readValueFromOther(quant_name)
        self.setValue(quant_name, str(value))

    def set_node_value(self, quant, value):
        """Perform node and parameter set

        This method uses the zhinst-toolkit setter to set the node
        and parameter values.
        """
        if quant.datatype == quant.COMBO:
            # If the quantity type is combo, extract the index and
            # check if a list of command strings is defined
            i = quant.getValueIndex(value)
            if len(quant.cmd_def) == 0:
                self.controller._set(quant.set_cmd, i)
            else:
                self.controller._set(quant.set_cmd, quant.cmd_def[i])
        else:
            # Otherwise, just send the value to the device
            self.controller._set(quant.set_cmd, value)
        return value

    def get_node_value(self, quant):
        """Perform node get

        This method uses the zhinst-toolkit getter to get the node
        and parameter values.
        """
        # Read the value from device
        value = self.controller._get(quant.get_cmd)
        return value

    def awg_start_stop(self, quant, value):
        """Handles setting of nodes with 'set_cmd'."""
        if not self.controller.awg.is_running and value:
            self.controller.awg.run()
        else:
            self.controller.awg.stop()
        if self.controller._get("awgs/0/single"):
            self.controller.awg.wait_done()
        return self.controller.awg.is_running

    def update_sequencers(self):
        """Handles the 'set_sequence_params(...)' for the AWGs."""
        if self.sequencer_updated:
            params = self.get_sequence_params()
            if params["sequence_type"] != "None":
                self.controller.awg.set_sequence_params(**params)
            if params["trigger_mode"] == "ZSync Trigger":
                if params["sequence_type"] == "None":
                    self.controller.awg.set_sequence_params(
                        trigger_mode="ZSync Trigger"
                    )
                # read the relevant settings from the device and update
                # the Labber controller
                self.update_labber_controller("Sequencer - Strobe Slope")
                self.update_labber_controller("Sequencer - Valid Polarity")
                self.update_labber_controller("Sequencer - Valid Index")

    def get_sequence_params(self):
        """Retrieves all sequence parameters from Labber quantities and returns
        them as a dictionary, ready for `set_sequence_params(...)`."""
        base_name = f"Sequencer - "
        params = dict(
            sequence_type=self.getValue(base_name + "Sequence"),
            period=self.getValue(base_name + "Period"),
            trigger_mode=self.getValue(base_name + "Trigger Mode"),
            alignment=self.getValue(base_name + "Alignment"),
            trigger_delay=self.getValue(base_name + "Trigger Delay"),
            readout_length=self.getValue(base_name + "Readout Length"),
            clock_rate=1.8e9,
            latency=self.getValue(base_name + "Latency"),
            dead_time=self.getValue(base_name + "Dead Time"),
        )
        if params["sequence_type"] == "Custom":
            params.update(path=self.getValue("Custom Sequence - Path"))
        if params["sequence_type"] == "Pulsed Spectroscopy":
            params.update(
                pulse_length=self.getValue("Sequencer - Pulse Length"),
                pulse_amplitude=self.getValue("Sequencer - Pulse Amplitude"),
            )
        length = self.controller._get("qas/0/result/length")
        avgs = self.controller._get("qas/0/result/averages")
        params.update(repetitions=length * avgs)
        return params

    def queue_waveforms(self, options={}):
        """Queue waveforms or replace waveforms on AWGs."""
        loop_index, _ = self.getHardwareLoopIndex(options)
        if loop_index == 0 and not self.replace_waveform:
            self.controller.awg.reset_queue()
        if any(self.waveforms_updated):
            w1 = self.getValueArray("Waveform 1")
            w2 = self.getValueArray("Waveform 1")
            if self.replace_waveform:
                self.controller.awg.replace_waveform(w1, w2, i=loop_index)
            else:
                self.controller.awg.queue_waveform(w1, w2)

    def compile_sequencers(self):
        """Handles the compilation and waveform upload of the AWGs."""
        sequence_type = self.getValue("Sequencer - Sequence")
        if sequence_type != "None" and not self.replace_waveform:
            self.controller.awg.compile()
        if sequence_type == "Simple":
            self.controller.awg.upload_waveforms()

    def set_crosstalk_matrix(self, matrix):
        """Set the crosstalk matrix as a 2D numpy array."""
        rows, cols = matrix.shape
        for r in range(rows):
            for c in range(cols):
                self.setValue(f"Crosstalk - {r+1} , {c+1}", matrix[r, c])
        self.controller.crosstalk_matrix(matrix)

    def get_demod_12(self):
        """Assembles a complex value from real valued data on channel 1 and 2.
        The returned data will be (channel 1) + i * (channel 2).
        """
        data1 = self.controller.channels[0].result()
        data2 = self.controller.channels[1].result()
        real = np.mean(np.real(data1))
        imag = np.mean(np.real(data2))
        return real + 1j * imag

    def connect_to_pqsc(self, value):
        if value:
            self.controller.enable_qccs_mode()
            self.update_labber_controller("Device - Reference Clock")
            self.update_labber_controller("Digital I/O - Ext Clock")
            self.update_labber_controller("Digital I/O - Mode")
            self.update_labber_controller("Digital I/O - Drive")
