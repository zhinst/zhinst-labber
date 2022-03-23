import re
import typing as t

from zhinst.labber.generator.helpers import tooltip


class LabberConfiguration:
    """Labber JSON configuration handler.

    Parses selected values from given settings based on name and mode.

    Args:
        name: Name of the Zurich Instrument object.
        mode: What parts to read from the settings file.
            'NORMAL' | 'ADVANCED'
        settings: Settings for the given object
            JSON schema: `zhinst/labber/resources/settings_json_schema.json`
    """

    def __init__(self, name: str, mode: str, settings: t.Dict):
        self._name = name.upper()
        self._mode = mode.lower()
        self.json_settings = settings.copy()
        self._set_name = list(
            filter(self._matching_name, list(self.json_settings.keys()))
        )
        if self._set_name:
            self._set_name = self._set_name[0]
            self.dev_settings = self.json_settings[self._set_name]
        else:
            self._set_name = self._name
            self.dev_settings = {}
        self._quants = self._find_quants()

    def _matching_name(self, s: str) -> bool:
        """Check if input matches with settings name.

        Returns:
            if input matches name.
        """
        if re.match(f"{s.lower()}(\d+)?$", self._name.lower()):
            return True
        return False

    def _find_quants(self) -> t.Dict:
        """Find quants based on device type and selected mode.

        Returns:
            Dictionary of all matching quant objects.
        """
        quants = self.json_settings["common"].get("quants", {}).copy()
        if self.dev_settings:
            quants.update(self.dev_settings.get("quants", {}))

        for quant, defs in quants.copy().items():
            if not defs.get("conf", {}) or defs.get("add", None) is None:
                quants.pop(quant)
                continue
            if defs["conf"].get("tooltip", None):
                quants[quant]["conf"]["tooltip"] = tooltip(defs["conf"]["tooltip"])
            if "mapping" in defs.keys():
                map_ = defs["mapping"].get(self._set_name, {})
                if not map_:
                    quants.pop(quant)
                    continue
                quants.pop(quant)
                quants[map_["path"]] = {
                    "indexes": map_["indexes"],
                    "conf": defs["conf"],
                    "add": defs["add"],
                }
            elif "dev_type" in defs.keys():
                if not self._name in defs["dev_type"]:
                    quants.pop(quant)
        return quants

    @property
    def version(self) -> str:
        """Settings JSON version."""
        return self.json_settings["version"]

    @property
    def general_settings(self) -> t.Dict:
        """Labber configuration file `General settings`-section."""
        if self.dev_settings:
            return self.dev_settings["generalSettings"]
        return self.json_settings["common"]["generalSettings"]

    @property
    def ignored_nodes(self) -> t.List[str]:
        """List of ignored nodes based on device and selected mode."""
        ignored_common = self.json_settings["common"].get("ignoredNodes", {})
        common_norm = ignored_common.get("normal", [])
        common_adv = ignored_common.get("advanced", [])
        if self.dev_settings:
            ignored_dev = self.dev_settings.get("ignoredNodes", {})
            dev_norm = ignored_dev.get("normal", [])
            dev_adv = ignored_dev.get("advanced", [])
            if self._mode == "normal":
                return common_norm + common_adv + dev_adv + dev_norm
            else:
                return dev_adv + common_adv
        if self._mode == "normal":
            return common_norm + common_adv
        return common_adv

    @property
    def quants(self) -> t.Dict:
        """Quants based on device type and selected mode."""
        return self._quants

    @property
    def quant_sections(self) -> t.Dict[str, str]:
        """Quant sections based on device type and selected mode."""
        common = self.json_settings["common"]["sections"]
        if self.dev_settings:
            dev = self.dev_settings.get("sections", {})
            common.update(dev)
            return common
        return common

    @property
    def quant_groups(self) -> t.Dict[str, str]:
        """Quant groups based on device type and selected mode."""
        common = self.json_settings["common"]["groups"]
        if self.dev_settings:
            dev = self.dev_settings.get("groups", {})
            common.update(dev)
            return common
        return common
