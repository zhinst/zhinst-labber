from collections import OrderedDict
import configparser
import typing as t
from pathlib import Path
import json
import natsort

from zhinst.toolkit import Session
from zhinst.toolkit.nodetree import Node
from zhinst.labber.generator.quants import NodeQuant, Quant, QuantGenerator
from zhinst.labber.generator.helpers import (
    delete_device_from_node_path,
    remove_leading_trailing_slashes,
    match_in_dict_keys,
    match_in_list,
)
from zhinst.labber.code_generator.drivers import generate_labber_device_driver_code
from zhinst.labber.generator.conf import LabberConfiguration
from zhinst.labber import __version__

class LabberConfig:
    """Base class for generating Labber configuration."""
    def __init__(self, root: Node, name: str, env_settings: dict, mode="NORMAL"):
        self.root = root
        self._mode = mode
        self._env_settings_json = env_settings
        self._env_settings = LabberConfiguration(name, mode, env_settings)
        self._quant_gen = QuantGenerator(self._node_list())
        self._tk_name = name
        self._name = name
        self._general_settings = {}
        self._settings = {}

    def _node_list(self) -> t.List[str]:
        nodes = {k: v for k,v in self.root}
        return [x["Node"] for x in nodes.values()]

    def _update_sections(self, quants: dict) -> dict:
        """Update quant sections."""
        for k in quants.copy().keys():
            _, sec = match_in_dict_keys(k, self.env_settings.quant_sections)
            if sec:
                quants[k]["section"] = sec
        return quants

    def _update_groups(self, quants: dict) -> dict:
        """Update quant groups"""
        for quant in quants.copy().keys():
            replc = [part for part in quant.split("/") if part.isnumeric()]
            quant_wc = {}
            for pattern, grp in self.env_settings.quant_groups.copy().items():
                pattern = pattern.replace('<n>', '*')
                quant_wc[pattern] = grp
            _, path = match_in_dict_keys(quant, quant_wc)
            if path:
                cnt = path.count("<n>")
                path = path.replace("<n>", "{}")
                repl = [replc[idx] for idx in range(cnt)]
                path = path.format(*repl)
                quants[quant]["group"] = path
        return quants

    def _generate_node_quants(self):
        quants = {}
        for _, info in self.root:
            if match_in_list(
                delete_device_from_node_path(info["Node"]),
                self.env_settings.ignored_nodes,
            ):
                continue
            sec = NodeQuant(info)
            quants.update(sec.as_dict(flat=False))
        return quants

    def _generate_quants(self) -> t.Dict[str, dict]:
        """Generate Labber quants."""
        nodes = self._generate_node_quants()
        # Added nodes from configuration if the node exists but is not available
        missing = self.env_settings.quants.copy()
        for k, v in nodes.copy().items():
            kk, vv = match_in_dict_keys(k, self.env_settings.quants)
            if kk:
                for _, conf in vv["conf"].items():
                    if not conf:
                        # Delete key if it is set to None
                        nodes[k].pop(v, None)
                v.update(vv["conf"])
                nodes[k] = v
                # If the quant is extended
                if vv.get("extend", None):
                    for p in self._quant_gen.quant_paths(kk, v.get("indexes", [])):
                        s = Quant(p, vv["extend"])
                        nodes.update(s.as_dict())
                missing.pop(kk, None)

        # Manually added quants from configuration
        for k, v in missing.items():
            if v.get("add", False):
                for p in self._quant_gen.quant_paths(k, v.get("indexes", [])):
                    s = Quant(p, v["conf"])
                    nodes.update(s.as_dict())
        return nodes

    def generated_code(self) -> str:
        """Generated labber code"""
        return generate_labber_device_driver_code(self._name, self.settings_path)

    def config(self) -> t.Dict[str, dict]:
        """Labber configuration as a Python dictionary."""
        general = self.general_settings
        nodes = self._generate_quants()
        nodes = self._update_groups(nodes)
        nodes = self._update_sections(nodes)
        general.update(nodes)
        return general

    @property
    def env_settings(self) -> LabberConfiguration:
        """Labber environment settings."""
        return self._env_settings

    @property
    def settings_path(self) -> str:
        """Settings filepath."""
        return "settings.json"

    @property
    def name(self) -> str:
        """Config name"""
        return "Zurich_Instruments_" + self._name

    @property
    def general_settings(self) -> dict:
        """General settings"""
        self._general_settings.update(self.env_settings.general_settings)
        return {"General settings": self._general_settings}

    @property
    def settings(self) -> dict:
        """Config settings."""
        return self._settings


class DeviceConfig(LabberConfig):
    def __init__(self, device: Node, session: Session, env_settings: dict, mode: str):
        self._tk_name = device.device_type.upper()
        super().__init__(device, self._tk_name, env_settings, mode)
        options = str(device.features.options()).replace('\n', '_')
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
            "version":version,
            "driver_path": f"Zurich_Instruments_{self._name}",
        }


class ModuleConfig(LabberConfig):
    def __init__(self, name: str, session: Session, env_settings: dict, mode: str):
        self.module = getattr(session.modules, name)
        self._tk_name = name
        super().__init__(self.module, self._tk_name, env_settings, mode)
        self.session = session
        if "MODULE" not in name.upper():
            self._name = name.upper() + "_Module"
        else:
            self._name = name.upper()
        self._settings = {
            "data_server": {
                "host": self.session.server_host,
                "port": self.session.server_port,
                "hf2": self.session.is_hf2_server,
                "shared_session": True,
            },
            "instrument": {"base_type": "module", "type": self._tk_name}
        }
        version = f"{session.about.version()}#{__version__}#{self.env_settings.version}"
        self._general_settings = {
            "name": f"Zurich Instruments {self._name}",
            "version": version,
            "driver_path": f"Zurich_Instruments_{self._name}",
        }


def _path_to_labber_section(path: str, delim: str) -> str:
    """Path to Labber format. Delete slashes from start and end."""
    path = remove_leading_trailing_slashes(path)
    return path.replace("/", delim)


def conf_to_labber_format(data: dict, delim: str) -> dict:
    """Transform data into Labber format.

    * Natural sort dictionary keys
    * Replace slashes with delimiter
    * Title sections
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
    """Turn Python dictionary into ConfigParser."""
    data = conf_to_labber_format(data, delim)
    for title, items in data.items():
        config.add_section(title)
        for name, value in items.items():
            config.set(title, name, value)


class Filehandler:
    def __init__(self, config: LabberConfig, root_dir: str, upgrade=False):
        self._config = config
        self._root_dir = Path(root_dir) / config.name
        self._root_dir.mkdir(exist_ok=True)
        self._upgrade = upgrade
        self._created_files = []
        self._upgraded_files = []

    def write_settings_file(self):
        path = self._root_dir / self._config.settings_path
        if self._upgrade:
            if not path.exists():
                self._created_files.append(path)
            else:
                self._upgraded_files.append(path)
            with open(path, "w") as json_file:
                json.dump(self._config.settings, json_file)
        else:
            if not path.exists():
                with open(path, "w") as json_file:
                    json.dump(self._config.settings, json_file)
                self._created_files.append(path)

    def write_config_file(self, delim: str):
        path = self._root_dir / f"{self._config.name}.ini"
        config = configparser.ConfigParser()
        dict_to_config(config, self._config.config(), delim=delim)
        if self._upgrade:
            if not path.exists():
                self._created_files.append(path)
            else:
                self._upgraded_files.append(path)
            with open(path, "w", encoding="utf-8") as config_file:
                config.write(config_file)
        else:
            if not path.exists():
                with open(path, "w", encoding="utf-8") as config_file:
                    config.write(config_file)
                self._created_files.append(path)

    def write_python_driver(self):
        path = self._root_dir / f"{self._config.name}.py"
        if self._upgrade:
            if not path.exists():
                self._created_files.append(path)
            else:
                self._upgraded_files.append(path)
            with open(path, "w") as f:
                f.write(self._config.generated_code())
        else:
            if not path.exists():
                with open(path, "w") as f:
                    f.write(self._config.generated_code())
                self._created_files.append(path)

    @property
    def upgraded_files(self):
        return self._upgraded_files

    @property
    def created_files(self):
        return self._created_files

def open_settings_file() -> dict:
    settings_file = Path(__file__).parent.parent / "resources/settings.json"
    with open(settings_file, "r") as json_f:
        return json.load(json_f)


def generate_labber_files(
    filepath: str,
    mode: str,
    device: str,
    server_host: str,
    upgrade: bool = False,
    server_port: t.Optional[int] = None,
    hf2: t.Optional[bool] = None,
):
    """Generate Labber files for the selected device."""
    session = Session(server_host=server_host, server_port=server_port, hf2=hf2)
    dev = session.connect_device(device)

    # Files generated to echo
    generated_files = []
    upgraded_files = []
    # Settings file
    json_settings = open_settings_file()
    labber_delim = json_settings["misc"]["labberDelimiter"]

    configs = [
        DataServerConfig(session, json_settings, mode),
        DeviceConfig(dev, session, json_settings, mode)
    ]
    # Modules
    # TODO: When hf2 option enabled:
    # RuntimeError: Unsupported API level for specified server
    if not hf2:
        modules: t.List[str] = json_settings["misc"]["ziModules"].copy()
        if "SHFQA" not in dev.device_type:
            modules.remove('shfqa_sweeper')
        configs += [ModuleConfig(mod, session, json_settings, mode) for mod in modules]
    for config in configs:
        filegen = Filehandler(config, root_dir=filepath, upgrade=upgrade)
        filegen.write_config_file(delim=labber_delim)
        filegen.write_python_driver()
        filegen.write_settings_file()
        generated_files += filegen.created_files
        upgraded_files += filegen.upgraded_files
    return generated_files, upgraded_files
