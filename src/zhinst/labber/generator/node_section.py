import typing as t

from . import helpers


class NodeSection:
    """Zurich instrument node information in a labber format."""
    def __init__(self, node: t.Dict):
        self.node = node
        self.node.setdefault("Options", {})
        self._node_path = helpers.delete_device_from_node_path(node["Node"].upper())
        self._node_path_no_prefix = self._node_path
        if self._node_path.startswith('/'):
            self._node_path_no_prefix = self._node_path[1:]
        self._properties = self.node["Properties"].lower()

    @property
    def filtered_node_path(self) -> str:
        """Filtered node path with device prefix."""
        return self._node_path

    @property
    def permission(self) -> str:
        """Permission"""
        if "read" in self._properties and "write" in self._properties:
            return "BOTH"
        if "read" in self._properties:
            return "READ"
        if "write" in self._properties:
            return "WRITE"
        return "NONE"

    @property
    def show_in_measurement_dlg(self) -> t.Optional[str]:
        """Show in measurement dialog"""
        if self.node["Type"] in ["VECTOR", "COMPLEX", "VECTOR_COMPLEX"]:
            if "RESULT" in self.label or "WAVE" in self.label:
                return "True"

    @property
    def section(self) -> str:
        """Section in Labber where the node representation will be"""
        parsed = self._node_path_no_prefix.upper().split("/")
        for idx, x in enumerate(parsed, 1):
            if idx == 3:
                break
            if x.isnumeric():
                return "/".join(parsed[0:idx])
        return parsed[0]

    @property
    def group(self) -> str:
        """Group in Labber where the node representation will be"""
        node_path = self._node_path_no_prefix
        path = [x for x in node_path.split("/") if not x.isnumeric()]
        if len(path) > 1:
            return "/".join(path[:-1])
        return "/".join(path)

    @property
    def label(self) -> str:
        """Node label."""
        return self._node_path_no_prefix

    @property
    def combo_def(self) -> t.List[dict]:
        """Combo definition.
        
        Turns enumerated options into Labber combo.
        """
        if "enumerated" in self.node["Type"].lower():
            if "READ" == self.permission:
                return []
        opt = self.node["Options"]
        combos = []
        for idx, (k, v) in enumerate(opt.items(), 1):
            value, _ = helpers.enum_description(v)
            res = {
                f"cmd_def_{idx}": value if value else str(k),
                f"combo_def_{idx}": value if value else str(k),
            }
            combos.append(res)
        return combos

    @property
    def tooltip(self) -> str:
        """Node tooltip as HTML."""
        node_path = self._node_path_no_prefix.upper()
        items = []
        for k, v in self.node["Options"].items():
            value, desc = helpers.enum_description(v)
            items.append(f"{value if value else k}: {desc}")
        return helpers.tooltip(self.node["Description"], enum=items, node=node_path)

    @property
    def unit(self) -> t.Optional[str]:
        """Node unit to Labber units"""
        if self.node["Unit"].lower() == "none":
            return None
        if self.node["Unit"].lower() == "dependent":
            return None
        unit = self.node["Unit"].replace("%", " percent").replace("'", "")
        # Remove degree signs etc.
        return unit.encode("ascii", "ignore").decode()

    @property
    def datatype(self) -> t.Optional[str]:
        """Node datatype to Labber datatypes"""
        unit = self.node["Type"]
        if "enumerated" in unit.lower():
            if not "READ" == self.permission:
                return "COMBO"
        boolean_nodes = ["ENABLE", "SINGLE", "ON", "BUSY"]
        if self.node["Node"].split("/")[-1].upper() in boolean_nodes:
            return "BOOLEAN"
        if unit == "Double" or "integer" in unit.lower():
            return "DOUBLE"
        if unit == "Complex":
            return unit.upper()
        if unit == "ZIVectorData":
            return "VECTOR"
        if unit == "String":
            return "STRING"
        if unit == "ZIAdvisorWave":
            return "VECTOR"
        if unit == "Complex Double":
            return "COMPLEX"
        if unit == "ZIVectorData":
            return "VECTOR"
        if unit == "ZIDemodSample":
            return "VECTOR"
        if unit == "ZIDIOSample":
            return "VECTOR"
        if unit == "ZITriggerSample":
            return "STRING"
        return "STRING"

    @property
    def set_cmd(self) -> t.Optional[str]:
        """Set command for the node. Nodepath"""
        if "write" in self._properties:
            return self._node_path_no_prefix

    @property
    def get_cmd(self) -> t.Optional[str]:
        """Get command for the node. Nodepath"""
        if "read" in self._properties:
            return self._node_path_no_prefix

    @property
    def title(self):
        """Title of the quant."""
        return self.label

    def as_dict(self, flat=True) -> dict:
        """Node in Labber format."""
        d = {}
        d["section"] = self.section
        d["group"] = self.group
        d["label"] = self.label
        if self.datatype:
            d["datatype"] = self.datatype
        if self.unit:
            d["unit"] = self.unit
        d["tooltip"] = self.tooltip
        for item in self.combo_def:
            for k, v in item.items():
                d[k] = v
        if self.permission:
            d["permission"] = self.permission
        if self.set_cmd:
            d["set_cmd"] = self.set_cmd
        if self.get_cmd:
            d["get_cmd"] = self.get_cmd
        if self.show_in_measurement_dlg:
            d["show_in_measurement_dlg"] = self.show_in_measurement_dlg
        if self.datatype in ['VECTOR', 'VECTOR_COMPLEX']:
            d["x_name"] = "Length"
            d["x_unit"] = "Sample"
        if flat:
            return d
        return {self.title: d}
