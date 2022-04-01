import string
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
        self._dev_base = name.rstrip(string.digits)
        self._dev_names = self._combine_devices(self._dev_base)
        self.dev_settings = self.json_settings.get(self._dev_base, {})
        self._quants = self._find_quants()

    def _combine_devices(self, name: str) -> t.List[str]:
        """Combine device quants in case the device is a combination
        if multiple devices."""
        if "SHFQC" in name:
            return ["SHFQC", "SHFQA", "SHFSG"]
        return [name]

    def _find_quants(self) -> t.Dict:
        """Find quants based on device type and selected mode.

        Returns:
            Dictionary of all matching quant objects.
        """
        quants = self.json_settings["common"].get("quants", {}).copy()

        for dev_name in self._dev_names:
            quants.update(self.json_settings.get(dev_name, {}).get("quants", {}))

        for quant, defs in quants.copy().items():
            if not defs.get("conf", {}) or defs.get("add", None) is None:
                quants.pop(quant)
                continue
            if defs["conf"].get("tooltip", None):
                quants[quant]["conf"]["tooltip"] = tooltip(defs["conf"]["tooltip"])
            if "mapping" in defs.keys():
                for dev_name in self._dev_names:
                    map_ = defs["mapping"].get(dev_name, {})
                    quants.pop(quant, None)
                    if not map_:
                        continue
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
    def quant_order(self) -> t.Dict:
        """Quant order"""
        common = self.json_settings["common"].get("quantOrder", {}).copy()
        common.update(self.dev_settings.get("quantOrder", {}))
        return common

    @property
    def base_name(self) -> str:
        """Base name of the device."""
        return self._dev_base

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
        ignored_nodes = []
        ignored_common = self.json_settings["common"].get("ignoredNodes", {})
        common_norm = ignored_common.get("normal", [])
        common_adv = ignored_common.get("advanced", [])
        if self._mode == "normal":
            ignored_nodes += common_norm + common_adv
        else:
            ignored_nodes += common_adv
        for dev in self._dev_names:
            dev_settings = self.json_settings.get(dev, {})
            ignored_dev = dev_settings.get("ignoredNodes", {})
            dev_norm = ignored_dev.get("normal", [])
            dev_adv = ignored_dev.get("advanced", [])
            if self._mode == "normal":
                ignored_nodes += dev_adv + dev_norm
            else:
                ignored_nodes += dev_adv
        return ignored_nodes

    @property
    def quants(self) -> t.Dict:
        """Quants based on device type and selected mode."""
        return self._quants

    @property
    def quant_sections(self) -> t.Dict[str, str]:
        """Quant sections based on device type and selected mode."""
        common = self.json_settings["common"]["sections"]
        for dev in self._dev_names:
            dev_settings = self.json_settings.get(dev, {})
            dev = dev_settings.get("sections", {})
            common.update(dev)
        return common

    @property
    def quant_groups(self) -> t.Dict[str, str]:
        """Quant groups based on device type and selected mode."""
        common = self.json_settings["common"]["groups"]
        for dev in self._dev_names:
            dev_settings = self.json_settings.get(dev, {})
            dev = dev_settings.get("groups", {})
            common.update(dev)
        return common
