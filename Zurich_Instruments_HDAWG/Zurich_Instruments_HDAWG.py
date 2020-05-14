import time
import numpy as np
from BaseDriver import LabberDriver, Error

import zhinst.toolkit as tk


# change this value in case you are not using 'localhost'
HOST = "localhost"


class Driver(LabberDriver):
    """ This class implements a Labber driver"""

    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection"""
        # get the interface selected in UI, restrict to either 'USB' or '1GbE'
        interface = self.comCfg.interface
        if not interface == "USB":
            interface = "1GbE"
        # initialize controller and connect
        self.controller = tk.HDAWG(
            self.comCfg.name, self.comCfg.address[:7], interface=interface, host=HOST
        )
        self.controller.setup()
        self.controller.connect_device()
        # initialize list for 'replace waveform'
        self.last_length = [0] * 8

    def performClose(self, bError=False, options={}):
        """Perform the close instrument connection operation"""
        pass

    def initSetConfig(self):
        """This function is run before setting values in Set Config"""
        pass

    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform the Set Value instrument operation. This function should
        return the actual value set by the instrument"""

        # set the instrument value to use later (this is only in cache)
        quant.setValue(value)

        # Initialize these lists at the start of 'Set Cfg' to keep track of
        # what is changed, only compile or uplaod at the end of 'Set Cfg'
        # see 'if self.isFinalCall(): ...' below
        if self.isFirstCall(options):
            self.sequencers_updated = [False] * 4
            self.waveforms_updated = [False] * 8
            self.replace_waveform = [False] * 8

        # see if we are hardware-looping
        loop_index, n_HW_loop = self.getHardwareLoopIndex(options)

        # if a 'set_cmd' is defined, just set the node
        if quant.set_cmd:
            value = self.set_node_value(quant, value)

        # go through all the quantity names that dont have 'set_cmd'
        #
        # do not use 'elif' or 'switch' here!
        # for some quantities multiple 'ifs' are true, e.g. to mark the
        # sequencer as updated

        # sequencer outputs
        if "Sequencer" in quant.name and "Output" in quant.name:
            i = map_name_to_awg(quant.name)
            if int(quant.name[-1]) % 2:
                self.controller.awgs[i].output1(int(value))
            else:
                self.controller.awgs[i].output2(int(value))

        # sequencer gains
        if "Sequencer" in quant.name and "Gain" in quant.name:
            i = map_name_to_awg(quant.name)
            if int(quant.name[-1]) % 2:
                self.controller.awgs[i].gain1(value)
            else:
                self.controller.awgs[i].gain2(value)

        # sequencer modulation enable/disable
        if quant.name.endswith("IQ Modulation"):
            i = map_name_to_awg(quant.name)
            if value:
                self.controller.awgs[i].enable_iq_modulation()
            else:
                self.controller.awgs[i].disable_iq_modulation()

        # sequencer modulation frequency
        if quant.name.endswith("Modulation Frequency"):
            i = map_name_to_awg(quant.name)
            self.controller.awgs[i].modulation_freq(value)

        # sequencer modulation phase
        if quant.name.endswith("Modulation Phase"):
            i = map_name_to_awg(quant.name)
            self.controller.awgs[i].modulation_phase_shift(value)

        # sequencer start / stop (also a 'BUTTON' can be 'value=False')
        if quant.name.endswith("Run"):
            value = self.awg_start_stop(quant, value)

        # mark sequencer as updated to be recompiled
        if quant.name.startswith("Sequencer"):
            self.sequencers_updated[map_name_to_awg(quant.name)] = True

        # sequencer waveform (for 'Simple' sequence)
        if quant.name.startswith("Waveform"):
            # which channel?
            ch = int(quant.name[-1]) - 1
            # mark the respective waveform as updated
            self.waveforms_updated[ch] = True
            # make as 'replace waveform' if not HW looping
            if not self.isHardwareLoop(options):
                data = value["y"]
                self.replace_waveform[ch] = (
                    True if len(data) == self.last_length[ch] else False
                )
                self.last_length[ch] = len(data)

        # sequence parameters Rabi: pulse amplitude (hardware-looping!)
        if quant.name.endswith("Pulse Amplitude"):
            if loop_index == 0:
                # init 'rabi_values' list before first set
                self.rabi_values = []
            # just append the newly set value to the list
            self.rabi_values.append(value)
            if loop_index + 1 != n_HW_loop:
                # only mark sequencer as updated at final 'set'
                # otherwise sequencer will be compiled at every set in HW loop
                self.sequencers_updated[map_name_to_awg(quant.name)] = False

        # sequence parameters T1/T2: delay time (hardware-looping!)
        if quant.name.endswith("Delay Time"):
            if loop_index == 0:
                # init 't1_values' list before first set
                self.t1_values = []
            # just append the newly set value to the list
            self.t1_values.append(value)
            # compare to 'Pulse Amplitude' above ... last 'if' statement missing
            # TODO: maybe this is a mistake? check!

        # at final call of 'Set Cfg' check if sequencer need to be
        # - updated, i.e. call `awg.set_sequence_params(...)` with new values
        # - queue new waveform
        # - compiled, i.e. call `awg.compile()`
        if self.isFinalCall(options):
            if any(self.sequencers_updated):
                # if any sequencers are marked as updated
                if loop_index + 1 == n_HW_loop:
                    self.update_sequencers()
            if any(self.waveforms_updated):
                # queue the waveforms marked as updated to the respective AWG
                self.queue_waveforms(options=options)
            if any(self.waveforms_updated) or any(self.sequencers_updated):
                # sequencer needs to be recompiled if
                # - a new waveform was queued
                # - OR a sequence parameter was changed
                if loop_index + 1 == n_HW_loop:
                    # - if we are not HW-looping (`loop_index=0`, `n_HW_loop=1`)
                    # - or after the last 'set' in the HW loop
                    self.compile_sequencers()
        # return the value that was set on the device ...
        return value

    def performGetValue(self, quant, options={}):
        """Perform the Set Value instrument operation. This function should
        return the actual value set by the instrument"""
        if quant.get_cmd:
            # if a 'get_cmd' is defined, use it to return the node value
            return self.controller._get(quant.get_cmd)
        else:
            # otherwise return the cached value
            return quant.getValue()

    def performArm(self, quant_names, options={}):
        """Perform the instrument arm operation"""
        # iterate through all AWGs
        for i in range(4):
            base_name = f"Sequencer {2*i + 1}-{2*i + 2} - "
            trigger = self.getValue(base_name + "Trigger Mode")
            sequence = self.getValue(base_name + "Sequence")
            # only start AWG if used as slave and if a sequence is selected
            if trigger == "External Trigger" and sequence != "None":
                self.controller.awgs[i].run()
                self.log(f"###       START SEQUENCER {i+1}")

    def set_node_value(self, quant, value):
        """Handles setting of nodes with 'set_cmd'."""
        if quant.datatype == quant.COMBO:
            # for 'COMBO' quantities, set the defined command value
            i = quant.getValueIndex(value)
            if len(quant.cmd_def) == 0:
                self.controller._set(quant.set_cmd, i)
            else:
                self.controller._set(quant.set_cmd, quant.cmd_def[i])
        else:
            # for all other datatypes, just set
            self.controller._set(quant.set_cmd, value)
        return self.controller._get(quant.get_cmd)

    def awg_start_stop(self, quant, value):
        """Starts or stops the respective AWG Core depending on the value."""
        # get the AWG index from the name
        i = map_name_to_awg(quant.name)
        if value:
            # start the AWG
            self.controller.awgs[i].run()
            self.log(f"###       STARTED SEQUENCER {i+1}")
        else:
            # stop the AWG
            self.controller.awgs[i].stop()
        if self.controller._get(f"awgs/{i}/single"):
            # wait until the AWG is finished
            self.controller.awgs[i].wait_done()
        return self.controller.awgs[i].is_running

    def update_sequencers(self):
        """Handles the 'set_sequence_params(...)' for the AWGs."""
        # iterate through the AWGs
        for i, updated in enumerate(self.sequencers_updated):
            if updated:
                # get all sequence parameters from Labber ...
                params = self.get_sequence_params(i)
                if params["sequence_type"] != "None":
                    # ... and set on the AWG if used
                    self.controller.awgs[i].set_sequence_params(**params)

    def get_sequence_params(self, seq):
        """Retrieves all sequence parameters from Labber quantities and returns 
        them as a dictionary, ready for `set_sequence_params(...)`."""
        base_name = f"Sequencer {2*seq + 1}-{2*seq + 2} - "
        params = dict(
            sequence_type=self.getValue(base_name + "Sequence"),
            repetitions=self.getValue(base_name + "Repetitions"),
            period=self.getValue(base_name + "Period"),
            trigger_mode=self.getValue(base_name + "Trigger Mode"),
            alignment=self.getValue(base_name + "Alignment"),
            trigger_delay=self.getValue(base_name + "Trigger Delay"),
            pulse_width=self.getValue(base_name + "Pulse Width"),
            pulse_amplitude=self.getValue(base_name + "Pulse Amplitude"),
        )
        if params["sequence_type"] == "Rabi":
            if not hasattr(self, "rabi_values"):
                self.rabi_values = [self.getValue(base_name + "Pulse Amplitude")]
            params.update(pulse_amplitudes=self.rabi_values)
        if params["sequence_type"] in ["T1", "T2*"]:
            if not hasattr(self, "t1_values"):
                self.t1_values = [self.getValue(base_name + "Delay Time")]
            params.update(delay_times=self.t1_values)
        if params["sequence_type"] == "Custom":
            params.update(
                path=self.getValue(f"Custom Sequence {2*seq + 1}-{2*seq + 2} - Path")
            )
        return params

    def queue_waveforms(self, options={}):
        """Queue waveforms or replace waveforms on AWGs."""
        # get the loop index
        loop_index, _ = self.getHardwareLoopIndex(options)
        # iterate through AWGs
        for seq in range(4):
            if loop_index == 0 and not any(
                self.replace_waveform[2 * seq : 2 * seq + 2]
            ):
                # reset queue at beginning
                self.controller.awgs[seq].reset_queue()
            if any(self.waveforms_updated[2 * seq : 2 * seq + 2]):
                # if one waveform of two channels is updated, get the arrays
                w1 = self.getValueArray(f"Waveform - {2*seq + 1}")
                w2 = self.getValueArray(f"Waveform - {2*seq + 2}")
                if all(self.replace_waveform[2 * seq : 2 * seq + 2]):
                    # replace the waveform data if both are marked as 'replace'
                    self.controller.awgs[seq].replace_waveform(w1, w2, i=loop_index)
                    self.log(f"###       REPLACED WAVE {loop_index} ON AWG {seq+1}")
                else:
                    # else queue the waveforms to the AWG
                    self.controller.awgs[seq].queue_waveform(w1, w2)
                    self.log(f"###       QUEUED WAVE ON AWG {seq+1}")

    def compile_sequencers(self):
        """Handles the compilation and waveform upload of the AWGs."""
        # iterate over AWGs
        for seq in range(4):
            # does the AWG need to be compiled? waveforms uplaoded?
            if self.sequencers_updated[seq] or any(
                self.waveforms_updated[2 * seq : 2 * seq + 2]
            ):
                sequence_type = self.getValue(
                    f"Sequencer {2*seq + 1}-{2*seq + 2} - Sequence"
                )
                # compile if AWG is used
                if sequence_type != "None" and not any(
                    self.replace_waveform[2 * seq : 2 * seq + 2]
                ):
                    self.controller.awgs[seq].compile()
                    self.log(f"###       COMPILED SEQUENCER {seq+1}")
                # if using a 'Simple' sequence, upload waveforms in the queue
                if sequence_type == "Simple":
                    self.controller.awgs[seq].upload_waveforms()
                    self.log(f"###       UPLOADED WAVES ON SEQUENCER {seq+1}")


"""
Helper function for mapping Sequencer name to awg index.

"""


def map_name_to_awg(s):
    if "1-2" in s:
        return 0
    elif "3-4" in s:
        return 1
    elif "5-6" in s:
        return 2
    elif "7-8" in s:
        return 3
    else:
        raise Exception("Mapping to AWG index not possible!")
