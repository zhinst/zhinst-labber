import typing as t
import re

from . import helpers


class Quant:
    """Quant representation of a node-like path.

    quant: Quant node-like path.
    defs: Quant definitions.
    """

    def __init__(self, quant: str, defs: dict):
        self._quant = quant
        self._defs = defs
        self._quant_no_slash = helpers.remove_leading_trailing_slashes(quant)

    def _suffix(self) -> str:
        """Suffix for the quant."""
        return self._defs.get("suffix", "").lower()

    @property
    def title(self) -> str:
        """Quant title."""
        return self._quant_no_slash

    @property
    def label(self) -> str:
        """Quant labe."""
        s = self._quant_no_slash.split("/")
        if len(self._quant) == 1:
            return self._quant
        elif s[-1].isnumeric():
            return "/".join(s[-2:])
        return s[-1]

    @property
    def group(self) -> str:
        """Quant group"""
        s = self._quant_no_slash.split("/")
        if len(s) == 1:
            return "SYSTEM"
        if s[-1].isnumeric():
            return "/".join(s[:-2])
        return "/".join(s[:-1]) + "/"

    @property
    def set_cmd(self) -> str:
        """Quant set command."""
        return self.title

    @property
    def get_cmd(self) -> str:
        """Quant get command."""
        return self.title

    @property
    def section(self) -> str:
        """Quant section."""
        dig = re.search(r"\d", self._quant_no_slash)
        if dig is not None:
            dig = int(dig.group(0))
            return "".join(
                list(self._quant_no_slash)[: self._quant_no_slash.find(str(dig)) + 1]
            )
        else:
            return self.title.split("/")[0]

    def as_dict(self) -> dict:
        """Python dictionary representation of the quant in a Labber format."""
        defs = self._defs.copy()
        defs.pop("suffix", None)
        if self._suffix():
            label = self.title + "/" + self._suffix()
        else:
            label = self.title
        res = {
            "label": label,
            "group": self.group,
            "section": self.section,
            "set_cmd": self.set_cmd,
            "get_cmd": self.get_cmd,
            "permission": "WRITE",
        }
        res.update(defs)
        return {label: res}


class NodeQuant:
    """Zurich instrument node information as a Labber quant."""

    def __init__(self, node: t.Dict):
        self.node = node
        self.node.setdefault("Options", {})
        self._node_path = helpers.delete_device_from_node_path(node["Node"].upper())
        self._node_path_no_prefix = self._node_path
        if self._node_path.startswith("/"):
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
        # HF2 does not have Unit.
        unit = self.node.get("Unit", None)
        if not unit:
            return None
        if unit.lower() in ["none", "dependent"]:
            return None
        unit = self.node["Unit"].replace("%", " percent").replace("'", "")
        # Remove degree signs etc.
        return unit.encode("ascii", "ignore").decode()

    @property
    def datatype(self) -> str:
        """Node datatype to Labber datatypes."""
        node = self.node["Node"].lower()
        unit = self.node["Type"].lower()
        if "enumerated" in unit:
            if not "READ" == self.permission:
                return "COMBO"
        boolean_nodes = ["enable", "single", "on", "busy", "ready", "reset"]
        if node.split("/")[-1] in boolean_nodes:
            return "BOOLEAN"
        if unit == "double" or "integer" in unit:
            return "DOUBLE"
        if unit == "complex":
            return "VECTOR_COMPLEX"
        if unit == "string":
            return "STRING"
        if unit in ["zivectordata", "ziadvisorwave", "zidemodsample", "zidiosample"]:
            return "VECTOR"
        if unit == "complex double":
            return "VECTOR_COMPLEX"
        if unit == "zitriggersample":
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
        if self.datatype in ["VECTOR", "VECTOR_COMPLEX"]:
            d["x_name"] = "Length"
            d["x_unit"] = "Sample"
        if flat:
            return d
        return {self.filtered_node_path: d}
