import re
import typing as t

from zhinst.labber.generator import helpers


class Quant:
    """Quant representation of a node-like path.

    Args:
        quant: Quant node-like path.
        defs: Quant definitions in Labber format.
    """

    def __init__(self, quant: str, defs: t.Dict[str, str]):
        self._quant = quant.strip("/")
        self._quant_parts = self._quant.split("/")
        self._defs = defs

    @property
    def suffix(self) -> str:
        """Suffix for the quant."""
        return self._defs.get("suffix", "").lower()

    @property
    def title(self) -> str:
        """Quant title."""
        return self._quant

    @property
    def label(self) -> str:
        """Quant label."""
        if self._quant_parts[-1].isnumeric():
            return "/".join(self._quant_parts[-2:])
        return self._quant_parts[-1]

    @property
    def group(self) -> str:
        """Quant group."""
        path = [x for x in self._quant_parts if not x.isnumeric()]
        if len([x for x in self._quant_parts if x.isnumeric()]) > 1:
            idx_ = 0
            for idx, c in enumerate(self._quant_parts):
                if c.isnumeric():
                    idx_ = idx
            return "/".join(path[: idx_ - 1])
        if len(path) > 1:
            return "/".join(path[:-1])
        return "/".join(path)

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
        digit = re.search(r"\d", self._quant)
        if digit is not None:
            digit = digit.group(0)
            return "".join(list(self._quant)[: self._quant.find(digit) + 1])
        else:
            return self.title.split("/")[0]

    def as_dict(self) -> t.Dict[str, t.Dict[str, str]]:
        """Quant as a Python dictionary.

        Returns:
            Quant in a Python dictionary format.
        """
        defs = self._defs.copy()
        defs.pop("suffix", None)
        if self.suffix:
            label = self.title + "/" + self.suffix
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
    """Zurich instruments node information as a Labber quant.

    Node information is transformed into a Labber suitable format.

    Args:
        node_info: Node information.

        Example format:

            {
                "Node": "/DEV1234/QACHANNELS/1/GENERATOR/AUXTRIGGERS/0/CHANNEL",
                "Description": "Selects the source of the digital Trigger.",
                "Properties": "Read, Write, Setting",
                "Type": "Integer (enumerated)",
                "Unit": "None",
                "Options": {}
            }
    """

    def __init__(self, node_info: t.Dict):
        self._validate_node_info(node_info)
        self._node_info = node_info
        self._node_info.setdefault("Options", {})
        self._node_path = helpers.delete_device_from_node_path(
            node_info["Node"].upper()
        )
        self._node_path_no_prefix = self._node_path.strip("/")
        self._path_parts = self._node_path_no_prefix.split("/")
        self._properties = node_info.get("Properties", "").lower()

    def _validate_node_info(self, node_info: t.Dict) -> None:
        """Validate Node info.
    
        Generally nodes that requires polling are ignored due to limited
        Labber functionality. This can change in the future.
        
        Args:
            node_info: Node info in ZIPython format.
        Raises:
            ValueError: Value(s) are not supported.
        """
        not_allowed_types = [
            "ZIPWAWave", 
            "ZITriggerSample", 
            "ZICntSample", 
            "ZIScopeWave",
            "ZIAuxInSample",
            "ZIImpedanceSample"
        ]
        if node_info.get("Type", None) in not_allowed_types:
            raise ValueError(f"Node type {node_info.get('Type', None)} not allowed.")

    @staticmethod
    def _enum_description(value: str) -> t.Tuple[str, str]:
        """Split enum description into tuple

        Args:
            value: Node enum description.
        Returns:
            Enum description split into a tuple."""
        v = value.split(": ")
        if len(v) > 1:
            v2 = v[0].split(",")
            return v2[0].strip('"'), v[-1]
        return "", v[0]

    @property
    def filtered_node_path(self) -> str:
        """Filtered node path without device prefix."""
        return self._node_path

    @property
    def permission(self) -> str:
        """Quant permission."""
        if "read" in self._properties and "write" in self._properties:
            return "BOTH"
        if "read" in self._properties:
            return "READ"
        if "write" in self._properties:
            return "WRITE"
        return "NONE"

    @property
    def show_in_measurement_dlg(self) -> t.Optional[str]:
        """Show in measurement dialog."""
        if self.datatype in ["VECTOR", "COMPLEX", "VECTOR_COMPLEX"]:
            if "result" in self.label.lower() or "wave" in self.label.lower():
                return "True"

    @property
    def section(self) -> str:
        """Quant section."""
        for idx, x in enumerate(self._path_parts, 1):
            if idx == 3:
                break
            if x.isnumeric():
                return "/".join(self._path_parts[0:idx])
        return self._path_parts[0]

    @property
    def group(self) -> str:
        """Quant group.

        Node path indexes are removed from the group representation.
        """
        path = [x for x in self._path_parts if not x.isnumeric()]
        if len([x for x in self._path_parts if x.isnumeric()]) > 1:
            idx_ = 0
            for idx, c in enumerate(self._path_parts):
                if c.isnumeric():
                    idx_ = idx
            return "/".join(path[: idx_ - 1])
        if len(path) > 1:
            return "/".join(path[:-1])
        return "/".join(path)

    @property
    def label(self) -> str:
        """Quant label.

        Label is a node path without DEV-prefix."""
        return self._node_path_no_prefix

    @property
    def combo_defs(self) -> t.Dict[str, str]:
        """Labber combo definitions.

        Turns enumerated options into a Labber combo definitions.
        No combo definitions are generated if the node is READ-only.

        Returns:
            Labber combo definitions.

            Format:

                {
                    "cmd_def_1": 1,
                    "combo_def_1": 1,
                    "cmd_def_n": 1,
                    "combo_def_n": 1
                }
        """
        if "enumerated" in self._node_info["Type"].lower():
            if self.permission == "READ":
                return {}
        defs = {}
        for idx, (k, v) in enumerate(self._node_info["Options"].items(), 1):
            value, _ = self._enum_description(v)
            defs[f"cmd_def_{idx}"] = value if value else str(k)
            defs[f"combo_def_{idx}"] = value if value else str(k)
        return defs

    @property
    def tooltip(self) -> str:
        """Node tooltip as HTML body.

        Options are converted into HTML lists and node is bolded.

        For COMBO and READ-only quants, a bolded text to highlight READ-ONLY
        is used.
        """
        items = []
        description = self._node_info["Description"]
        for k, v in self._node_info["Options"].items():
            value, desc = self._enum_description(v)
            if self.permission == "READ":
                items.append(f"{k}: {desc}")
            else:
                items.append(f"{value if value else k}: {desc}")
        if self.permission == "READ" and self.datatype in ["STRING", "COMBO"]:
                description = "<p><b>READ-ONLY!</p></b>" + description
        return helpers.tooltip(
            description,
            enum=items,
            node=self._node_path_no_prefix.upper(),
        )

    @property
    def unit(self) -> t.Optional[str]:
        """Node unit to Labber units.

        Special characters are ignored or replaced in the string representation.
        """
        # HF2 does not have Unit.
        unit = self._node_info.get("Unit", None)
        if not unit:
            return None
        if unit.lower() in ["none", "dependent", "many", "boolean"]:
            return None
        unit = self._node_info["Unit"].replace("%", " percent").replace("'", "")
        # Remove degree signs etc.
        return unit.encode("ascii", "ignore").decode()

    @property
    def datatype(self) -> str:
        """Node datatype to Labber datatypes."""
        unit = self._node_info.get("Type", "").lower()
        if not unit:
            return ""
        if "enumerated" in unit:
            return "COMBO"
        boolean_nodes = [
            "enable",
            "single",
            "on",
            "busy",
            "ready",
            "reset",
            "preampenable",
        ]
        if self._path_parts[-1].lower() in boolean_nodes:
            return "BOOLEAN"
        string_nodes = ["alias", "serial", "devtype", "fwrevision"]
        if self._path_parts[-1].lower() in string_nodes:
            return "STRING"
        if unit == "double" or "integer" in unit:
            return "DOUBLE"
        if unit == "string":
            return "STRING"
        if unit in ["zivectordata", "ziadvisorwave"]:
            return "VECTOR"
        if unit in ["zidemodsample", "zidiosample", "complex double"]:
            return "COMPLEX"
        if unit in ["complex"]:
            return "VECTOR_COMPLEX"
        return "STRING"

    @property
    def set_cmd(self) -> t.Optional[str]:
        """Set command for the node if the node is writable."""
        if "write" in self._properties:
            return self._node_path_no_prefix

    @property
    def get_cmd(self) -> t.Optional[str]:
        """Get command for the node if the node is readable."""
        if "read" in self._properties:
            return self._node_path_no_prefix

    @property
    def title(self) -> str:
        """Title of the quant."""
        return self.label

    def as_dict(self) -> t.Dict[str, t.Dict]:
        """Python dictionary representation of the node quant.

        Due to some problems with Labber, some modification for READ-only nodes are 
        needed:

            If datatype is COMBO and permission is READ:
                - COMBO -> Datatype DOUBLE (enumerated number)
            if datatype is COMBO or STRING and permission is READ:
                - Permission is removed from quant and a tooltip text to highlight
                that this is READ-only.

        Returns:
            Dictionary where the keys and values are in a Labber format.
        """
        d = {}
        d["section"] = self.section.lower()
        d["group"] = self.group.lower()
        d["label"] = self.label.lower()
        if self.datatype:
            if self.permission == "READ" and self.datatype == "COMBO":
                d["datatype"] = "DOUBLE"
            else:
                d["datatype"] = self.datatype
        if self.unit:
            d["unit"] = self.unit
        d["tooltip"] = self.tooltip
        d.update(self.combo_defs)
        if not (self.permission == "READ" and self.datatype in ["COMBO", "STRING"]):
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
        return {self.filtered_node_path.lower(): d}


class QuantGenerator:
    """Quant generator.

    Args:
        quants: List of quants in node-like format.
    """

    def __init__(self, quants: t.List[str]) -> None:
        self.quants = list(map(helpers.delete_device_from_node_path, quants))

    @staticmethod
    def find_nth_occurrence(s: str, target: str, n: int) -> int:
        """Find nth occurrence of the target in a string.

        Args:
            s: String
            target: Target string to find from s
            n: Nth occurrence of target in s

        Returns:
            Index of the nth occurrence in the string. -1 if not found."""
        if s.count(target) < n + 1:
            return -1
        return s.find(target, s.find(target) + n)

    @staticmethod
    def path_from_indexes(
        quant_original: str,
        quant: str,
        i: int,
        indexes: t.List[int],
        quants: t.List[str],
    ) -> t.List[str]:
        """Recursively generate quant path from given indexes.

        Args:
            quant_original: Original quant
            quant: Traveled quant
            i: Index of the wildcard *
            indexes: Number of indexes added to wildcard
            quants: List of quant paths

        Returns:
            List of generated quant paths.
        """
        for x in range(indexes[i]):
            idx = QuantGenerator.find_nth_occurrence(quant_original, "*", i)
            q_list = list(quant)
            if idx != -1:
                q_list[idx] = str(x)
                try:
                    quants = QuantGenerator.path_from_indexes(
                        quant_original, "".join(q_list), i + 1, indexes, quants
                    )
                except IndexError:
                    quants.append("".join(q_list))
        return quants

    @staticmethod
    def _to_regex(s: str) -> str:
        """Quant to regex.

        Wildcard `*` is replaced with any numbers and case is ignored.

        Args:
            s: String to be transformed into regex.
        Returns:
            Regex of the input string."""
        s = s.replace("/", r"\/")
        s = s.replace("*", r"[0-9]+")
        return "(?i)" + s

    def quant_paths(
        self, quant: str, indexes: t.List[t.Union[str, int]]
    ) -> t.List[str]:
        """Quant paths for all given indexes.

        Args:
            quant: Quant node-like path.
            indexes: Indexes for wildcards (*). 'dev' | int
                'dev' = Indexes from device.
                int = The amount of indexes to be added.

        Returns:
            Quant paths with given indexes.
        """
        wc_count = quant.count("*")
        if wc_count == 0:
            return [quant]
        if not indexes:
            indexes = ["dev" for _ in range(wc_count)]
        if wc_count > len(indexes):
            diff = wc_count - len(indexes)
            indexes += ["dev" for _ in range(diff)]

        idxs = []
        for enum, idx in enumerate(indexes):
            # Get the number of indexes from device.
            if idx == "dev":
                paths = set()
                idx_pos = self.find_nth_occurrence(quant, "*", enum) + 1
                p = re.compile(self._to_regex(quant[:idx_pos]))
                for path in list(filter(p.match, self.quants)):
                    paths.add(re.findall(r"[0-9]+", path)[enum])
                idxs.append(len(paths))
            else:
                # Add any number of indexes.
                idxs.append(idx)
        return self.path_from_indexes(quant, quant, 0, idxs, [])
