import re
import types


class Element:
    def __init__(
        self,
        node: str,
        name: str,
        datatype: str,
        group: str,
        section: str,
        label: str = None,
        unit: str = None,
        def_value: str = None,
        tooltip: str = None,
        low_lim: str = None,
        high_lim: str = None,
        x_name: str = None,
        x_unit: str = None,
        combo_defs: str = None,
        cmd_defs: str = None,
        state_quant: str = None,
        second_state_quant: str = None,
        state_values: str = None,
        second_state_values: str = None,
        model_values: str = None,
        option_values: str = None,
        permission: str = None,
        show_in_measurement_dlg: str = None,
        set_cmd: str = None,
        get_cmd: str = None,
        mapping: str = None,
        extended_map: bool = False,
        multi_section: bool = False,
    ):
        self._node = node
        self._name = name
        self._datatype = datatype
        self.group = group
        self.section = section
        self._label = label
        self._unit = unit
        self._def_value = def_value
        self._tooltip = tooltip
        self._low_lim = low_lim
        self._high_lim = high_lim
        self._x_name = x_name
        self._x_unit = x_unit
        self._combo_defs = combo_defs
        self._cmd_defs = cmd_defs
        self._state_quant = state_quant
        self._second_state_quant = second_state_quant
        self._state_values = state_values
        self._second_state_values = second_state_values
        self._model_values = model_values
        self._option_values = option_values
        self._permission = permission
        self._show_in_measurement_dlg = show_in_measurement_dlg
        self._set_cmd = set_cmd
        self._get_cmd = get_cmd
        self._mapping = mapping
        self._extended_map = extended_map
        self._multi_section = multi_section
        self._generated = False

    @staticmethod
    def nested_getattr(obj, attr_str):
        attr_list = attr_str.split(".")
        result = obj
        pattern = r"\[(.*)\]"
        for element in attr_list:
            match = re.search(pattern, element)
            if match:
                attr = element[: match.start()] + element[match.end() :]
                index = int(element[match.start() + 1 : match.end() - 1])
                result = getattr(result, attr)
                if len(result) <= index:
                    result = result[0]
                else:
                    result = result[index]
            else:
                if hasattr(result, element):
                    result = getattr(result, element)
                    if type(result) == types.MethodType:
                        result = None
                else:
                    result = None
        return result

    def generate(self, device):
        """
        This function writes and returns the `.ini` string for a single
        quantity from a `zhinst.toolkit.Parameter`.

        """
        if self._node and device:
            param = self.nested_getattr(device, self._node)
        else:
            param = None
        if self._unit is None:
            if param and param._unit != "None":
                self._unit = param._unit
        if param and self._def_value is None:
            self._def_value = param()
        if param and self._tooltip is None:
            self._description = param._description
            self._path = param._path.split("/", 2)
            if self._path[-2] == "ZI":
                self._path = "/".join(self._path[-2:]).lower()
            else:
                self._path = self._path[-1].lower()
            self._tooltip = f"<html><body><p>{self._description}</p><p><b>{self._path}</b></p></body></html>"
        elif self._tooltip is not None:
            self._tooltip = f"<html><body><p>{self._tooltip}</p></body></html>"
        if param and self._mapping is None and param._map is not None:
            if self._extended_map is False:
                self._mapping = param._map
            elif self._extended_map is True:
                self._mapping = param._map_extended
        if self._combo_defs is None and self._mapping is not None:
            self._combo_defs = list(self._mapping.values())
            for i in range(len(self._combo_defs)):
                if isinstance(self._combo_defs[i], list):
                    if self._extended_map is False:
                        self._combo_defs[i] = self._combo_defs[i][1]
                    elif self._extended_map is True:
                        self._combo_defs[i] = self._combo_defs[i][2]
        if self._cmd_defs is None and self._mapping is not None:
            if self._extended_map is False:
                self._cmd_defs = list(self._mapping.keys())
            elif self._extended_map is True:
                self._cmd_defs = list(self._mapping.values())
                for i in range(len(self._cmd_defs)):
                    self._cmd_defs[i] = self._cmd_defs[i][0]
        if param and self._permission is None:
            if "Read" in param._properties and "Write" not in param._properties:
                self._permission = "READ"
                if self._get_cmd is None:
                    self._get_cmd = self._node
            elif "Write" in param._properties and "Read" not in param._properties:
                self._permission = "WRITE"
                if self._set_cmd is None:
                    self._set_cmd = self._node
            elif "Write" in param._properties and "Read" in param._properties:
                self._permission = "BOTH"
                if self._get_cmd is None:
                    self._get_cmd = self._node
                if self._set_cmd is None:
                    self._set_cmd = self._node
        if self._node is not None and self._permission is not None:
            if self._permission == "READ":
                if self._get_cmd is None:
                    self._get_cmd = self._node
            elif self._permission == "WRITE":
                if self._set_cmd is None:
                    self._set_cmd = self._node
            elif self._permission == "BOTH":
                if self._get_cmd is None:
                    self._get_cmd = self._node
                if self._set_cmd is None:
                    self._set_cmd = self._node
        self._generated = True

    def __str__(self):

        if not self._generated:
            raise Exception(
                "The element needs to be generated before it can be converted into a string"
            )

        element_str = ""
        if self._datatype in list(("VECTOR", "VECTOR_COMPLEX", "BUTTON")):
            element_str += f"[{self.section} - {self._name}]\n"
        elif self._multi_section:
            element_str += f"[{self.section} - {self.group} - {self._name}]\n"
        else:
            element_str += f"[{self.group} - {self._name}]\n"
        element_str += f"datatype: {self._datatype}\n"
        element_str += f"group: {self.group}\n"
        element_str += f"section: {self.section}\n"
        if self._label is not None:
            element_str += f"label: {self._label}\n"
        else:
            element_str += f"label: {self._name}\n"
        if self._unit is not None:
            element_str += f"unit: {self._unit}\n"
        if self._def_value is not None:
            element_str += f"def_value: {self._def_value}\n"
        if self._tooltip is not None:
            element_str += f"tooltip: {self._tooltip}\n"
        if self._low_lim is not None:
            element_str += f"low_lim: {self._low_lim}\n"
        if self._high_lim is not None:
            element_str += f"high_lim: {self._high_lim}\n"
        if self._x_name is not None:
            element_str += f"x_name: {self._x_name}\n"
        if self._x_unit is not None:
            element_str += f"x_unit: {self._x_unit}\n"
        if self._combo_defs is not None and self._datatype == "COMBO":
            for i in range(len(self._combo_defs)):
                element_str += f"combo_def_{i+1}: {self._combo_defs[i]}\n"
                if self._cmd_defs is not None:
                    element_str += f"cmd_def_{i+1}: {self._cmd_defs[i]}\n"
        if self._state_quant is not None:
            element_str += f"state_quant: {self._state_quant}\n"
            if self._state_values is not None:
                for i in range(len(self._state_values)):
                    element_str += f"state_value_{i+1}: {self._state_values[i]}\n"
        # We need to support older versions as well
        # if self._second_state_quant is not None:
        #     element_str += f"second_state_quant: {self._second_state_quant}\n"
        #     if self._second_state_values is not None:
        #         for i in range(len(self._second_state_values)):
        #             element_str += f"second_state_value_{i+1}: {self._second_state_values[i]}\n"
        if self._model_values is not None:
            for i in range(len(self._model_values)):
                element_str += f"model_value_{i+1}: {self._model_values[i]}\n"
        if self._option_values is not None:
            for i in range(len(self._option_values)):
                element_str += f"option_value_: {self._option_values[i]}\n"
        if self._permission is not None:
            element_str += f"permission: {self._permission}\n"
        if self._show_in_measurement_dlg is not None:
            element_str += f"show_in_measurement_dlg: {self._show_in_measurement_dlg}\n"
        if self._set_cmd is not None:
            element_str += f"set_cmd: {self._set_cmd}\n"
        if self._get_cmd is not None:
            element_str += f"get_cmd: {self._get_cmd}\n"
        element_str += "\n"
        return element_str
