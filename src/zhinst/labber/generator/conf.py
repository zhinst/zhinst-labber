from copy import deepcopy
import typing as t


class LabberConfiguration:
    def __init__(self, name: str, mode: str, settings: dict):
        self._name = name.upper()
        self._mode = mode.lower()
        self.json_settings = settings
        self._set_name = list(filter(self._matching_name, list(self.json_settings.keys())))
        if self._set_name:
            self._set_name = self._set_name[0]
            self.dev_settings = self.json_settings[self._set_name]
        else:
            self._set_name = self._name
            self.dev_settings = {}

    def _matching_name(self, s: str) -> bool:
        """Check if match with name is found."""
        import re
        if re.match(f"{s.lower()}(\d+)?$", self._name.lower()):
            return True
        return False

    @property
    def ignored_nodes(self) -> t.List[str]:
        """Ignored nodes."""
        common_norm = self.json_settings['common']['ignoredNodes']['normal']
        common_adv = self.json_settings['common']['ignoredNodes']['advanced']
        if self.dev_settings:
            dev_norm = self.dev_settings['ignoredNodes'].get('normal', [])
            dev_adv = self.dev_settings['ignoredNodes'].get('advanced', [])
            if self._mode == 'normal':
                return common_norm + common_adv + dev_adv + dev_norm
            else:
                return dev_adv + common_adv
        if self._mode == 'normal':
            return common_norm + common_adv
        return common_adv

    @property
    def quants(self) -> dict:
        """Replaced nodes."""
        b = deepcopy(self.json_settings['common']['quants'])
        if self.dev_settings:
            b.update(self.dev_settings.get('quants', {}))
        for k, v in deepcopy(b).items():
            if "mapping" in v.keys():
                map_ = v['mapping'].get(self._set_name, {})
                if not map_:
                    b.pop(k)
                    continue
                b.pop(k)
                b[map_['path']] = {
                    'indexes': map_['indexes'],
                    'conf': v['conf'],
                    'add': v['add']
                }
            elif 'dev_type' in v.keys():
                if not self._name in v['dev_type']:
                    b.pop(k)
        return b

    @property
    def quant_sections(self) -> dict:
        common = self.json_settings['common']['sections']
        if self.dev_settings:
            dev = self.dev_settings['sections']
            common.update(dev)
            return common
        return common

    @property
    def quant_groups(self) -> dict:
        common = self.json_settings['common']['groups']
        if self.dev_settings:
            dev = self.dev_settings['groups']
            common.update(dev)
            return common
        return common
