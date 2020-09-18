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
        interface = self.comCfg.interface
        if not interface == "USB":
            interface = "1GbE"
        # initialize controller and connect
        self.controller = tk.UHFLI(
            self.comCfg.name, self.comCfg.address[:7], interface=interface, host=HOST
        )
        self.controller.setup()
        self.controller.connect_device()
        self.setInstalledOptions(self.controller.options)
        self.setValue("DAQ - Status", f"Ready for Measurement")
        self.setValue("Sweeper Control - Status", f"Ready for Measurement")

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

        loop_index, n_HW_loop = self.getHardwareLoopIndex(options)

        # set DAQ module nodes
        if "DAQ" in quant.name:
            if quant.set_cmd:
                value = self.set_daq_value(quant, value)
            if "DAQ Trigger - Trigger" in quant.name:
                self.get_daq_trigger()
            if "DAQ Signal" in quant.name:
                self.get_daq_signals()
            if quant.name == "DAQ - Measure" and value:
                if not self.controller.daq.signals:
                    self.get_daq_signals()
                self.daq_measure()
        # set Sweeper module nodes
        elif "Sweeper" in quant.name:
            if quant.set_cmd:
                value = self.set_sweeper_value(quant, value)
            if quant.name == "Sweeper - Parameter":
                self.controller.sweeper.sweep_parameter(value)
            if quant.name == "Sweeper Advanced - Application":
                self.controller.sweeper.application(value)
            if "Sweeper Signal" in quant.name:
                self.get_sweeper_signals()
            if quant.name == "Sweeper Control - Measure" and value:
                if not self.controller.sweeper.signals:
                    self.get_sweeper_signals()
                self.sweeper_measure()
        # if a 'set_cmd' is defined, just set the node
        elif quant.set_cmd:
            value = self.set_node_value(quant, value)

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

        # sequencer start / stop
        if quant.name.endswith("Run"):
            value = self.awg_start_stop(quant, value)

        # mark sequencer as updated to be recompiled
        if quant.name.startswith("Sequencer"):
            self.sequencer_updated = True

        # sequencer waveform (for 'Simple' sequence)
        if quant.name.startswith("Waveform"):
            ch = int(quant.name[-1]) - 1
            self.waveforms_updated[ch] = True

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
        """Perform the Set Value instrument operation. This function should
        return the actual value set by the instrument"""
        # getting a demodulator sample value
        if "Demodulator" in quant.name and "Value" in quant.name:
            if self.getValue(quant.name.replace("Value", "Enable")):
                return self.controller._get(quant.get_cmd)
            else:
                return 0 + 1j * 0
        # getting a value from the DAQ module
        if "DAQ" in quant.name:
            if quant.get_cmd:
                return self.get_daq_value(quant)
            elif "Trace" in quant.name:
                i = int(quant.name[11]) - 1
                try:
                    signal = self.controller.daq.signals[i]
                    result = self.controller.daq.results[signal]
                    return self.daq_result_to_quant(quant, result)
                except:
                    return self.daq_return_zeros(quant)
        # getting a value from the Sweeper module
        elif "Sweeper" in quant.name:
            if quant.get_cmd:
                return self.get_sweeper_value(quant)
            elif "Trace" in quant.name:
                i = int(quant.name[15]) - 1
                try:
                    signal = self.controller.sweeper.signals[i]
                    result = self.controller.sweeper.results[signal]
                    return self.sweeper_result_to_quant(quant, result)
                except:
                    return self.sweeper_return_zeros(quant)
        # if not a DAQ or Sweeper node and a 'get_cmd' is defined
        elif quant.get_cmd:
            return self.controller._get(quant.get_cmd)
        else:
            return quant.getValue()

    def performArm(self, quant_names, options={}):
        """Perform the instrument arm operation"""
        pass

    def set_node_value(self, quant, value):
        """Handles setting of device nodes with 'set_cmd'."""
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
        """Handles setting of nodes with 'set_cmd'."""
        if value:
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

    def get_sequence_params(self):
        """Retrieves all sequence parameters from Labber quantities and returns 
        them as a dictionary, ready for `set_sequence_params(...)`."""
        base_name = f"Sequencer - "
        params = dict(
            sequence_type=self.getValue(base_name + "Sequence"), clock_rate=1.8e9,
        )
        if params["sequence_type"] == "Pulse Train":
            params.update(repetitions=int(self.getValue(base_name + "Repetitions")))
        if params["sequence_type"] == "Custom":
            params.update(path=self.getValue(base_name + "Custom Path"))
        return params

    def queue_waveforms(self, options={}):
        """Queue waveforms or replace waveforms on AWGs."""
        loop_index, _ = self.getHardwareLoopIndex(options)
        if loop_index == 0:
            self.controller.awg.reset_queue()
        if any(self.waveforms_updated):
            w1 = self.getValueArray("Waveform 1")
            w2 = self.getValueArray("Waveform 1")
            self.controller.awg.queue_waveform(w1, w2)

    def compile_sequencers(self):
        """Handles the compilation and waveform upload of the AWGs."""
        sequence_type = self.getValue("Sequencer - Sequence")
        if sequence_type != "None":
            self.controller.awg.compile()
        if sequence_type == "Pulse Train":
            self.controller.awg.upload_waveforms()

    def set_daq_value(self, quant, value):
        """Handles setting of DAQ module nodes with 'set_cmd'."""
        name = quant.set_cmd
        param = self.controller.daq.__dict__[name]
        param(value)
        return param()

    def get_daq_value(self, quant):
        """Handles getting of DAQ module nodes with 'set_cmd'."""
        name = quant.set_cmd
        param = self.controller.daq.__dict__[name]
        return param()

    def set_sweeper_value(self, quant, value):
        """Handles getting of Sweeper module nodes with 'set_cmd'."""
        name = quant.set_cmd
        param = self.controller.sweeper.__dict__[name]
        param(value)
        return param()

    def get_sweeper_value(self, quant):
        name = quant.set_cmd
        param = self.controller.sweeper.__dict__[name]
        return param()

    def daq_result_to_quant(self, quant, result):
        """Gets the corresponding result data from the DAQ module."""
        if "FFT" in quant.name and result.frequency is None:
            return self._daq_return_zeros(quant)
        elif "FFT" not in quant.name and result.time is None:
            return self._daq_return_zeros(quant)
        else:
            x = result.time if result.time is not None else result.frequency
            y = result.value[0]
            return quant.getTraceDict(y, x=x)

    def daq_return_zeros(self, quant):
        """Generate a result trace dictionary with zeros for invalid result."""
        l = self.controller.daq._get("/grid/cols")
        return quant.getTraceDict(np.zeros(l), x=np.linspace(0, 1, l))

    def sweeper_result_to_quant(self, quant, result):
        """Gets the corresponding result data from the Sweeper module."""
        base = quant.name[:19]
        signal_source = self.getValue(base + "Source")
        if "demod" in signal_source:
            signal_type = self.getValue(base + "Type")
            operation = self.getValue(base + "Operation").replace("none", "")
            param = signal_type + operation
            x = result.grid
            try:
                y = result.__dict__[param]
            except KeyError:
                return self._sweeper_return_zeros(quant)
            return quant.getTraceDict(y, x=x)
        else:
            x = result.grid
            try:
                y = result.value
            except KeyError:
                return self._sweeper_return_zeros(quant)
            return quant.getTraceDict(y, x=x)

    def sweeper_return_zeros(self, quant):
        """Generate a result trace dictionary with zeros for invalid result."""
        l = self.controller.sweeper._get("/samplecount")
        return quant.getTraceDict(np.zeros(l), x=np.linspace(0, 1, l))

    def get_daq_signals(self):
        """Add selected signals to measurement on DAQ module."""
        n_signals = int(self.getValue("DAQ Signals - Number of Signals"))
        self.controller.daq.signals_clear()
        for i in range(n_signals):
            base = f"DAQ Signal {i+1} - "
            signal_source = self.getValue(base + "Source")
            if "demod" in signal_source:
                signal_type = self.getValue(base + "Type Demod")
            if "imp" in signal_source:
                signal_type = self.getValue(base + "Type Imp")
            operation = self.getValue(base + "Operation")
            fft = self.getValue(base + "FFT")
            selector = self.getValue(base + "Complex Selector")
            s = self.controller.daq.signals_add(
                signal_source,
                signal_type,
                operation=operation,
                fft=fft,
                complex_selector=selector,
            )

    def get_sweeper_signals(self):
        """Add selected signals to measurement on Sweeper module."""
        n_signals = int(self.getValue("Sweeper Signals - Number of Signals"))
        self.controller.sweeper.signals_clear()
        for i in range(n_signals):
            base = f"Sweeper Signal {i+1} - "
            signal_source = self.getValue(base + "Source")
            s = self.controller.sweeper.signals_add(signal_source)

    def get_daq_trigger(self):
        """Set selected trigger signal on DAQ module."""
        base = "DAQ Trigger - Trigger "
        trigger_source = self.getValue(base + "Source")
        if "demod" in trigger_source:
            trigger_type = self.getValue(base + "Type Demod")
        elif "aux" in trigger_source:
            trigger_type = self.getValue(base + "Type Aux")
        elif "imp" in trigger_source:
            trigger_type = self.getValue(base + "Type Imp")
        self.controller.daq.trigger(trigger_source, trigger_type)

    def daq_measure(self):
        """Start the measurement on the DAQ."""
        timeout = self.getValue("DAQ - Timeout")
        try:
            self.setValue("DAQ - Status", f"Busy ...")
            self.controller.daq.measure(timeout=timeout)
            self.setValue("DAQ - Status", f"Ready for Measurement")
        except TimeoutError:
            self.controller.daq._results = {}

    def sweeper_measure(self):
        """Start the measurement on the Sweeper."""
        timeout = self.getValue("Sweeper Control - Timeout")
        try:
            node = self.controller.sweeper._get("gridnode")
            self.setValue(
                "Sweeper Control - Status", f"Sweeping Parameter '{node}'",
            )
            self.controller.sweeper.measure(timeout=timeout)
            self.setValue("Sweeper Control - Status", "Ready for Measurement")
        except TimeoutError:
            self.controller.sweeper._results = {}
