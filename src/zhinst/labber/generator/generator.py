from collections import OrderedDict
import configparser
from copy import deepcopy
from functools import cached_property
import re
import typing as t
from pathlib import Path
import json
import fnmatch
import natsort

from zhinst.toolkit import Session
from .node_section import NodeSection
from zhinst.toolkit.nodetree import Node
from zhinst.labber.generator.helpers import (
    delete_device_from_node_path,
)
from zhinst.labber.code_generator.drivers import generate_labber_device_driver_code
from .conf import (
    LabberConfiguration
)


class QuantPath:
    def __init__(self, quant: str):
        self._quant = quant
        self._quant_no_slash = self._remove_slashes(quant)

    def _remove_slashes(self, s: str) -> str:
        if s.startswith('/'):
            s = "".join(list(s)[1:])
        if s[-1] == '/':
            s = "".join(list(s)[:-1])
        return s

    @property
    def title(self) -> str:
        return self._quant_no_slash

    @property
    def label(self) -> str:
        if len(self._quant) == 1:
            return self._quant
        s = self._quant_no_slash.split('/')
        if s[-1].isnumeric():
            return "/".join(s[-2:])
        return s[-1]

    @property
    def group(self) -> str:
        s = self._quant_no_slash.split('/')
        if len(s) == 1:
            return "SYSTEM"
        if s[-1].isnumeric():
            return "/".join(s[:-2])
        return "/".join(s[:-1]) + "/"

    @property
    def set_cmd(self) -> str:
        return self.title

    @property
    def get_cmd(self) -> str:
        return self.title

    @property
    def section(self) -> str:
        dig = re.search(r"\d", self._quant_no_slash)
        if dig is not None:
            dig = int(dig.group(0))
            return "".join(list(self._quant_no_slash)[:self._quant_no_slash.find(str(dig))+1])
        else:
            return self.title.split('/')[0]

class LabberConfig:
    """Base class for generating Labber configuration."""
    def __init__(self, root: Node, session: Session, env_settings: dict, mode="NORMAL"):
        self.root = root
        self.session = session
        self._mode = mode
        self._env_settings = env_settings
        self._base_dir = "Zurich_Instruments_"
        self._name = ""
        self._settings_path = "settings.json"
        self._general_settings = {}
        self._settings = {}
        self._tk_name = ""

    def _natural_sort(self, config: dict) -> dict:
        """Natural sort for dictionary keys."""
        sorted_keys = natsort.natsorted(list(config.keys()))
        return OrderedDict({k: config[k] for k in sorted_keys}.items())

    def _match_key(
        self, 
        target: str, 
        data: dict
        ) -> t.Optional[t.Tuple[str, dict]]:
        """Find matches for target in data."""
        if isinstance(data, dict):
            for k, v in data.items():
                k_ = k
                if not k.startswith('/'):
                    k_ = '/' + k
                if not target.startswith('/'):
                    target = '/' + target
                r = fnmatch.filter([target.lower()], f"{k_.lower()}*")
                if r:
                    return k, v
            return None, None
        if isinstance(data, list):
            for item in data:
                r = fnmatch.filter([target.lower()], f"{item.lower()}*")
                if r:
                    return item
            return None
        return None, None

    def _update_sections(self, quants: dict) -> dict:
        """Update sections."""
        for k in quants.copy().keys():
            _, sec = self._match_key(k, self.env_settings.quant_sections)
            if sec:
                quants[k]['section'] = sec
        return quants

    def _update_groups(self, quants: dict) -> dict:
        """Update groups"""
        for k in quants.copy().keys():
            _, sec = self._match_key(k, self.env_settings.quant_groups)
            if sec:
                quants[k]['group'] = sec
        return quants

    def _find_nth_occurence(self, s: str, target: str, idx: int) -> int:
        """Find nth occurence of the target in a string"""
        return s.find(target, s.find(target) + idx)

    def _matching_name(self, s: str) -> bool:
        """Check if value matches name"""
        if re.match(f"{s}(\d+)?$", self._name):
            return True
        return False

    def _generate_quants_from_indexes(self, quant: str, index: int, indexes: t.List[int]) -> list:
        """Quants based on their indexes."""
        qts = []
        if not indexes:
            indexes = ["dev" for _ in range(quant.count("*"))]
            if not indexes:
                return [quant]
        def find_indexes(quant, i, idxs):
            for x in range(idxs[i]):
                s = list(quant)
                idx = self._find_nth_occurence("".join(s), '*', i)
                s[idx] = str(x)
                try:
                    find_indexes(s, i+1, idxs)
                except IndexError:
                    qts.append("".join(s))
        find_indexes(quant, index, indexes)
        return qts

    def _quant_indexes(self, quant: str, indexes: t.List[str]) -> t.List[int]:
        """Find all quant indexes."""
        idxs = []
        if not indexes:
            indexes = ["dev" for _ in range(quant.count("*"))]
            if not indexes:
                return []

        for enumm, idx in enumerate(indexes):
            bar = self._find_nth_occurence(quant, '*', enumm)
            if idx ==  'dev':
                stop = list(quant)[:bar]
                stop = ''.join(stop).replace('//', '/')
                if stop[-1] == '/':
                    stop = stop[:-1]
                if not stop.startswith('/'):
                    stop = '/' + stop
                idxs.append(len(self.root[stop]))
            else:
                idxs.append(idx)
        return idxs

    def _generate_quants(self) -> t.Dict[str, dict]:
        """Generate Labber quants."""
        nodes = {}
        # Existing nodes to quants
        for _, info in self.root:
            if self._match_key(
                delete_device_from_node_path(info["Node"]),
                self.env_settings.ignored_nodes
                ):
                continue
            sec = NodeSection(info)

            sec_dict = sec.as_dict(flat=True)
            filtr_path = sec.filtered_node_path
            nodes[filtr_path.lower()] = sec_dict
        # Added nodes from configuration if the node exists but is not available
        missing = deepcopy(self.env_settings.quants)
        for k, v in nodes.copy().items():
            kk, vv = self._match_key(k, self.env_settings.quants)
            if kk:
                for _, conf in vv['conf'].items():
                    if not conf:
                        nodes[k].pop(v, None)
                v.update(vv['conf'])
                nodes[k] = v
                # If the quant is extended
                if vv.get('extend', None):
                    idxs = self._quant_indexes(kk, v.get('indexes', []))
                    paths = self._generate_quants_from_indexes(kk, 0, idxs)
                    for p in paths:
                        d = {}
                        s = QuantPath(p)
                        suffix = vv["extend"].get('suffix', '')
                        vv.pop('suffix', None)
                        d['label'] = s.title + "/" + suffix
                        d['group'] = s.group
                        d['section'] = s.section
                        d['set_cmd'] = s.set_cmd
                        d['get_cmd'] = s.get_cmd
                        d['permission'] = 'WRITE'
                        d.update(vv["extend"])
                        nodes[s.title + "/" + suffix] = d
                missing.pop(kk, None)

        # Manually added quants from configuration
        for k, v in missing.items():
            if v.get('add', False):
                idxs = self._quant_indexes(k, v.get('indexes', []))
                paths = self._generate_quants_from_indexes(k, 0, idxs)
                for p in paths:
                    d = {}
                    s = QuantPath(p)
                    d['label'] = s.title
                    d['group'] = s.group
                    d['section'] = s.section
                    d['set_cmd'] = s.set_cmd
                    d['get_cmd'] = s.get_cmd
                    d['permission'] = 'WRITE'
                    d.update(v["conf"])
                    nodes[s.title] = d
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

    @cached_property
    def env_settings(self) -> LabberConfiguration:
        """Labber environment settings."""
        return LabberConfiguration(self._tk_name, self._mode, self._env_settings)

    @property
    def settings_path(self) -> str:
        """Settings filepath."""
        return self._settings_path

    @property
    def name(self) -> str:
        """Config name"""
        return self._base_dir + self._name

    @property
    def general_settings(self) -> dict:
        """General settings"""
        return self._general_settings

    @property
    def settings(self) -> dict:
        """Config settings."""
        return self._settings


class DeviceConfig(LabberConfig):
    def __init__(self, device: Node, session: Session, env_settings: dict, mode: str):
        super().__init__(device, session, env_settings, mode)
        self.device = device
        self._name = self.device.device_type.upper()
        self._tk_name = self.device.device_type.upper()
        self._settings = {
            "data_server": {
                "host": self.session.server_host,
                "port": self.session.server_port,
                "hf2": self.session.is_hf2_server,
                "shared_session": True,
            },
            "instrument": {"base_type": "device", "type": self._name},
        }
        self._general_settings = {
            "General settings": {
                "name": f"Zurich Instruments {self._name}",
                "version": "0.1",
                "driver_path": f"Zurich_Instruments_{self._name}",
                "interface": "Other",
                "startup": f"Do nothing",
            }
        }


class DataServerConfig(LabberConfig):
    def __init__(self, session: Session, env_settings: dict, mode: str):
        super().__init__(session, session, env_settings, mode)
        self._tk_name = "DataServer"
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
        self._general_settings = {
            "General settings": {
                "name": f"Zurich Instruments {self._name}",
                "version": "0.1",
                "driver_path": f"Zurich_Instruments_{self._name}",
                "interface": "Other",
                "startup": f"Do nothing",
            }
        }


class ModuleConfig(LabberConfig):
    def __init__(self, name: str, session: Session, env_settings: dict, mode: str):
        self.module = getattr(session.modules, name)
        super().__init__(self.module, session, env_settings, mode)
        self._tk_name = name
        if 'MODULE' not in name.upper():
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
            "instrument": {"base_type": "module", "type": self._tk_name},
        }
        self._general_settings = {
            "General settings": {
                "name": f"Zurich Instruments {self._name}",
                "version": "0.1",
                "driver_path": f"Zurich_Instruments_{self._name}",
                "interface": "Other",
                "startup": f"Do nothing",
            }
        }


def _path_to_labber_section(path: str, delim: str) -> str:
    """Path to Labber format. Delete slashes from start and end."""
    path = list(path)
    if path[0] == '/':
        path = path[1:]
    if path[-1] == '/':
        path = path[0:-1]
    p = "".join(path)
    return p.replace('/', delim)


def dict_to_config(config: configparser.ConfigParser, data: dict, delim: str) -> None:
    """Turn Python dictionary into ConfigParser.
    
    Also sorts the keys naturally and titles them."""
    sorted_keys = natsort.natsorted(list(data.keys()))
    data = OrderedDict({k: data[k] for k in sorted_keys}.items())
    for title, items in data.items():
        if not title == "General settings":
            title = title.title()
        title_ = _path_to_labber_section(title, delim)
        config.add_section(title_)
        for name, value in items.items():
            if name not in ['set_cmd', 'get_cmd', 'tooltip', 'datatype']:
                name = _path_to_labber_section(name, delim)
                value = _path_to_labber_section(value, delim)
            if name.lower() in ["label", "group", "section"]:
                config.set(title_, name.title(), value.title())
            else:
                config.set(title_, name, value)


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

    root_path = Path(filepath)
    root_path.mkdir(exist_ok=True)

    # Settings file
    settings_file = Path(__file__).parent.parent / "settings.json"
    with open(settings_file, 'r') as json_f:
        json_settings = json.load(json_f)
    labber_delim = json_settings['misc']['labberDelimiter']

    def write_to_json(path: Path, data, upgrade):
        if upgrade:
            with open(path, "w") as json_file:
                json.dump(data, json_file)
        else:
            if not path.exists():
                with open(path, "w") as json_file:
                    json.dump(data, json_file)

    def write_to_file(path: Path, data, upgrade):
        if upgrade:
            with open(path, "w") as f:
                f.write(data)
        else:
            if not path.exists():
                with open(path, "w") as f:
                    f.write(data)

    def write_to_config(path: Path, config, upgrade):
        if upgrade:
            with open(path, "w", encoding="utf-8") as config_file:
                config.write(config_file)
        else:
            if not path.exists():
                with open(path, "w", encoding="utf-8") as config_file:
                    config.write(config_file)

    # Dataserver
    obj = DataServerConfig(session, json_settings, mode)
    dev_dir = root_path / obj.name
    dev_dir.mkdir(exist_ok=True)

    config = configparser.ConfigParser()
    dict_to_config(config, obj.config(), delim=labber_delim)
    path = dev_dir / f"{obj.name}.ini"
    write_to_config(path, config, upgrade)
    s_path = dev_dir / obj.settings_path
    write_to_json(s_path, obj.settings, upgrade)
    c_path = dev_dir / f"{obj.name}.py"
    write_to_file(c_path, obj.generated_code(), upgrade)

    # Device
    obj = DeviceConfig(dev, session, json_settings, mode)
    dev_dir = root_path / obj.name
    dev_dir.mkdir(exist_ok=True)

    config = configparser.ConfigParser()
    dict_to_config(config, obj.config(), delim=labber_delim)
    path = dev_dir / f"{obj.name}.ini"
    write_to_config(path, config, upgrade)
    s_path = dev_dir / obj.settings_path
    write_to_json(s_path, obj.settings, upgrade)
    c_path = dev_dir / f"{obj.name}.py"
    write_to_file(c_path, obj.generated_code(), upgrade)

    # Modules
    modules: t.List[str] = json_settings['misc']['ziModules']

    for module in modules:
        obj = ModuleConfig(module, session, json_settings, mode)
        dev_dir = root_path / obj.name
        dev_dir.mkdir(exist_ok=True)
        config = configparser.ConfigParser()
        dict_to_config(config, obj.config(), delim=labber_delim)
        path = dev_dir / f"{obj.name}.ini"
        write_to_config(path, config, upgrade)
        s_path = dev_dir / obj.settings_path
        write_to_json(s_path, obj.settings, upgrade)
        c_path = dev_dir / f"{obj.name}.py"
        write_to_file(c_path, obj.generated_code(), upgrade)
