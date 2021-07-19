# Copyright (C) 2021 Zurich Instruments
#
# This software may be modified and distributed under the terms
# of the MIT license. See the LICENSE file for details.
"""Labber Driver for the Zurich Instruments SHFQA Quantum Analyzer.

This driver provides a high-level interface of the Zurich Instruments
SHFQA Quantum Analyzer for the scientific measurement software Labber.
It is based on the Zurich Instruments Toolkit (zhinst-toolkit), an
extension of our Python API ziPython for high-level instrument control.
"""

import re
import csv
import numpy as np
import time
from BaseDriver import LabberDriver, Error

import zhinst.toolkit as tk

# change this value in case you are not using 'localhost'
HOST = "localhost"
# change this value in case you need longer timeout
# for generator, readout and scope
TIMEOUT = 10


class Driver(LabberDriver):
    """Implement a Labber Driver for the Zurich Instruments SHFQA."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controller = None
        self.num_qachannels = 0
        self.sequencers_updated = []
        self.waveforms_updated = []
        self.replace_waveform = []
        self.sweepers_updated = []
        self.generators_armed = []
        self.readouts_armed = []
        self.sweepers_armed = []
        self.scope_armed = False

    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection."""
        # Get the interface selected in UI,
        # restrict to either 'USB' or '1GbE'
        interface = self.comCfg.interface
        if not interface == "USB":
            interface = "1GbE"
        # Initialize controller and connect
        self.controller = tk.SHFQA(
            self.comCfg.name, self.comCfg.address[:8], interface=interface, host=HOST
        )
        self.controller.setup()
        self.controller.connect_device()
        # Read the model string from the device
        # and update Labber controller.
        self.update_model()
        # Read the revision numbers after the connection
        # and update Labber controller.
        self.update_labber_controller("Revisions - Data Server")
        self.update_labber_controller("Revisions - Firmware")
        self.update_labber_controller("Revisions - FPGA")
        # Get number of qachannels
        self.num_qachannels = self.controller.num_qachannels()
        # Initialize armed flags as False
        self.generators_armed = [False] * self.num_qachannels
        self.readouts_armed = [False] * self.num_qachannels
        self.sweepers_armed = [False] * self.num_qachannels
        self.scope_armed = False

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
        current_loop_index, total_n_pts = self.getHardwareLoopIndex(options)
        # Reset all updated flags to `False`
        if self.isFirstCall(options):
            self.sequencers_updated = [False] * self.num_qachannels
            self.waveforms_updated = [False] * self.num_qachannels
            self.replace_waveform = [False] * self.num_qachannels
            self.sweepers_updated = [False] * self.num_qachannels

        # Device tab
        if quant.name == "Preset - Factory Reset":
            # Load factory preset
            self.controller.factory_reset(sync=True)
        if quant.name == "Input Reference Clock - Set Source":
            # Check if reference clock is locked
            self.controller.check_ref_clock(blocking=True, timeout=30, sleep_time=1)
            # Update actual source and status values
            self.update_labber_controller("Input Reference Clock - Actual Source")
            self.update_labber_controller("Input Reference Clock - Status")
        if quant.name == "Extras - Enable Internal Trigger Loopback":
            if value:
                self.controller.set_trigger_loopback()
            else:
                self.controller.clear_trigger_loopback()

        # In/Out tab
        if "Center Frequency" in quant.name:
            # Update Output Frequency if the Center Frequency is changed
            index = self.name_to_index(quant.name)
            base_name = f"QA Channel {index + 1} - "
            self.update_labber_controller(base_name + "Output Frequency")

        # QA Setup tab
        # Spectroscopy mode
        if "Offset Frequency" in quant.name:
            # Update Output Frequency if the Offset Frequency is changed
            index = self.name_to_index(quant.name)
            base_name = f"QA Channel {index + 1} - "
            self.update_labber_controller(base_name + "Output Frequency")
        # Readout mode
        if "Integration Weights File Path" in quant.name:
            # Upload integration weights
            self.upload_integration_weights(quant)

        # Generator tab
        if "Sequencer" in quant.name:
            # Start / Stop generator
            if "Run/Stop" in quant.name:
                self.generator_start_stop(quant, value)
            sequencer_settings = ["Sequence Type", "Program", "Parameters", "Trigger"]
            if any(k in quant.name for k in sequencer_settings):
                index = self.name_to_index(quant.name)
                # Mark sequencer as updated to be recompiled
                self.sequencers_updated[index] = True
            # Sequencer waveform (for 'Custom' sequence)
            if "Waveform" in quant.name:
                index = self.name_to_index(quant.name)
                base_name = f"Sequencer {index + 1} - "
                data_source = self.getValue(base_name + "Waveform Source")
                # Mark the respective waveform as updated
                self.waveforms_updated[index] = True
                # Mark as 'replace waveform' if not HW looping
                # and data source is vector
                if data_source == "Vector Data" and not self.isHardwareLoop(options):
                    self.replace_waveform[index] = True

        # Sweeper tab
        if "Sweeper" in quant.name:
            # Start sweeper
            if "Run" in quant.name:
                self.sweeper_start(quant)
            sweeper_settings = ["Frequency", "Points", "Mapping", "Averages", "Mode"]
            if any(k in quant.name for k in sweeper_settings):
                index = self.name_to_index(quant.name)
                # Mark sweeper as updated
                self.sweepers_updated[index] = True

        if self.isFinalCall(options):
            if any(self.waveforms_updated) or any(self.sequencers_updated):
                if current_loop_index + 1 == total_n_pts:
                    # Update the sequencers
                    self.update_sequencers()
                    if any(self.waveforms_updated):
                        # Queue the waveforms marked as updated
                        # to the respective Generator
                        self.queue_waveforms(options=options)
                    # Recompile the sequencers
                    self.compile_sequencers()
            if any(self.sweepers_updated):
                if current_loop_index + 1 == total_n_pts:
                    # Update the sweepers
                    self.update_sweepers()

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
        current_loop_index, total_n_pts = self.getHardwareLoopIndex(options)

        # Device tab
        if quant.name == "Input Reference Clock - Set Source":
            # Update actual source and status values
            self.update_labber_controller("Input Reference Clock - Actual Source")
            self.update_labber_controller("Input Reference Clock - Status")

        # QA Result tab
        if "Readout" in quant.name:
            readout_index = self.name_to_index(quant.name)
            readout = self.controller.qachannels[readout_index].readout
            if any(k in quant.name for k in ["Result Vector", "Result Average"]):
                integration_index = int(quant.name[-1]) - 1
                if self.readouts_armed[readout_index]:
                    # If the channel is armed, wait until readout is
                    # finished, before reading the data
                    data = readout.read(
                        [integration_index], blocking=True, timeout=TIMEOUT
                    )
                    # Reset armed flags back to False, channel must be
                    # armed again for the next readout
                    self.readouts_armed[readout_index] = False
                    self.generators_armed[readout_index] = False
                else:
                    data = readout.read([integration_index], blocking=False)
                if "Vector" in quant.name:
                    value = quant.getTraceDict(data[0], x0=0, dx=1)
                if "Average" in quant.name:
                    if self.isHardwareLoop(options):
                        value = data[0][current_loop_index]
                    else:
                        value = np.mean(data[0])

        # Sweeper tab
        if "Sweeper" in quant.name:
            index = self.name_to_index(quant.name)
            sweeper = self.controller.qachannels[index].sweeper
            if "Result Vector" in quant.name:
                if self.sweepers_armed[index]:
                    # If the channel is armed, reset armed flag back to
                    # False, channel must be armed again for the next
                    # spectroscopy reading
                    self.sweepers_armed[index] = False
                data = sweeper.read()
                start_frequency = data["properties"]["startfreq"]
                stop_frequency = data["properties"]["stopfreq"]
                logx = data["properties"]["mapping"] == "log"
                value = quant.getTraceDict(
                    data["vector"], x0=start_frequency, x1=stop_frequency, logX=logx
                )

        # Scope tab
        if "Scope" in quant.name:
            if "Result Vector" in quant.name:
                index = self.name_to_index(quant.name)
                if self.scope_armed:
                    # If the channel is armed, wait until scope
                    # recording is finished, before reading the data
                    data = self.controller.scope.read(
                        index, blocking=True, timeout=TIMEOUT
                    )
                    # Reset armed flags back to False, channel must be
                    # armed again for the next scope reading
                    self.scope_armed = False
                    self.generators_armed = [False] * self.num_qachannels
                else:
                    data = self.controller.scope.read(index, blocking=False)
                value = quant.getTraceDict(data["data"], x=data["time"])

        return value

    def performArm(self, quant_names, options={}):
        """Perform the instrument arm operation"""
        if not self.scope_armed and self.getValue(f"Recording - Enable Scope"):
            # Start the scope if it is enabled and not armed yet
            self.controller.scope.stop()
            self.controller.scope.run()
            # Set the armed flag to True
            self.scope_armed = True
        for index in range(self.num_qachannels):
            application_mode = self.getValue(
                f"QA Channel {index + 1} - Application Mode"
            )
            sweeper_enabled = self.getValue(f"Sweeper {index + 1} - Enable Sweeper")
            readout_enabled = self.getValue(f"Readout {index + 1} - Enable Readout")
            sequence_type = self.getValue(f"Sequencer {index + 1} - Sequence Type")
            trigger_mode = self.getValue(f"Sequencer {index + 1} - Trigger Mode")
            if (
                not self.sweepers_armed[index]
                and application_mode == "spectroscopy"
                and sweeper_enabled
            ):
                # Start the sweeper if it is enabled and not armed yet
                self.controller.qachannels[index].sweeper.run()
                # Set the armed flag to True
                self.sweepers_armed[index] = True
            if (
                not self.readouts_armed[index]
                and application_mode == "readout"
                and readout_enabled
            ):
                # Arm the readout if it is enabled and not armed yet
                self.controller.qachannels[index].readout.arm()
                # Set the armed flag to True
                self.readouts_armed[index] = True

            if (
                not self.generators_armed[index]
                and application_mode == "readout"
                and trigger_mode in ["Receive Trigger", "ZSync Trigger"]
                and sequence_type != "None"
            ):
                # Start the generator if the trigger mode is
                # "Receive Trigger" or "ZSync Trigger" and it is not
                # armed yet
                self.controller.qachannels[index].generator.stop()
                self.controller.qachannels[index].generator.run()
                # Set the armed flag to True
                self.generators_armed[index] = True

    def update_labber_controller(self, quant_name):
        """Read the quantity from device and update the Labber controller."""
        value = self.readValueFromOther(quant_name)
        self.setValue(quant_name, value)

    def update_model(self):
        """Read the model from device and update the Labber controller."""
        model = self.controller.nodetree.features.devtype()
        self.setModel(model)

    def set_node_value(self, quant, value):
        """Perform node and parameter set

        This method uses the zhinst-toolkit setter to set the node
        and parameter values.
        """
        if quant.datatype == quant.BOOLEAN:
            # If the quantity type is boolean convert it to 1/0
            mapping = {True: 1, False: 0}
            value = mapping[value]
        elif quant.datatype == quant.COMBO:
            # If the quantity type is combo, check if a list of command
            # strings is defined
            if quant.cmd_def:
                # Extract the command string from value
                value = quant.getCmdStringFromValue(value)
            # If the value corresponds to a number, convert it to a
            # numerical type (int or float), otherwise do not change it
            value = self.str_to_num(value)
        # Send the value to the device
        self.nested_getattr(self.controller, quant.set_cmd)(value)
        return value

    def get_node_value(self, quant):
        """Perform node and parameter get

        This method uses the zhinst-toolkit getter to get the node
        and parameter values.
        """
        # Read the value from device
        value = self.nested_getattr(self.controller, quant.get_cmd)()
        if quant.datatype == quant.BOOLEAN:
            # If the quantity type is boolean and device returns
            # on/off, convert it to True/False
            if value in ["on", "off"]:
                mapping = {"on": True, "off": False}
                value = mapping[value]
        elif quant.datatype == quant.COMBO:
            # If a numerical value is returned as float or integer,
            # `num_to_str` function converts it to string,
            # otherwise, does not change it.
            value = self.num_to_str(value)
            # Check if `cmd_def` list contains the string value
            if value in quant.cmd_def:
                value = quant.getValueFromCmdString(value)
        return value

    def upload_integration_weights(self, quant):
        """Handles the upload of integration weights in readout mode."""
        index = self.name_to_index(quant.name)
        base_name = f"QA Channel {index + 1} - "
        data_path = self.getValue(quant.name)
        if data_path != "":
            weights_list = self.csv_path_to_complex_vector(data_path)
            for i in range(len(weights_list)):
                integration = self.controller.qachannels[index].readout.integrations[i]
                integration.set_int_weights(weights_list[i])
            self.update_labber_controller(base_name + "Readout Integration Length")

    def generator_start_stop(self, quant, value):
        """Start or stop the respective Generator."""
        index = self.name_to_index(quant.name)
        base_name = f"QA Channel {index + 1} - "
        if self.getValue(base_name + "Application Mode") == "readout":
            if not self.controller.qachannels[index].generator.is_running and value:
                self.controller.qachannels[index].generator.run()
            else:
                self.controller.qachannels[index].generator.stop()
            return self.controller.qachannels[index].generator.is_running
        else:
            print("Please switch to readout mode to use the generator.")

    def get_sequence_params(self, index):
        """Retrieve all sequence parameters

        Gets all sequence parameters from Labber quantities and
        returns them as a dictionary, ready for
        `set_sequence_params(...)`.

        """
        base_name = f"Sequencer {index + 1} - "
        params = dict(
            sequence_type=self.getValue(base_name + "Sequence Type"),
            trigger_mode=self.getValue(base_name + "Trigger Mode"),
        )
        if params["sequence_type"] == "Custom":
            custom_params = self.getValue(base_name + "Custom Parameters").split(", ")
            path = self.getValue(base_name + "Program Path")
            params.update(path=path, custom_params=custom_params)
        return params

    def update_sequencers(self):
        """Handles the 'set_sequence_params(...)' for the Sequencers."""
        for index, updated in enumerate(self.sequencers_updated):
            generator = self.controller.qachannels[index].generator
            if updated:
                params = self.get_sequence_params(index)
                sequence_type = params["sequence_type"]
                if sequence_type != "None":
                    generator.set_sequence_params(**params)

    def queue_waveforms(self, options={}):
        """Queue waveforms or replace waveforms on the Generators."""
        current_loop_index, total_n_pts = self.getHardwareLoopIndex(options)
        for index in range(self.num_qachannels):
            generator = self.controller.qachannels[index].generator
            base_name = f"Sequencer {index + 1} - "
            if current_loop_index == 0 and not self.replace_waveform[index]:
                generator.reset_queue()
            if self.waveforms_updated[index]:
                data_source = self.getValue(base_name + "Waveform Source")
                if data_source == "File Path":
                    wave_path = self.getValue(base_name + "Waveform Path")
                    if wave_path != "":
                        vector_list = self.csv_path_to_complex_vector(wave_path)
                        for wave in vector_list:
                            generator.queue_waveform(wave)
                elif data_source == "Vector Data":
                    wave_vector = self.getValueArray(base_name + "Waveform Vector")
                    queue_length = len(generator.waveforms)
                    if self.replace_waveform[index] and queue_length != 0:
                        generator.replace_waveform(wave_vector, i=current_loop_index)
                    else:
                        generator.queue_waveform(wave_vector)

    def compile_sequencers(self):
        """Handles the compilation and waveform upload of the Generators."""
        for index in range(self.num_qachannels):
            generator = self.controller.qachannels[index].generator
            queue_length = len(generator.waveforms)
            if self.sequencers_updated[index] or self.waveforms_updated[index]:
                sequence_type = self.getValue(f"Sequencer {index + 1} - Sequence Type")
                if sequence_type != "None" and not self.replace_waveform[index]:
                    generator.compile()
                if sequence_type == "Custom" and queue_length != 0:
                    generator.upload_waveforms()

    def sweeper_start(self, quant):
        """Start the respective Sweeper."""
        index = self.name_to_index(quant.name)
        base_name = f"Sweeper {index + 1} - "
        if self.getValue(base_name + "Enable Sweeper"):
            # Mark sweeper as updated and start it if it is enabled
            self.sweepers_updated[index] = True
            self.update_sweepers()
            self.controller.qachannels[index].sweeper.run()
        else:
            print(
                "Please switch to spectroscopy mode and enable the sweeper to use "
                "it."
            )

    def get_sweeper_params(self, index):
        """Retrieve all sweeper parameters

        Gets all sequence parameters from Labber quantities and
        returns them as a dictionary, ready for
        `update_sweepers(...)`.

        """
        base_name = f"Sweeper {index + 1} - "
        params = dict(
            start_frequency=self.getValue(base_name + "Start Frequency"),
            stop_frequency=self.getValue(base_name + "Stop Frequency"),
            num_points=int(self.getValue(base_name + "Number of Points")),
            mapping=self.getValue(base_name + "Mapping"),
            num_averages=int(self.getValue(base_name + "Number of Averages")),
            averaging_mode=self.getValue(base_name + "Averaging Mode"),
        )
        return params

    def update_sweepers(self):
        """Update the parameters of the Sweepers."""
        for index, updated in enumerate(self.sweepers_updated):
            sweeper = self.controller.qachannels[index].sweeper
            if updated:
                params = self.get_sweeper_params(index)
                for key, value in params.items():
                    self.nested_getattr(sweeper, key)(value)

    @staticmethod
    def name_to_index(name):
        """Extract sequencer index from name"""
        indices = [int(s) for s in name.split() if s.isdigit()]
        return indices[0] - 1

    @staticmethod
    def nested_getattr(main_obj, attr_str):
        """Implement `getattr` on nested objects and chained attributes"""
        attr_list = attr_str.split(".")
        result = main_obj
        pattern = r"\[(.*)\]"
        for element in attr_list:
            match = re.search(pattern, element)
            if match:
                attr = element[: match.start()] + element[match.end() :]
                index = int(element[match.start() + 1 : match.end() - 1])
                result = getattr(result, attr)
                result = result[index]
            else:
                attr = element
                result = getattr(result, attr)
        return result

    @staticmethod
    def str_to_num(s):
        """Convert a string to numerical value

        Returns integer or float value depending on the string input.
        If the conversion is not possible, the input is returned without
        any change.
        """
        try:
            a = float(s)
            b = int(a)
            if a == b:
                return b
            else:
                return a
        except (TypeError, ValueError):
            return s

    @staticmethod
    def num_to_str(n):
        """Convert an integer or float numerical value to string

        If the input number is an integer written in float format, it is
        returned as integer string. If the input does not correspond to
        a numerical value, it is returned without any change.
        """
        try:
            a = int(n)
            if a == n:
                return str(a)
            else:
                return str(n)
        except (TypeError, ValueError):
            return n

    @staticmethod
    def csv_path_to_complex_vector(path):
        """Import complex valued vectors from a .csv file path"""
        vectors = []
        with open(path, newline="") as csvfile:
            datareader = csv.reader(csvfile, delimiter=",", quotechar="|")
            for row in datareader:
                vectors.append(np.array(row, dtype=complex))
        return vectors
