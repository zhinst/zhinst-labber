import configparser
import json
import typing as t
from collections import OrderedDict
from pathlib import Path
import fnmatch

import natsort
from zhinst.toolkit import Session
from zhinst.toolkit.nodetree import Node

from zhinst.labber import __version__
from zhinst.labber.code_generator.drivers import generate_labber_device_driver_code
from zhinst.labber.generator.conf import LabberConfiguration
from zhinst.labber.generator.helpers import (
    delete_device_from_node_path,
    match_in_dict_keys,
    match_in_list,
)
from zhinst.labber.generator.quants import NodeQuant, Quant, QuantGenerator


class LabberConfig:
    """Base class for generating Labber configuration.

    The class generates necessary Labber driver data
    It also converts available nodes into Labber driver configuration and
    modifies them based on given settings file.

    Args:
        root: Zurich Instruments toolkit root node
        name: Name of the root object
        env_settings: Existing Labber settings
        mode: Labber mode. `NORMAL` | `ADVANCED`
    """

    def __init__(self, root: Node, name: str, env_settings: dict, mode="NORMAL"):
        self._root = root
        self._env_settings = LabberConfiguration(name, mode, env_settings)
        self._quant_gen = QuantGenerator(list(root._root.raw_dict.keys()))
        self._tk_name = name
        self._name = name
        self._general_settings = {}
        self._settings = {}

    def _update_section(self, quant: str, defs: t.Dict) -> t.Dict:
        """Update quant section.

        Returns:
            Defs with updated section from `env_settings`."""
        _, section = match_in_dict_keys(quant, self.env_settings.quant_sections)
        if section:
            defs["section"] = section
        return defs

    def _update_group(self, quant: str, defs: t.Dict) -> t.Dict:
        """Update quant group.

        if a match is found, `<n>` updated with corresponding
        quant index.

            Example:

                quant: "sines/0"
                group def: "/sines/<n>/*": "Sines <n>"
                group = Sines 0

        Returns:
            Defs with updated group key from `env_settings`.
        """
        indexes = [part for part in quant.split("/") if part.isnumeric()]
        for pattern, group in self.env_settings.quant_groups.copy().items():
            pattern = pattern.replace("<n>", "*")
            r = fnmatch.fnmatch(
                quant.strip("/").lower(), f"{pattern.strip('/').lower()}*"
            )
            if r:
                cnt = group.count("<n>")
                path = group.replace("<n>", "{}")
                defs["group"] = path.format(*[indexes[idx] for idx in range(cnt)])
                break
        return defs

    def _generate_node_quants(self) -> t.Dict:
        """Generate node quants from available nodes.

        Returns:
            Dictionary of available nodes in Labber format.
        """
        quants = {}
        for info in self._root._root.raw_dict.values():
            if match_in_list(
                delete_device_from_node_path(info["Node"]),
                self.env_settings.ignored_nodes,
            ):
                continue
            sec = NodeQuant(info)
            quants.update(sec.as_dict())
        return quants

    def _generate_quants(self) -> t.Dict[str, dict]:
        """Generate Labber quants from available nodes and settings file.

        Returns:
            Generated Labber quants which consists of existing and added nodes from
            `env_settings`
        """
        nodes = self._generate_node_quants()
        # Added nodes from configuration if the node exists but is not available
        custom_quants = self.env_settings.quants.copy()
        for node_quant, node_defs in nodes.copy().items():
            settings_quant, settings_defs = match_in_dict_keys(
                node_quant, self.env_settings.quants
            )
            if settings_quant:
                [
                    nodes[node_quant].pop(node_defs, None)
                    for conf in settings_defs["conf"].values()
                    if not conf
                ]
                node_defs.update(settings_defs["conf"])
                nodes[node_quant] = node_defs
                # If the quant is extended
                if settings_defs.get("extend", None):
                    for path in self._quant_gen.quant_paths(
                        settings_quant, node_defs.get("indexes", [])
                    ):
                        conf = settings_defs["extend"]
                        conf = self._update_group(path, conf)
                        conf = self._update_section(path, conf)
                        nodes.update(Quant(path, conf).as_dict())
                custom_quants.pop(settings_quant, None)
            nodes[node_quant] = self._update_group(node_quant, node_defs)
            nodes[node_quant] = self._update_section(node_quant, node_defs)

        # Manually added quants from configuration
        for custom_quant, custom_defs in custom_quants.items():
            if custom_defs.get("add", False):
                for path in self._quant_gen.quant_paths(
                    custom_quant, custom_defs.get("indexes", [])
                ):
                    conf = custom_defs["conf"]
                    conf = self._update_group(path, conf)
                    conf = self._update_section(path, conf)
                    nodes.update(Quant(path, self._update_group(path, conf)).as_dict())
        return nodes

    def generated_code(self) -> str:
        """Generated labber code

        Returns:
            Labber driver code for the current object.
        """
        return generate_labber_device_driver_code(self._name, self.settings_filename)

    def config(self) -> t.Dict[str, t.Dict]:
        """Labber configuration as a Python dictionary.

        Returns:
            Generated Labber quants which consists of existing and added nodes from
            `env_settings` and general settings."""
        general = self.general_settings
        nodes = self._generate_quants()
        general.update(nodes)
        return general

    @property
    def env_settings(self) -> LabberConfiguration:
        """Labber environment settings."""
        return self._env_settings

    @property
    def settings_filename(self) -> str:
        """Settings filename."""
        return "settings.json"

    @property
    def name(self) -> str:
        """Name of the config driver."""
        return "Zurich_Instruments_" + self._name

    @property
    def general_settings(self) -> t.Dict:
        """General settings section for Labber."""
        self._general_settings.update(self.env_settings.general_settings)
        return {"General settings": self._general_settings}

    @property
    def settings(self) -> t.Dict:
        """Driver settings."""
        return self._settings


class DeviceConfig(LabberConfig):
    """Class for generating Labber configuration for Zurich Instruments
    devices.

    The class generates necessary Labber driver data
    It also converts available nodes into Labber driver configuration and
    modifies them based on given settings file.

    Args:
        device: Zurich Instruments toolkit device node.
        session: Existing DataServer session
        env_settings: Existing Labber settings
        mode: Labber mode. `NORMAL` | `ADVANCED`
    """

    def __init__(self, device: Node, session: Session, env_settings: dict, mode: str):
        self._tk_name = device.device_type.upper()
        super().__init__(device, self._tk_name, env_settings, mode)
        options = str(device.features.options()).replace("\n", "_")
        self._name = f"{self._tk_name}_{options}" if options else self._tk_name
        self.session = session
        self.device = device
        self._settings = {
            "data_server": {
                "host": self.session.server_host,
                "port": self.session.server_port,
                "hf2": self.session.is_hf2_server,
                "shared_session": True,
            },
            "instrument": {"base_type": "device", "type": self._name},
        }
        version = f"{session.about.version()}#{__version__}#{self.env_settings.version}"
        self._general_settings = {
            "name": f"Zurich Instruments {self._name}",
            "version": version,
            "driver_path": f"Zurich_Instruments_{self._name}",
        }


class DataServerConfig(LabberConfig):
    """Class for generating Labber configuration for Zurich Instruments
    DataServer.

    The class generates necessary Labber driver data
    It also converts available nodes into Labber driver configuration and
    modifies them based on given settings file.

    Args:
        session: Existing DataServer session
        env_settings: Existing Labber settings
        mode: Labber mode. `NORMAL` | `ADVANCED`
    """

    def __init__(self, session: Session, env_settings: dict, mode: str):
        self._tk_name = "DataServer"
        super().__init__(session, self._tk_name, env_settings, mode)
        self.session = session
        self._name = "DataServer"
        self._settings = {
            "data_server": {
                "host": self.session.server_host,
                "port": self.session.server_port,
                "hf2": self.session.is_hf2_server,
                "shared_session": True,
            },
            "instrument": {
                "base_type": "DataServer",
            },
        }
        version = f"{session.about.version()}#{__version__}#{self.env_settings.version}"
        self._general_settings = {
            "name": f"Zurich Instruments {self._name}",
            "version": version,
            "driver_path": f"Zurich_Instruments_{self._name}",
        }


class ModuleConfig(LabberConfig):
    """Class for generating Labber configuration for Zurich Instruments
    modules.

    The class generates necessary Labber driver data
    It also converts available nodes into Labber driver configuration and
    modifies them based on given settings file.

    Args:
        name: Name of the toolkit module
        session: Existing DataServer session
        env_settings: Existing Labber settings
        mode: Labber mode. `NORMAL` | `ADVANCED`
    """

    def __init__(self, name: str, session: Session, env_settings: dict, mode: str):
        self.module = getattr(session.modules, name)
        self._tk_name = name
        super().__init__(self.module, self._tk_name, env_settings, mode)
        self.session = session
        self._name = name.upper() + "_Module"
        self._settings = {
            "data_server": {
                "host": self.session.server_host,
                "port": self.session.server_port,
                "hf2": self.session.is_hf2_server,
                "shared_session": True,
            },
            "instrument": {"base_type": "module", "type": self._tk_name},
        }
        version = f"{session.about.version()}#{__version__}#{self.env_settings.version}"
        self._general_settings = {
            "name": f"Zurich Instruments {self._name}",
            "version": version,
            "driver_path": f"Zurich_Instruments_{self._name}",
        }


def _path_to_labber_section(path: str, delim: str) -> str:
    """Path to Labber format. Delete slashes from start and end.

    Returns:
        Formatted path in Labber format with given delimited."""
    return path.strip("/").replace("/", delim)


def conf_to_labber_format(data: dict, delim: str) -> dict:
    """Transform data into Labber format.

    * Natural sort dictionary keys
    * Replace slashes with delimiter
    * Title sections

    Returns:
        Formatted data
    """

    def _to_title_keep_uppercase(s: str) -> str:
        if s.islower():
            return s.title()
        return s

    sorted_keys = natsort.natsorted(list(data.keys()))
    data = OrderedDict({k: data[k] for k in sorted_keys}.items())

    for title, quant in data.copy().items():
        title_ = str(title)
        if not title == "General settings":
            title_ = _to_title_keep_uppercase(title_)
        title_ = _path_to_labber_section(title_, delim)

        data.pop(title, None)
        data[title_] = {}
        for key, value in quant.items():
            if key not in ["set_cmd", "get_cmd", "tooltip", "datatype"]:
                key = _path_to_labber_section(str(key), delim)
                value = _path_to_labber_section(str(value), delim)
            if key.lower() in ["label", "group", "section"]:
                key = _to_title_keep_uppercase(key)
                value = _to_title_keep_uppercase(value)
            data[title_].update({key: value})
    return data


def dict_to_config(config: configparser.ConfigParser, data: dict, delim: str) -> None:
    """Update config with give data.

    The data will be formatted and then set as config sections.
    """
    data = conf_to_labber_format(data, delim)
    for title, items in data.items():
        config.add_section(title)
        for name, value in items.items():
            config.set(title, name, value)


class Filehandler:
    """FileHandler class for generating Labber configuration files.

    Args:
        config: Labber configuration class
        root_dir: Root directory where the files are generated
        upgrade: If the existing files should be overwritten
    """

    def __init__(self, config: LabberConfig, root_dir: str, upgrade=False):
        self._config = config
        self._root_dir = Path(root_dir) / config.name
        self._root_dir.mkdir(exist_ok=True)
        self._upgrade = upgrade
        self._created_files = []
        self._upgraded_files = []

    def write_to_file(self, path: Path, filehandler: t.Callable) -> None:
        """Write to file.

        Args:
            path: Filepath
            filehandler: Handler to be called for saving the file
        """
        if self._upgrade:
            if not path.exists():
                self._created_files.append(path)
            else:
                self._upgraded_files.append(path)
            with open(path, "w", encoding="utf-8") as file:
                filehandler(file)
        else:
            if not path.exists():
                with open(path, "w", encoding="utf-8") as file:
                    filehandler(file)
                self._created_files.append(path)

    def write_settings_file(self) -> None:
        """Write settings file (.*json-format)."""
        path = self._root_dir / self._config.settings_filename
        self.write_to_file(path, lambda x: json.dump(self._config.settings, x))

    def write_config_file(self, delim: str) -> None:
        """Write configuration file (*.ini-format)."""
        path = self._root_dir / f"{self._config.name}.ini"
        config = configparser.ConfigParser()
        dict_to_config(config, self._config.config(), delim=delim)
        self.write_to_file(path, lambda x: config.write(x))

    def write_python_driver(self) -> None:
        """Write Python driver file (*.py-format)."""
        path = self._root_dir / f"{self._config.name}.py"
        self.write_to_file(path, lambda x: x.write(self._config.generated_code()))

    @property
    def upgraded_files(self) -> t.List[Path]:
        """List of upgraded files."""
        return self._upgraded_files

    @property
    def created_files(self) -> t.List[Path]:
        """List of created files."""
        return self._created_files


def open_settings_file() -> dict:
    """Open settings file.

    Returns:
        Contents of the opened settings file.
    """
    settings_file = Path(__file__).parent.parent / "resources/settings.json"
    with open(settings_file, "r") as json_f:
        return json.load(json_f)


def generate_labber_files(
    driver_directory: str,
    mode: str,
    device_id: str,
    server_host: str,
    upgrade: bool = False,
    server_port: t.Optional[int] = None,
    hf2: t.Optional[bool] = None,
):
    """Generate Labber files for the selected device.

    Args:
        driver_directory: Base directory for generated driver files.
        mode: Driver mode. `NORMAL` | `ADVANCED`.
            Normal has select amount of functionality available.
            Advanced has most of the nodes available.
        device_id: Zurich Instruments device ID. (e.g: dev1234)
        server_host: DataServer host
        upgrade: Overwrite existing drivers
        server_port: DataServer port
        hf2: If the device is HF2.
    """
    session = Session(server_host=server_host, server_port=server_port, hf2=hf2)
    dev = session.connect_device(device_id)

    # Files generated to echo
    generated_files = []
    upgraded_files = []
    # Settings file
    json_settings = open_settings_file()

    configs = [
        DataServerConfig(session, json_settings, mode),
        DeviceConfig(dev, session, json_settings, mode),
    ]
    # Modules
    # TODO: When hf2 option enabled:
    # RuntimeError: Unsupported API level for specified server
    if not hf2:
        modules: t.List[str] = json_settings["misc"]["ziModules"].copy()
        if "SHFQA" not in dev.device_type:
            modules.remove("shfqa_sweeper")
        configs += [ModuleConfig(mod, session, json_settings, mode) for mod in modules]
    for config in configs:
        filegen = Filehandler(config, root_dir=driver_directory, upgrade=upgrade)
        filegen.write_config_file(delim=json_settings["misc"]["labberDelimiter"])
        filegen.write_python_driver()
        filegen.write_settings_file()
        generated_files += filegen.created_files
        upgraded_files += filegen.upgraded_files
    return generated_files, upgraded_files
