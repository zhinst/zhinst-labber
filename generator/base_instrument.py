from pathlib import Path
from element import Element
import zhinst.toolkit as tk


class BaseInstrument:
    def __init__(
        self,
        name: str,
        path: Path,
        version: str = "1.0",
        model_options: list = [],
        hardware_loop: bool = True,
    ) -> None:
        self.name = name
        self.path = path
        self.version = version
        self.model_options = model_options
        self.ini_file = ""
        self._dict = dict()
        self.hardware_loop = hardware_loop

    @staticmethod
    def setup(name: str, version: str, model_options: list, hardware_loop:bool):

        model_option_str = ""
        for count, opt in enumerate(model_options):
            model_option_str += f"model_str_{count+1}: {opt}\n"

        ini_file = f""" \
        # Instrument driver configuration file.

        [General settings]
        # The General settings-section define name and version of the driver.
        # Note that it is the name property in this section that sets the
        # driver name, not the name of the driver definition INI file.

        # The name is shown in all the configuration windows
        name: {name}
        # The version string should be updated whenever changes are made to
        # this config file
        version: {version}

        # Name of folder containing the code defining a custom driver. Do not
        # define this item or leave it blank for any standard driver based on
        # the built-in VISA interface.
        driver_path: {name.replace(" ","_")}

        # Pre-defined communication interface for instrument, default is  GPIB.
        interface: Other

        # Pre-defined startup option for instrument, default is Set config.
        startup: Do nothing

        # Set to True if driver supports hardware looping. Default is False
        support_hardware_loop: {"True" if hardware_loop else "False"}

        # Set to True if driver supports hardware arming. Default is False
        support_arm: True

        [Model and options]
        # The Model and options-section provides a way to enable/disable
        # certain features of a driver depending on the instrument
        # model/installed options.

        # List of models supported by this driver
        {model_option_str}

        # All quantities are defined in separate sections, with the name of the
        # quantity given by the section header. The properties of a quantity
        # are defined by a number of keywords, see below for a list the
        # possible options. Only the datatype  keyword is mandatory, the other
        # ones are optional.
        #
        # datatype:                 The data type should be one of DOUBLE,
        #                           BOOLEAN, COMBO, STRING, COMPLEX, VECTOR,
        #                           VECTOR_COMPLEX, PATH or BUTTON. Only DOUBLE,
        #                           BOOLEAN and COMBO datatypes can be stepped
        #                           in a measurement. The BUTTON datatype does
        #                           not have an associated value, and can
        #                           therefore not be controlled from the
        #                           Measurement program. It is typically used to
        #                           manually force an instrument to perform a
        #                           certain task.
        # label:                    Label shown next to control in user
        #                           interface. If not specified, the label
        #                           defaults to the name of the quantity.
        # unit:                     Unit for the quantity.
        # def_value:                Default value.
        # tooltip:                  Tool tip shown when hovering the mouse over
        #                           the control in the driver GUI.
        # low_lim:                  Lowest allowable value. Defaults to -INF.
        # high_lim:                 Highest allowable values. Defaults to  +INF.
        # x_name:                   X-axis label for a vector data. Only valid
        #                           if datatype  is VECTOR or VECTOR_COMPLEX.
        # x_unit:                   X-axis unit for a vector data. Only valid if
        #                           datatype is VECTOR or VECTOR_COMPLEX.
        # combo_def_1,              Options for a pull-down combo box. Only used
        # combo_def_2,              when datatype is COMBO.
        # ...:
        # group:                    Name of the group where the control belongs.
        # section:                  Name of the section where the control
        #                           belongs.
        # state_quant:              Quantity that determines this control’s
        #                           visibility.
        # second_state_quant:       A second quantity that determines this
        #                           control’s visibility. This is an ‘AND’
        #                           operation: if a control has a state_quant
        #                           and a second_state_quant, both need to be
        #                           True for it to appear
        # state_value_1,            Values of  "state_quant"  for which the
        # state_value_2,            control is visible.
        # ...:
        # second_state_value_1,     Values of "second_state_quant" for which the
        # second_state_value_2,     control is visible, if "state_quant" is also
        # ...:                      True.
        # model_value_1,            Values of  "model"  for which the control is
        # model_value_2,            visible. The value must match one of the
        # ...:                      models defined in the Model and
        #                           Options-section described above.
        # option_value_1,           Values of  "option"  for which the control
        # option_value_2,           is visible. The value must match one of the
        # ...:                      options defined in the Model and
        #                           Options-section described above.
        # permission:               Sets read/writability, options are BOTH,
        #                           READ, WRITE or NONE. Default is BOTH.
        # show_in_measurement_dlg:  This setting is optional. If True, the
        #                           the quantity will be automatically shown
        #                           when adding the instrument to a Measurement
        #                           configuration. This is useful for instrument
        #                           that contain a lot of quantities, but where
        #                           most are not likely to be stepped in a
        #                           measurement
        # set_cmd:                  Command used to send data to the instrument.
        #                           Put "<*>" where the value should appear. If
        #                           "<*>" does not occur in the string, the
        #                           value will be added after the command.
        # get_cmd:                  Command used to get the data from the
        #                           instrument. Default is set_cmd?.
        # cmd_def_1,                List of strings that define what is sent
        # cmd_def_2,                to/read from an instrument for a quantity
        # ...:                      that is defined as a a list of multiple
        #                           options. Only used when datatype is COMBO.

        """
        return ini_file

    def add_element(self, element: Element):
        if not element.section in self._dict.keys():
            self._dict[element.section] = dict()
        if not element.group in self._dict[element.section].keys():
            self._dict[element.section][element.group] = list()
        self._dict[element.section][element.group].append(element)

    def validate(self, device: tk.BaseInstrument):
        for groups in self._dict.values():
            for elements in groups.values():
                for element in elements:
                    element.generate(device)

    def write_ini(self):
        self.ini_file = BaseInstrument.setup(self.name,self.version,self.model_options, self.hardware_loop)
        for section in self._dict.keys():
            for group in self._dict[section]:
                self.ini_file += f"""\

                #########################################
                # SECTION: {section}
                # GROUP: {group}

                """
                for element in self._dict[section][group]:
                    self.ini_file += str(element)


        init_file = self.path / f"{self.name.replace(' ', '_')}.ini"
        init_file.parents[0].mkdir(parents=True, exist_ok=True)
        self.ini_file = "\n".join([m.lstrip() for m in self.ini_file.split("\n")])
        with init_file.open("w") as f:
            f.write(self.ini_file)
