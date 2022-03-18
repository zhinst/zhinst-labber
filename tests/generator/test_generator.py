from collections import OrderedDict
import pytest
from zhinst.labber.generator.generator import conf_to_labber_format, DeviceConfig
from zhinst.toolkit.driver.devices import UHFLI


@pytest.fixture
def uhfli(data_dir, mock_connection, session):
    json_path = data_dir / "nodedoc_dev1234_uhfli.json"
    with json_path.open("r", encoding="UTF-8") as file:
        nodes_json = file.read()
    mock_connection.return_value.listNodesJSON.return_value = nodes_json
    mock_connection.return_value.getString.return_value = ""
    yield UHFLI("DEV1234", "UHFLI", session)


def test_conf_to_labber_format():
    conf = {
        "General Settings": {"version": "1.0"},
        "/bar/0/foo/2/wavE": {
            "set_cmd": "/bar/0/foo/2/wavE",
            "get_cmd": "/bar/0/foo/2/wavE",
            "label": "/bar/0/foo/2/wavE",
            "section": "bar",
            "group": "bar 0",
            "tooltip": "tooltip",
            "datatype": "BOOLEAN",
        },
        "/bar/1/foo/0/wavE": {
            "set_cmd": "/bar/1/foo/0/wavE",
            "get_cmd": "/bar/1/foo/0/wavE",
            "label": "/bar/1/foo/0/wavE",
            "section": "bar",
            "group": "bar 0",
            "tooltip": "tooltip",
            "datatype": "BOOLEAN",
        },
        "/bar/0/foo/1/wavE": {
            "set_cmd": "/bar/0/foo/1/wavE",
            "get_cmd": "/bar/0/foo/1/wavE",
            "label": "/bar/0/foo/1/wavE",
            "section": "bar",
            "group": "bar 0",
            "tooltip": "tooltip",
            "datatype": "BOOLEAN",
        },
        "/bar/0/foo/0/wavE": {
            "set_cmd": "/bar/0/foo/0/wavE",
            "get_cmd": "/bar/0/foo/0/wavE",
            "label": "/bar/0/foo/0/wavE",
            "section": "bar",
            "group": "bar 0",
            "tooltip": "tooltip",
            "datatype": "BOOLEAN",
        },
        "/bar/1/foo/1/wavE": {
            "set_cmd": "/bar/1/foo/1/wavE",
            "get_cmd": "/bar/1/foo/1/wavE",
            "label": "/bar/1/foo/1/wavE",
            "section": "bar",
            "group": "bar 0",
            "tooltip": "tooltip",
            "datatype": "BOOLEAN",
        },
    }
    d = conf_to_labber_format(conf, delim=" - ")
    assert d == OrderedDict(
        [
            (
                "Bar - 0 - Foo - 0 - Wave",
                {
                    "set_cmd": "/bar/0/foo/0/wavE",
                    "get_cmd": "/bar/0/foo/0/wavE",
                    "Label": "Bar - 0 - Foo - 0 - Wave",
                    "Section": "Bar",
                    "Group": "Bar 0",
                    "tooltip": "tooltip",
                    "datatype": "BOOLEAN",
                },
            ),
            (
                "Bar - 0 - Foo - 1 - Wave",
                {
                    "set_cmd": "/bar/0/foo/1/wavE",
                    "get_cmd": "/bar/0/foo/1/wavE",
                    "Label": "Bar - 0 - Foo - 1 - Wave",
                    "Section": "Bar",
                    "Group": "Bar 0",
                    "tooltip": "tooltip",
                    "datatype": "BOOLEAN",
                },
            ),
            (
                "Bar - 0 - Foo - 2 - Wave",
                {
                    "set_cmd": "/bar/0/foo/2/wavE",
                    "get_cmd": "/bar/0/foo/2/wavE",
                    "Label": "Bar - 0 - Foo - 2 - Wave",
                    "Section": "Bar",
                    "Group": "Bar 0",
                    "tooltip": "tooltip",
                    "datatype": "BOOLEAN",
                },
            ),
            (
                "Bar - 1 - Foo - 0 - Wave",
                {
                    "set_cmd": "/bar/1/foo/0/wavE",
                    "get_cmd": "/bar/1/foo/0/wavE",
                    "Label": "Bar - 1 - Foo - 0 - Wave",
                    "Section": "Bar",
                    "Group": "Bar 0",
                    "tooltip": "tooltip",
                    "datatype": "BOOLEAN",
                },
            ),
            (
                "Bar - 1 - Foo - 1 - Wave",
                {
                    "set_cmd": "/bar/1/foo/1/wavE",
                    "get_cmd": "/bar/1/foo/1/wavE",
                    "Label": "Bar - 1 - Foo - 1 - Wave",
                    "Section": "Bar",
                    "Group": "Bar 0",
                    "tooltip": "tooltip",
                    "datatype": "BOOLEAN",
                },
            ),
            ("General Settings", {"version": "1.0"}),
        ]
    )


class TestLabberConfig:
    @pytest.fixture
    def dev_conf(self, uhfli, session, settings_json):
        return DeviceConfig(uhfli, session, settings_json, "normal")

    def test_generate_quants_from_indexes_dev(self, dev_conf):
        r = dev_conf._quant_paths("/awgs/*/waveform/waves/*", ["dev", 4])
        assert r == [
            "/awgs/0/waveform/waves/0",
            "/awgs/0/waveform/waves/1",
            "/awgs/0/waveform/waves/2",
            "/awgs/0/waveform/waves/3"
        ]

    def test_generate_quants_from_indexes_no_idx(self, dev_conf):
        r = dev_conf._quant_paths("/awgs/*/markers", [])
        assert r == [
            "/awgs/0/markers"
        ]
