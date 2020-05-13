import time
import numpy as np
from BaseDriver import LabberDriver, Error

import zhinst.toolkit as tk


CLK_RATE = 1.8e9
HOST = "localhost"


class Driver(LabberDriver):
    """ This class implements a Labber driver"""

    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection"""
        interface = self.comCfg.interface
        if not interface == "USB":
            interface = "1GbE"
        self.controller = tk.UHFQA(
            self.comCfg.name, self.comCfg.address[:7], interface=interface, host=HOST
        )
        self.controller.setup()
        self.controller.connect_device()
        self.last_length = [0] * 2

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
            self.sequencer_updated = False
            self.waveforms_updated = [False] * 2
            self.replace_waveform = False

        loop_index, n_HW_loop = self.getHardwareLoopIndex(options)

        if quant.set_cmd:
            value = self.set_node_value(quant, value)

        if quant.name == "Control - Output 1":
            self.controller.awg.output1(int(value))

        if quant.name == "Control - Output 2":
            self.controller.awg.output2(int(value))

        if quant.name == "Control - Gain 1":
            self.controller.awg.gain1(value)

        if quant.name == "Control - Gain 2":
            self.controller.awg.gain2(value)

        if quant.name == "Crosstalk - Reset":
            self.set_cosstalk_matrix(np.eye(10))

        if quant.name == "Integration - Time":
            self.controller.integration_time(value)
            value = self.controller.integration_time()

        if quant.name.endswith("Run"):
            value = self.awg_start_stop(quant, value)

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

        if quant.name.startswith("Sequencer") or quant.name in [
            "QA Results - Length",
            "QA Results - HW Averages",
        ]:
            self.sequencer_updated = True

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
                if loop_index + 1 == n_HW_loop:
                    self.update_sequencers()
            if any(self.waveforms_updated):
                self.queue_waveforms(options=options)
            if any(self.waveforms_updated) or self.sequencer_updated:
                if loop_index == 0:
                    self.compile_sequencers()

        return value

    def performGetValue(self, quant, options={}):
        """Perform the Set Value instrument operation. This function should
        return the actual value set by the instrument"""
        if quant.get_cmd:
            return self.controller._get(quant.get_cmd)
        elif quant.name.startswith("Result Vector - QB"):
            i = int(quant.name[-2:]) - 1
            value = self.controller.channels[i].result()
            return quant.getTraceDict(value, x0=0, dx=1)
        elif quant.name.startswith("Result Avg - QB"):
            i = int(quant.name[-2:]) - 1
            value = self.controller.channels[i].result()
            if self.isHardwareLoop(options):
                index, _ = self.getHardwareLoopIndex(options)
                return value[index]
            else:
                return np.mean(value)
        elif quant.name == "Result Demod 1-2":
            return self.get_demod_12()
        else:
            return quant.getValue()

    def performArm(self, quant_names, options={}):
        """Perform the instrument arm operation
        """
        if self.getValue("QA Results - Enable"):
            self.controller._set("/qas/0/result/enable", 0)
            # add reset(0), reset(1) here?
            self.controller._set("/qas/0/result/reset", 1)
            self.controller._set("/qas/0/result/enable", 1)
        if self.getValue("Sequencer - Trigger Mode") == "External Trigger":
            self.controller.awg.run()
            self.log(f"###       UHFQA: RUN SEQUENCER")

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
        if value:
            self.controller.awg.run()
            self.log(f"###       UHFQA: RUN SEQUENCER")
        else:
            self.controller.awg.stop()
        if self.controller._get("awgs/0/single"):
            self.controller.awg.wait_done()
        return self.controller.awg.is_running

    def update_sequencers(self):
        if self.sequencer_updated:
            params = self.get_sequence_params()
            if params["sequence_type"] != "None":
                self.controller.awg.set_sequence_params(**params)

    def get_sequence_params(self):
        base_name = f"Sequencer - "
        params = dict(
            sequence_type=self.getValue(base_name + "Sequence"),
            period=self.getValue(base_name + "Period"),
            trigger_mode=self.getValue(base_name + "Trigger Mode"),
            alignment=self.getValue(base_name + "Alignment"),
            trigger_delay=self.getValue(base_name + "Trigger Delay"),
            readout_length=self.getValue(base_name + "Readout Length"),
            clock_rate=1.8e9,
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
        loop_index, _ = self.getHardwareLoopIndex(options)
        if loop_index == 0 and not self.replace_waveform:
            self.controller.awg.reset_queue()
        if any(self.waveforms_updated):
            w1 = self.getValueArray("Waveform 1")
            w2 = self.getValueArray("Waveform 1")
            if self.replace_waveform:
                self.controller.awg.replace_waveform(w1, w2, i=loop_index)
                self.log(f"###       UHFQA: REPLACED WAVE {loop_index+1}")
            else:
                self.controller.awg.queue_waveform(w1, w2)

    def compile_sequencers(self):
        sequence_type = self.getValue("Sequencer - Sequence")
        if sequence_type != "None" and not self.replace_waveform:
            self.controller.awg.compile()
            self.log(f"###       UHFQA: COMPILED SEQUENCER")
        if sequence_type == "Simple":
            self.controller.awg.upload_waveforms()
            self.log(f"###       UHFQA: UPLOADED WAVES")

    def set_cosstalk_matrix(self, matrix):
        rows, cols = matrix.shape
        for r in range(rows):
            for c in range(cols):
                self.setValue(f"Crosstalk - {r+1} , {c+1}", matrix[r, c])
        self.controller.crosstalk_matrix(matrix)

    def get_demod_12(self):
        data1 = self.controller.channels[0].result
        data2 = self.controller.channels[1].result
        real = np.mean(np.real(data1))
        imag = np.mean(np.real(data2))
        return real + 1j * imag
