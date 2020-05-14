import time
import numpy as np
from BaseDriver import LabberDriver, Error

import zhinst.toolkit as tk


# change this value in case you are not using 'localhost'
HOST = "10.42.0.226"


class Driver(LabberDriver):
    """ This class implements a Labber driver"""

    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection"""
        # get the interface selected in UI, restrict to either 'USB' or '1GbE'
        interface = self.comCfg.interface
        if not interface == "USB":
            interface = "1GbE"
        # initialize controller and connect
        self.controller = tk.UHFLI(
            self.comCfg.name, self.comCfg.address[:7], interface=interface, host=HOST
        )
        self.controller.setup()
        self.controller.connect_device()
        # initialize 'Status' quantities
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

        # set the instrument value to use later (this is only in cache)
        quant.setValue(value)

        # set DAQ module nodes
        if "DAQ" in quant.name:
            if quant.set_cmd:
                value = self._set_daq_value(quant, value)
            if "DAQ Trigger - Trigger" in quant.name:
                # set the trigger signal
                self._get_daq_trigger()
            if "DAQ Signal" in quant.name:
                # set the DAQ signals
                self._get_daq_signals()
            if quant.name == "DAQ - Measure" and value:
                # start the measurement when button clicked (for 'value=True')
                if not self.controller.daq.signals:
                    # update signals if not defined
                    self._get_daq_signals()
                self._daq_measure()
        # set Sweeper module nodes
        elif "Sweeper" in quant.name:
            if quant.set_cmd:
                # if a 'set_cmd' is defined, use 'set' of module
                value = self._set_sweeper_value(quant, value)
            if quant.name == "Sweeper - Parameter":
                # change the sweep parameter
                self.controller.sweeper.sweep_parameter(value)
            if quant.name == "Sweeper Advanced - Application":
                # change the application preset
                self.controller.sweeper.application(value)
            if "Sweeper Signal" in quant.name:
                # set the Sweeper signals
                self._get_sweeper_signals()
            if quant.name == "Sweeper Control - Measure" and value:
                # start the measurement when button clicked (for 'value=True')
                if not self.controller.sweeper.signals:
                    # update signals if not defined
                    self._get_sweeper_signals()
                self._sweeper_measure()
        # if a 'set_cmd' is defined, just set the node
        elif quant.set_cmd:
            value = self._set_node_value(quant, value)
        # return the value that was set on the device ...
        return value

    def performGetValue(self, quant, options={}):
        """Perform the Set Value instrument operation. This function should
        return the actual value set by the instrument"""
        # getting a value from the DAQ module
        if "DAQ" in quant.name:
            # if a 'get_cmd' is defined, use module to return the node value
            if quant.get_cmd:
                return self.get_daq_value(quant)
            # if we read a signal trace
            elif "Trace" in quant.name:
                i = int(quant.name[11]) - 1
                try:
                    # get the corresponding result data
                    signal = self.controller.daq.signals[i]
                    result = self.controller.daq.results[signal]
                    return self._daq_result_to_quant(quant, result)
                except:
                    # if it's not there, return a zero array
                    return self._daq_return_zeros(quant)
        # getting a value from the Sweeper module
        elif "Sweeper" in quant.name:
            # if a 'get_cmd' is defined, use module to return the node value
            if quant.get_cmd:
                return self._get_sweeper_value(quant)
            # if we read a signal trace
            elif "Trace" in quant.name:
                i = int(quant.name[15]) - 1
                try:
                    # get the corresponding result data
                    signal = self.controller.sweeper.signals[i]
                    result = self.controller.sweeper.results[signal]
                    return self._sweeper_result_to_quant(quant, result)
                except:
                    # if it's not there, return a zero array
                    return self._sweeper_return_zeros(quant)
        # if not a DAQ or Sweeper node and a 'get_cmd' is defined
        elif quant.get_cmd:
            return self.controller._get(quant.get_cmd)
        else:
            # otherwise return the cached value
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
        """Handles getting of Sweeper module nodes with 'set_cmd'."""
        name = quant.set_cmd
        param = self.controller.sweeper.__dict__[name]
        param(value)
        return param()

    def _get_sweeper_value(self, quant):
        name = quant.set_cmd
        param = self.controller.sweeper.__dict__[name]
        return param()

    def _daq_result_to_quant(self, quant, result):
        """Gets the corresponding result data from the DAQ module."""
        # FFT quantity but result is not from FFT signal
        if "FFT" in quant.name and result.frequency is None:
            # return zeros
            return self._daq_return_zeros(quant)
        # time domain quantity but result is not from time domain signal
        elif "FFT" not in quant.name and result.time is None:
            # return zeros
            return self._daq_return_zeros(quant)
        # other cases, i.e. where signal and result match
        else:
            # get result data for FFT or time domain
            x = result.time if result.time is not None else result.frequency
            # select only first row, 2D arrays not supported in Labber!
            y = result.value[0]
            # return as Labber trace dictionary
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
            # for a demod result
            signal_type = self.getValue(base + "Type")
            operation = self.getValue(base + "Operation").replace("none", "")
            param = signal_type + operation
            x = result.grid
            try:
                # try if selected attribute exists ...
                y = result.__dict__[param]
            except KeyError:
                # ... otherwise return zeros
                return self._sweeper_return_zeros(quant)
            return quant.getTraceDict(y, x=x)
        else:
            # if not a demod result just return 'value' attribute
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
        # clear signals list
        self.controller.daq.signals_clear()
        # iterate through slected signals
        for i in range(n_signals):
            base = f"DAQ Signal {i+1} - "
            # get signal source, type, operation, fft, ...
            signal_source = self.getValue(base + "Source")
            if "demod" in signal_source:
                signal_type = self.getValue(base + "Type Demod")
            if "imp" in signal_source:
                signal_type = self.getValue(base + "Type Imp")
            operation = self.getValue(base + "Operation")
            fft = self.getValue(base + "FFT")
            selector = self.getValue(base + "Complex Selector")
            # add selected signal to measurement
            s = self.controller.daq.signals_add(
                signal_source,
                signal_type,
                operation=operation,
                fft=fft,
                complex_selector=selector,
            )
            self.log(f"####   DAQ:    added signal '{s}'")

    def _get_sweeper_signals(self):
        """Add selected signals to measurement on Sweeper module."""
        n_signals = int(self.getValue("Sweeper Signals - Number of Signals"))
        # clear signals list
        self.controller.sweeper.signals_clear()
        # iterate through slected signals
        for i in range(n_signals):
            base = f"Sweeper Signal {i+1} - "
            # get signal source, type, operation, fft, ...
            signal_source = self.getValue(base + "Source")
            # add selected signal to measurement
            s = self.controller.sweeper.signals_add(signal_source)
            self.log(f"####   Sweeper:    added signal '{s}'")

    def _get_daq_trigger(self):
        """Set selected trigger signal on DAQ module."""
        base = "DAQ Trigger - Trigger "
        # get trigger source and type
        trigger_source = self.getValue(base + "Source")
        if "demod" in trigger_source:
            trigger_type = self.getValue(base + "Type Demod")
        elif "aux" in trigger_source:
            trigger_type = self.getValue(base + "Type Aux")
        elif "imp" in trigger_source:
            trigger_type = self.getValue(base + "Type Imp")
        self.log(f"#####            gridnode: {trigger_source}, {trigger_type}")
        # and set trigger
        self.controller.daq.trigger(trigger_source, trigger_type)
        self.log(
            f"#####            gridnode: {self.controller.daq._get('triggernode')}"
        )

    def _daq_measure(self):
        """Start the measurement on the DAQ."""
        timeout = self.getValue("DAQ - Timeout")
        try:
            self.setValue("DAQ - Status", f"Busy ...")
            self.controller.daq.measure(timeout=timeout)
            self.setValue("DAQ - Status", f"Ready for Measurement")
        except TimeoutError:
            self.log(f"Measurement timed out!")
            # reset results ...
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
            self.log(f"Measurement timed out!")
            # reset results ...
            self.controller.sweeper._results = {}
