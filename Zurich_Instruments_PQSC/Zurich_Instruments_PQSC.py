# Copyright (C) 2020 Zurich Instruments
#
# This software may be modified and distributed under the terms
# of the MIT license. See the LICENSE file for details.
"""Labber Driver for the Zurich Instruments PQSC Programmable Quantum
System Controller.

This driver provides a high-level interface of the Zurich Instruments
PQSC Programmable Quantum System Controller for the scientific
measurement software Labber. It is based on the Zurich Instruments
Toolkit (zhinst-toolkit), an extension of our Python API ziPython for
high-level instrument control.
"""

import re
from BaseDriver import LabberDriver, Error

import zhinst.toolkit as tk

# change this value in case you are not using 'localhost'
HOST = "localhost"


class Driver(LabberDriver):
    """Implement a Labber Driver for the Zurich Instruments PQSC."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controller = None

    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection."""
        # Get the interface selected in UI,
        # restrict to either 'USB' or '1GbE'
        interface = self.comCfg.interface
        if not interface == "USB":
            interface = "1GbE"
        # initialize controller and connect
        self.controller = tk.PQSC(
            self.comCfg.name, self.comCfg.address[:8], interface=interface, host=HOST
        )
        self.controller.setup()
        self.controller.connect_device()
        # Read the revision numbers after the connection
        # and update Labber controller.
        self.update_labber_controller("Revisions - Data Server")
        self.update_labber_controller("Revisions - Firmware")
        self.update_labber_controller("Revisions - FPGA")

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

        # Ports tab
        if "Run/Stop" in quant.name:
            value = self.start_stop(quant, value)

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

        # Device tab
        if quant.name == "Input Reference Clock - Set Source":
            # Update actual source and status values
            self.update_labber_controller("Input Reference Clock - Actual Source")
            self.update_labber_controller("Input Reference Clock - Status")

        return value

    def performArm(self, quant_names, options={}):
        """Perform the instrument arm operation"""
        self.controller.arm()

    def update_labber_controller(self, quant_name):
        """Read the quantity from device and update the Labber controller."""
        value = self.readValueFromOther(quant_name)
        self.setValue(quant_name, value)

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

    def start_stop(self, quant, value):
        """Start or stop sending triggers to all connected instruments
        over ZSync ports.."""
        if not self.controller.is_running and value:
            self.controller.run()
        else:
            self.controller.stop()
        return self.controller.is_running

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
