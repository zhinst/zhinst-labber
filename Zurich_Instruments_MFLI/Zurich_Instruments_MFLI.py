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
            interface = "PCIE"
        # initialize controller and connect
        self.controller = tk.MFLI(
            self.comCfg.name, self.comCfg.address[:7], interface=interface, host=HOST
        )
        self.controller.setup()
        self.controller.connect_device()
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

        # set DAQ module nodes
        if "DAQ" in quant.name:
            if quant.set_cmd:
                value = self._set_daq_value(quant, value)
            if "DAQ Trigger - Trigger" in quant.name:
                self._get_daq_trigger()
            if "DAQ Signal" in quant.name:
                self._get_daq_signals()
            if quant.name == "DAQ - Measure" and value:
                if not self.controller.daq.signals:
                    self._get_daq_signals()
                self._daq_measure()
        # set Sweeper module nodes
        elif "Sweeper" in quant.name:
            if quant.set_cmd:
                value = self._set_sweeper_value(quant, value)
            if quant.name == "Sweeper - Parameter":
                self.controller.sweeper.sweep_parameter(value)
            if quant.name == "Sweeper Advanced - Application":
                self.controller.sweeper.application(value)
            if "Sweeper Signal" in quant.name:
                self._get_sweeper_signals()
            if quant.name == "Sweeper Control - Measure" and value:
                if not self.controller.sweeper.signals:
                    self._get_sweeper_signals()
                self._sweeper_measure()
        elif quant.set_cmd:
            value = self._set_node_value(quant, value)
        return value

    def performGetValue(self, quant, options={}):
        """Perform the Set Value instrument operation. This function should
        return the actual value set by the instrument"""
        if "DAQ" in quant.name:
            if quant.get_cmd:
                return self.get_daq_value(quant)
            elif "Trace" in quant.name:
                i = int(quant.name[11]) - 1
                try:
                    signal = self.controller.daq.signals[i]
                    result = self.controller.daq.results[signal]
                    return self._daq_result_to_quant(quant, result)
                except:
                    return self._daq_return_zeros(quant)
        elif "Sweeper" in quant.name:
            if quant.get_cmd:
                return self._get_sweeper_value(quant)
            elif "Trace" in quant.name:
                i = int(quant.name[15]) - 1
                try:
                    signal = self.controller.sweeper.signals[i]
                    result = self.controller.sweeper.results[signal]
                    return self._sweeper_result_to_quant(quant, result)
                except:
                    return self._sweeper_return_zeros(quant)
        elif quant.get_cmd:
            return self.controller._get(quant.get_cmd)
        else:
            return quant.getValue()

    def _set_node_value(self, quant, value):
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

    def _set_daq_value(self, quant, value):
        """Handles setting of DAQ module nodes with 'set_cmd'."""
        name = quant.set_cmd
        param = self.controller.daq.__dict__[name]
        param(value)
        return param()

    def _get_daq_value(self, quant):
        """Handles getting of DAQ module nodes with 'set_cmd'."""
        name = quant.set_cmd
        param = self.controller.daq.__dict__[name]
        return param()

    def _set_sweeper_value(self, quant, value):
        """Handles setting of Sweeper module nodes with 'set_cmd'."""
        name = quant.set_cmd
        param = self.controller.sweeper.__dict__[name]
        param(value)
        return param()

    def _get_sweeper_value(self, quant):
        """Handles getting of Sweeper module nodes with 'set_cmd'."""
        name = quant.set_cmd
        param = self.controller.sweeper.__dict__[name]
        return param()

    def _daq_result_to_quant(self, quant, result):
        """Gets the corresponding result data from the DAQ module."""
        if "FFT" in quant.name and result.frequency is None:
            return self._daq_return_zeros(quant)
        elif "FFT" not in quant.name and result.time is None:
            return self._daq_return_zeros(quant)
        else:
            x = result.time if result.time is not None else result.frequency
            # select only first row, 2D arrays not supported in Labber!
            y = result.value[0]
            return quant.getTraceDict(y, x=x)

    def _daq_return_zeros(self, quant):
        """Generate a result trace dictionary with zeros for invalid result."""
        l = self.controller.daq._get("/grid/cols")
        return quant.getTraceDict(np.zeros(l), x=np.linspace(0, 1, l))

    def _sweeper_result_to_quant(self, quant, result):
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

    def _sweeper_return_zeros(self, quant):
        """Generate a result trace dictionary with zeros for invalid result."""
        l = self.controller.sweeper._get("/samplecount")
        return quant.getTraceDict(np.zeros(l), x=np.linspace(0, 1, l))

    def _get_daq_signals(self):
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

    def _get_sweeper_signals(self):
        """Add selected signals to measurement on Sweeper module."""
        n_signals = int(self.getValue("Sweeper Signals - Number of Signals"))
        self.controller.sweeper.signals_clear()
        for i in range(n_signals):
            base = f"Sweeper Signal {i+1} - "
            signal_source = self.getValue(base + "Source")
            s = self.controller.sweeper.signals_add(signal_source)

    def _get_daq_trigger(self):
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

    def _daq_measure(self):
        """Start the measurement on the DAQ."""
        timeout = self.getValue("DAQ - Timeout")
        try:
            self.setValue("DAQ - Status", f"Busy ...")
            self.controller.daq.measure(timeout=timeout)
            self.setValue("DAQ - Status", f"Ready for Measurement")
        except TimeoutError:
            self.controller.daq._results = {}

    def _sweeper_measure(self):
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
