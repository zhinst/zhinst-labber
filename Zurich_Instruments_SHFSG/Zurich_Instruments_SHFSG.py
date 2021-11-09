# Copyright (C) 2020 Zurich Instruments
#
# This software may be modified and distributed under the terms
# of the MIT license. See the LICENSE file for details.
"""Labber Driver for the Zurich Instruments SHFSG Signal Generator.

This driver provides a high-level interface of the Zurich Instruments
SHFSG Signal Generator for the scientific measurement
software Labber. It is based on the Zurich Instruments Toolkit
(zhinst-toolkit), an extension of our Python API ziPython for
high-level instrument control.
"""
import re
import csv
import numpy as np
import json
from BaseDriver import LabberDriver


import zhinst.toolkit as tk

import time

# change this value in case you are not using 'localhost'
HOST = "localhost"


class Driver(LabberDriver):
    """Implement a Labber Driver for the Zurich Instruments SHFSG"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controller = None
        self.sequencers_updated = []
        self.waveforms_updated = []
        self.replace_waveform = []
        self.sequence_error = []

    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection."""
        # Get the interface selected in UI,
        # restrict to either 'USB' or '1GbE'
        interface = self.comCfg.interface
        if not interface == "USB":
            interface = "1GbE"
        # initialize controller and connect
        self.controller = tk.SHFSG(
            self.comCfg.name, self.comCfg.address[:8], interface=interface, host=HOST
        )
        self.controller.setup()
        self.controller.connect_device()

        num_channels = self.controller.num_sgchannels()
        if num_channels == 8:
            self.instrCfg.sModel = "SHFSG8"
        elif num_channels == 4:
            self.instrCfg.sModel = "SHFSG4"
        else:
            raise Exception(
                "The device reported an invalid amount of SG Channels.",
                "This is likely cause by a failed setup",
            )

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
            self.set_node_value(quant, value)
            if quant.datatype == quant.DOUBLE:
                value = self.get_value(quant)
        # Update the current local value of the quantity of the driver
        quant.setValue(value)

        if quant.name == "Preset - Factory Reset":
            try:
                self.controller.factory_reset(sync=True)
            except Exception as e:
                print(e)
        if "Reset Default" in quant.name:
            channel_id = self.map_name_to_channel(quant.name) + 1
            self.reset_sequencer_defaults(channel_id)

        # Reset all updated flags to `False`
        if self.isFirstCall(options):
            self.sequencers_updated = [False] * 8
            self.cts_updated = [False] * 8
            self.waveforms_updated = [False] * 8
            self.reset_sequence_error()

        if (
            any(ext in quant.name for ext in ["Sequencer Program", "Advance"])
            and not "Manual" in quant.name
        ):
            self.sequencers_updated[self.map_name_to_channel(quant.name)] = True
        if "Waveform" in quant.name and not "Manual" in quant.name:
            self.waveforms_updated[self.map_name_to_channel(quant.name)] = True
        if "Command Table" in quant.name and not "Manual" in quant.name:
            self.cts_updated[self.map_name_to_channel(quant.name)] = True

        # Custom Buttons (not called during a measurement)
        if quant.name.endswith("Run"):
            value = self.awg_start_stop(quant, value)
        if quant.name.endswith("Download"):
            seq = self.get_node_value(
                f"sgchannels/{self.map_name_to_channel(quant.name)}/awg/sequencer/program",
                "",
            )
            seq_path = self.getValue(
                quant.name.replace(
                    "Download", "Sequencer Code Manual - Sequencer Code Output"
                )
            )
            if seq_path and seq:
                with open(seq_path, "w") as f:
                    f.write(seq)
            ct = self.get_node_value(
                f"sgchannels/{self.map_name_to_channel(quant.name)}/awg/commandtable/data",
                "",
            )
            ct_path = self.getValue(
                quant.name.replace(
                    "Download", "Sequencer Code Manual - Command Table Output"
                )
            )
            if ct_path and ct:
                with open(ct_path, "w") as f:
                    f.write(ct)
        if "Waveform to View" in quant.name:
            self.update_waveform_vector(self.map_name_to_channel(quant.name), [1, 2])

        if self.isFinalCall(options):
            self.update_sequencers()
            self.queue_waveforms()
            self.update_ct()
            self.compile_sequences()

        return value

    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation."""
        if "Waveform Channel" in quant.name:
            wave = 1 if "Channel 2" in quant.name else 2
            self.update_waveform_vector(self.map_name_to_channel(quant.name), [wave])
        if quant.get_cmd:
            # if a 'get_cmd' is defined, use it to return the node value
            value = self.get_value(quant)
            if value is None:
                print(f"Get operation failed for {quant.name}")
                value = quant.getValue()
            else:
                # Update the current local value of the quantity of the driver
                quant.setValue(value)
        else:
            # for other quantities, just return current value of control
            value = quant.getValue()

        return value

    def performArm(self, quant_names, options={}):
        """Perform the instrument arm operation"""
        for i in range(8):
            base_name = f"Sequencer {i+1} - Sequencer Program - "
            trigger = self.getValue(base_name + "Trigger Mode")
            sequence = self.getValue(base_name + "Sequence")
            # only start AWG if used as slave and if a sequence is selected
            if trigger in ["Receive Trigger", "ZSync Trigger"] and sequence != "None":
                self.controller.sgchannels[i].awg.run()

    def update_labber_controller(self, quant_name):
        """Read the quantity from device and update the Labber controller."""
        value = self.readValueFromOther(quant_name)
        self.setValue(quant_name, str(value))

    def update_waveform_vector(self, channel, wave_channel):
        """Updates a waveform vector."""
        if self.controller.num_sgchannels() > channel:
            wave_index = int(
                self.getValue(
                    f"Sequencer {channel+1} - Sequencer Code Manual - Waveform to View"
                )
            )
            wave = self.get_node_value(
                f"sgchannels/{channel}/awg/waveform/waves/{wave_index}"
            )
            if wave is not None:
                f = lambda x: (x if x < 2 ** 15 else x - 2 ** 16) / 2 ** 15
                wave = [f(x) for x in wave]
                if 1 in wave_channel:
                    self.setValue(
                        f"Sequencer {channel+1} - Waveform Channel 1", wave[::2]
                    )
                if 2 in wave_channel:
                    self.setValue(
                        f"Sequencer {channel+1} - Waveform Channel 2", wave[1::2]
                    )

    def set_node_value(self, quant, value):
        """Perform node and parameter set."""
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
        func = self.nested_getattr(self.controller, quant.set_cmd)
        if func:
            func(value)
        else:
            self.controller._set(quant.get_cmd,value)

        return value

    def get_value(self, quant):
        """Performs a get either on an attribute or the node."""
        # Read the value from device
        funct = self.nested_getattr(self.controller, quant.get_cmd)
        value = ""
        if not funct:
            value = self.get_node_value(quant.get_cmd)
        else:
            value = funct()
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

    def get_node_value(self, node, default=None):
        """Performs a get on the node."""
        try:
            value = self.controller._get(node)
        except Exception as e:
            print(e)
            value = default
        return value

    def awg_start_stop(self, quant, value):
        """Starts or stops the respective AWG Core depending on the value."""
        i = self.map_name_to_channel(quant.name)
        if not self.controller.sgchannels[i].awg.is_running and value:
            self.controller.sgchannels[i].awg.run()
        else:
            self.controller.sgchannels[i].awg.stop()
        if self.controller.sgchannels[i].awg.single:
            self.controller.sgchannels[i].awg.wait_done()
        return self.controller.sgchannels[i].awg.is_running

    def update_sequencers(self):
        """updates the sequences of the AWGs if they have changed."""
        for i, updated in enumerate(self.sequencers_updated):
            if updated:
                prefix_string = f"Sequencer {i+1} - Sequencer Program - "
                try:
                    self.controller.sgchannels[i].awg.set_sequence_params(
                        sequence_type=self.getValue(prefix_string + "Sequence"),
                        pulse_width=self.getValue(prefix_string + "Pulse Width"),
                        pulse_amplitudes=np.linspace(
                            self.getValue(prefix_string + "Pulse Amplitude Start"),
                            self.getValue(prefix_string + "Pulse Amplitude Stop"),
                            self.getValue(prefix_string + "Pulse Amplitude Number"),
                        ),
                        pulse_amplitude=self.getValue(
                            prefix_string + "Pulse Amplitude"
                        ),
                        delay_times=np.linspace(
                            self.getValue(prefix_string + "Delay Time Start"),
                            self.getValue(prefix_string + "Delay Time Stop"),
                            self.getValue(prefix_string + "Delay Time Number"),
                        ),
                        path=self.getValue(prefix_string + "Sequence Path"),
                        custom_params=self.getValue(prefix_string + "Custom Params"),
                        trigger_mode=self.getValue(prefix_string + "Trigger Mode"),
                        trigger_delay=self.getValue(
                            f"Sequencer {i+1} - Advance - Trigger Delay"
                        ),
                        repetitions=self.getValue(
                            f"Sequencer {i+1} - Advance - Repetitions"
                        ),
                        period=self.getValue(f"Sequencer {i+1} - Advance - Period"),
                    )
                except Exception as e:
                    self.log_sequence_error(e, i)

    def queue_waveforms(self):
        """Queue waveforms on AWGs."""
        for i, updated in enumerate(self.waveforms_updated):
            if updated:
                prefix_string = f"Sequencer {i+1} - Sequencer Program - "
                wave_path = self.getValue(prefix_string + "Waveform Path")
                if updated and wave_path:
                    vector_list = self.csv_path_to_vector(wave_path)
                    self.controller.sgchannels[i].awg.reset_queue()
                    for j in range(int(len(vector_list) / 2)):
                        self.controller.sgchannels[i].awg.queue_waveform(
                            vector_list[2 * j], vector_list[2 * j + 1]
                        )

    def update_ct(self):
        """Update command table"""
        for i, updated in enumerate(self.cts_updated):
            if updated:
                prefix_string = f"Sequencer {i+1} - Sequencer Program - "
                ct_path = self.getValue(prefix_string + "Command Table Path")
                if updated and ct_path:
                    with open(ct_path, "r", encoding="UTF-8") as f:
                        ct = json.loads(f.read())
                        self.controller.sgchannels[i].awg.ct.load(ct)

    def compile_sequences(self):
        """Handles the compilation and waveform upload of the AWGs."""
        for i, updated in enumerate(self.sequencers_updated):
            if updated:
                sequence_type = self.getValue(
                    f"Sequencer {i+1} - Sequencer Program - Sequence"
                )
                if sequence_type != "None":
                    try:
                        if self.waveforms_updated[i]:
                            self.controller.sgchannels[
                                i
                            ].awg.compile_and_upload_waveforms()
                        else:
                            self.controller.sgchannels[i].awg.compile()
                    except Exception as e:
                        self.log_sequence_error(e, i)

    def log_sequence_error(self, message, sequencer):
        if message:
            print(f"sequencer {sequencer}: {message}")
            if self.sequence_error[sequencer]:
                self.sequence_error[
                    sequencer
                ] = f"{self.sequence_error[sequencer]} | {message}"
            else:
                self.sequence_error[sequencer] = message
            self.setValue(
                f"Sequencer {sequencer+1} - Error - Sequence Error",
                self.sequence_error[sequencer],
            )

    def reset_sequence_error(self):
        self.sequence_error = [""] * 8
        for i in range(8):
            self.setValue(f"Sequencer {i+1} - Error - Sequence Error", "")

    def reset_sequencer_defaults(self, seq_num):
        prefix = f"Sequencer {seq_num} - "
        self.reset_default(f"{prefix}Sequencer Program - Trigger Mode")
        self.reset_default(f"{prefix}Sequencer Program - Pulse Amplitude Start")
        self.reset_default(f"{prefix}Sequencer Program - Pulse Amplitude Stop")
        self.reset_default(f"{prefix}Sequencer Program - Pulse Amplitude Number")
        self.reset_default(f"{prefix}Sequencer Program - Pulse Amplitude")
        self.reset_default(f"{prefix}Sequencer Program - Pulse Width")
        self.reset_default(f"{prefix}Sequencer Program - Delay Time Start")
        self.reset_default(f"{prefix}Sequencer Program - Delay Time Stop")
        self.reset_default(f"{prefix}Sequencer Program - Delay Time Number")
        self.reset_default(f"{prefix}Advance - Trigger Delay")
        self.reset_default(f"{prefix}Advance - Repetitions")
        self.reset_default(f"{prefix}Advance - Period")
        self.bCfgUpdated = True

    def reset_default(self, quant_name):
        quant = self.instrCfg.getQuantity(quant_name)
        quant.setValue(quant.def_value)
        self.interface.reportSet(quant, quant.def_value)

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
                if hasattr(result, attr):
                    result = getattr(result, attr)
                else:
                    return None
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
    def csv_path_to_vector(path):
        """Import complex valued vectors from a .csv file path"""
        vectors = []
        with open(path, newline="") as csvfile:
            datareader = csv.reader(csvfile, delimiter=",", quotechar="|")
            for row in datareader:
                vectors.append(np.array(row))
        return vectors

    @staticmethod
    def map_name_to_channel(s):
        if "1" in s:
            return 0
        elif "2" in s:
            return 1
        elif "3" in s:
            return 2
        elif "4" in s:
            return 3
        elif "5" in s:
            return 4
        elif "6" in s:
            return 5
        elif "7" in s:
            return 6
        elif "8" in s:
            return 7
        else:
            raise Exception("Mapping to AWG index not possible!")
