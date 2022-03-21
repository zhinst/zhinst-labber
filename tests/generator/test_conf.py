import pytest

from zhinst.labber.generator.conf import LabberConfiguration


@pytest.fixture
def tk_confs_norm(settings_json):
    objs = ["SHFQA4", "HDAWG8"]
    return [LabberConfiguration(obj, "normal", settings_json) for obj in objs]


@pytest.fixture
def tk_confs_adv(settings_json):
    objs = ["SHFQA4", "HDAWG8"]
    return [LabberConfiguration(obj, "advanced", settings_json) for obj in objs]


def test_ignored_nodes_normal(tk_confs_norm, settings_json):
    for conf in tk_confs_norm:
        ign_com_norm = settings_json["common"]["ignoredNodes"]["normal"]
        ign_com_adv = settings_json["common"]["ignoredNodes"]["advanced"]
        ign_dev = settings_json[conf._set_name]["ignoredNodes"]["normal"]
        ign_dev_adv = settings_json[conf._set_name]["ignoredNodes"]["advanced"]
        assert conf.ignored_nodes == ign_com_norm + ign_com_adv + ign_dev + ign_dev_adv


def test_ignored_nodes_adv(tk_confs_adv, settings_json):
    for conf in tk_confs_adv:
        ign_com_adv = settings_json["common"]["ignoredNodes"]["advanced"]
        ign_dev = settings_json[conf._set_name]["ignoredNodes"]["advanced"]
        assert conf.ignored_nodes == ign_com_adv + ign_dev


def test_general_settings(tk_confs_norm, settings_json):
    for conf in tk_confs_norm:
        assert settings_json[conf._set_name]["generalSettings"] == conf.general_settings


def test_quant_sections(tk_confs_norm, settings_json):
    common = settings_json["common"]["sections"]
    for conf in tk_confs_norm:
        conf_secs = settings_json[conf._set_name]["sections"]
        common.update(conf_secs)
        assert conf.quant_sections == common


def test_quant_groups(tk_confs_norm, settings_json):
    common = settings_json["common"]["groups"]
    for conf in tk_confs_norm:
        conf_secs = settings_json[conf._set_name]["groups"]
        common.update(conf_secs)
        assert conf.quant_groups == common


def test_quants_mapping():
    settings = {
        "common": {
            "quants": {
                "/bar": {
                    "add": True,
                    "mapping": {
                        "SHFQA": {
                            "path": "/foo/bar",
                            "indexes": ["dev", 1],
                        }
                    },
                    "conf": {"datatype": "BOOLEAN"},
                }
            }
        },
        "SHFQA": {
            "quants": {
                "/bar2": {"add": True, "conf": {"foo": "bar"}, "indexes": [1, 2]}
            }
        },
    }
    obj = LabberConfiguration("SHFQA100", "normal", settings)
    assert obj.quants == {
        "/bar2": {"add": True, "conf": {"foo": "bar"}, "indexes": [1, 2]},
        "/foo/bar": {
            "indexes": ["dev", 1],
            "conf": {"datatype": "BOOLEAN"},
            "add": True,
        },
    }
    obj = LabberConfiguration("!=_NAME", "normal", settings)
    assert obj.quants == {}


class TestDeviceNotFound:
    def test_ignored_nodes_nodev(self):
        settings = {"common": {"ignoredNodes": {"normal": ["sa"], "advanced": ["fo"]}}}
        obj = LabberConfiguration("CANNOT_EXISTS", "normal", settings)
        assert obj.ignored_nodes == ["sa", "fo"]
        obj = LabberConfiguration("CANNOT_EXISTS", "advanced", settings)
        assert obj.ignored_nodes == ["fo"]

    def test_general_settings_nodev(self):
        settings = {"common": {"generalSettings": {"bar": "1"}}}
        obj = LabberConfiguration("CANNOT_EXISTS", "normal", settings)
        assert obj.general_settings == {"bar": "1"}

    def test_quant_sections_nodev(self):
        settings = {"common": {"sections": {"foobar1": "barcode"}}}
        obj = LabberConfiguration("CANNOT_EXISTS", "normal", settings)
        assert obj.quant_sections == {"foobar1": "barcode"}

    def test_quant_groups_nodev(self):
        settings = {"common": {"groups": {"foobar1": "barcode"}}}
        obj = LabberConfiguration("CANNOT_EXISTS", "normal", settings)
        assert obj.quant_groups == {"foobar1": "barcode"}

    def test_quants_mapping_nodev(self):
        settings = {
            "common": {
                "quants": {
                    "/bar": {
                        "add": True,
                        "conf": {"datatype": "BOOLEAN"},
                    },
                    "/*/foo": {"add": False, "conf": {"section": "12"}},
                }
            }
        }
        obj = LabberConfiguration("CANNOT_EXISTS", "normal", settings)
        assert obj.quants == {
            "/bar": {"add": True, "conf": {"datatype": "BOOLEAN"}},
            "/*/foo": {"add": False, "conf": {"section": "12"}},
        }


def test_devtype_quant():
    settings = {
        "common": {
            "quants": {},
        },
        "DEV": {
            "quants": {
                "/bar2": {"add": True, "conf": {"foo": "bar"}, "indexes": [1, 2]},
                "fordev": {
                    "add": True,
                    "conf": {"foo": "bar"},
                    "indexes": [1, 2],
                    "dev_type": ["DEV6000"],
                },
            }
        },
    }
    obj = LabberConfiguration("DEV", "normal", settings)
    assert obj.quants == {
        "/bar2": {"add": True, "conf": {"foo": "bar"}, "indexes": [1, 2]}
    }
    obj = LabberConfiguration("DEV6000", "normal", settings)
    assert obj.quants == {
        "/bar2": {"add": True, "conf": {"foo": "bar"}, "indexes": [1, 2]},
        "fordev": {
            "add": True,
            "conf": {"foo": "bar"},
            "indexes": [1, 2],
            "dev_type": ["DEV6000"],
        },
    }

def test_settings_version(settings_json):
    obj = LabberConfiguration("DEV", "normal", settings_json)
    assert obj.version == settings_json["version"]
