import time
import numpy as np
from BaseDriver import LabberDriver, Error

import zhinst.toolkit as tk


HOST = "10.42.0.226"


class Driver(LabberDriver):
    """ This class implements a Labber driver"""

    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection"""
        interface = self.comCfg.interface
        if not interface == "USB":
            interface = "1GbE"
        self.controller = tk.HDAWG(
            self.comCfg.name, self.comCfg.address[:7], interface=interface, host=HOST
        )
        self.controller.setup()
        self.controller.connect_device()
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
        quant.setValue(value)

        if self.isFirstCall(options):
            self.sequencers_updated = [False] * 4
            self.waveforms_updated = [False] * 8
            self.replace_waveform = [False] * 8

        loop_index, n_HW_loop = self.getHardwareLoopIndex(options)

        if quant.set_cmd:
            value = self.set_node_value(quant, value)

        if "Sequencer" in quant.name and "Output" in quant.name:
            i = map_name_to_awg(quant.name)
            if int(quant.name[-1]) % 2:
                self.controller.awgs[i].output1(int(value))
            else:
                self.controller.awgs[i].output2(int(value))

        if "Sequencer" in quant.name and "Gain" in quant.name:
            i = map_name_to_awg(quant.name)
            if int(quant.name[-1]) % 2:
                self.controller.awgs[i].gain1(value)
            else:
                self.controller.awgs[i].gain2(value)

        if quant.name.endswith("IQ Modulation"):
            i = map_name_to_awg(quant.name)
            if value:
                self.controller.awgs[i].enable_iq_modulation()
            else:
                self.controller.awgs[i].disable_iq_modulation()

        if quant.name.endswith("Modulation Frequency"):
            i = map_name_to_awg(quant.name)
            self.controller.awgs[i].modulation_freq(value)

        if quant.name.endswith("Modulation Phase"):
            i = map_name_to_awg(quant.name)
            self.controller.awgs[i].modulation_phase_shift(value)

        if quant.name.endswith("Run"):
            value = self.awg_start_stop(quant, value)

        if quant.name.startswith("Sequencer"):
            self.sequencers_updated[map_name_to_awg(quant.name)] = True

        if quant.name.startswith("Waveform"):
            ch = int(quant.name[-1]) - 1
            self.waveforms_updated[ch] = True
            if not self.isHardwareLoop(options):
                data = value["y"]
                self.replace_waveform[ch] = (
                    True if len(data) == self.last_length[ch] else False
                )
                self.last_length[ch] = len(data)

        if quant.name.endswith("Pulse Amplitude"):
            if loop_index == 0:
                self.rabi_values = []
            self.rabi_values.append(value)
            if loop_index + 1 != n_HW_loop:
                self.sequencers_updated[map_name_to_awg(quant.name)] = False

        if quant.name.endswith("Delay Time"):
            if loop_index == 0:
                self.t1_values = []
            self.t1_values.append(value)

        if self.isFinalCall(options):
            if any(self.sequencers_updated):
                if loop_index + 1 == n_HW_loop:
                    self.update_sequencers()
            if any(self.waveforms_updated):
                self.queue_waveforms(options=options)
            if any(self.waveforms_updated) or any(self.sequencers_updated):
                if loop_index + 1 == n_HW_loop:
                    self.compile_sequencers()

        return value

    def performGetValue(self, quant, options={}):
        """Perform the Set Value instrument operation. This function should
        return the actual value set by the instrument"""
        if quant.get_cmd:
            return self.controller._get(quant.get_cmd)
        # add get for values??
        else:
            return quant.getValue()

    def performArm(self, quant_names, options={}):
        """Perform the instrument arm operation
        """
        for i in range(4):
            base_name = f"Sequencer {2*i + 1}-{2*i + 2} - "
            trigger = self.getValue(base_name + "Trigger Mode")
            sequence = self.getValue(base_name + "Sequence")
            if trigger == "External Trigger" and sequence != "None":
                self.controller.awgs[i].run()
                self.log(f"###       START SEQUENCER {i+1}")

    def set_node_value(self, quant, value):
        if quant.datatype == quant.COMBO:
            i = quant.getValueIndex(value)
            if len(quant.cmd_def) == 0:
                self.controller._set(quant.set_cmd, i)
            else:
                self.controller._set(quant.set_cmd, quant.cmd_def[i])
        else:
            self.controller._set(quant.set_cmd, value)
        return self.controller._get(quant.get_cmd)

    def awg_start_stop(self, quant, value):
        i = map_name_to_awg(quant.name)
        if value:
            self.controller.awgs[i].run()
            self.log(f"###       STARTED SEQUENCER {i+1}")
        else:
            self.controller.awgs[i].stop()
        if self.controller._get(f"awgs/{i}/single"):
            self.controller.awgs[i].wait_done()
        return self.controller.awgs[i].is_running

    def update_sequencers(self):
        for i, updated in enumerate(self.sequencers_updated):
            if updated:
                params = self.get_sequence_params(i)
                if params["sequence_type"] != "None":
                    self.controller.awgs[i].set_sequence_params(**params)

    def get_sequence_params(self, seq):
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
        loop_index, _ = self.getHardwareLoopIndex(options)
        for seq in range(4):
            if loop_index == 0 and not any(
                self.replace_waveform[2 * seq : 2 * seq + 2]
            ):
                self.controller.awgs[seq].reset_queue()
            if any(self.waveforms_updated[2 * seq : 2 * seq + 2]):
                w1 = self.getValueArray(f"Waveform - {2*seq + 1}")
                w2 = self.getValueArray(f"Waveform - {2*seq + 2}")
                if all(self.replace_waveform[2 * seq : 2 * seq + 2]):
                    self.controller.awgs[seq].replace_waveform(w1, w2, i=loop_index)
                    self.log(f"###       REPLACED WAVE {loop_index} ON AWG {seq+1}")
                else:
                    self.controller.awgs[seq].queue_waveform(w1, w2)
                    self.log(f"###       QUEUED WAVE ON AWG {seq+1}")

    def compile_sequencers(self):
        for seq in range(4):
            if self.sequencers_updated[seq] or any(
                self.waveforms_updated[2 * seq : 2 * seq + 2]
            ):
                sequence_type = self.getValue(
                    f"Sequencer {2*seq + 1}-{2*seq + 2} - Sequence"
                )
                if sequence_type != "None" and not any(
                    self.replace_waveform[2 * seq : 2 * seq + 2]
                ):
                    self.controller.awgs[seq].compile()
                    self.log(f"###       COMPILED SEQUENCER {seq+1}")
                if sequence_type == "Simple":
                    self.controller.awgs[seq].upload_waveforms()
                    self.log(f"###       UPLOADED WAVES ON SEQUENCER {seq+1}")


#################################################################
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
