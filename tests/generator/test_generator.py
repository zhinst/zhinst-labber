from collections import OrderedDict
import pytest
from unittest.mock import Mock, patch
import tempfile
from zhinst.labber import __version__
from zhinst.labber.generator.generator import (
    conf_to_labber_format,
    DeviceConfig,
    generate_labber_files,
)
from zhinst.toolkit.driver.devices import UHFLI, SHFQA


@pytest.fixture
def uhfli(data_dir, mock_connection, session):
    json_path = data_dir / "nodedoc_dev1234_uhfli.json"
    with json_path.open("r", encoding="UTF-8") as file:
        nodes_json = file.read()
    mock_connection.return_value.listNodesJSON.return_value = nodes_json
    mock_connection.return_value.getString.return_value = ""
    yield UHFLI("DEV1234", "UHFLI", session)


@pytest.fixture
def shfqa(data_dir, mock_connection, session):
    json_path = data_dir / "nodedoc_dev1234_shfqa.json"
    with json_path.open("r", encoding="UTF-8") as file:
        nodes_json = file.read()
    mock_connection.return_value.listNodesJSON.return_value = nodes_json
    mock_connection.return_value.getString.return_value = ""
    yield SHFQA("DEV1234", "SHFQA4", session)


def test_conf_to_labber_format():
    conf = {
        "General Settings": {"version": "1.0"},
        "/bar/0/foo/2/wave": {
            "set_cmd": "/bar/0/foo/2/wave",
            "get_cmd": "/bar/0/foo/2/wave",
            "label": "/bar/0/foo/2/wave",
            "section": "bar",
            "group": "bar 0",
            "tooltip": "tooltip",
            "datatype": "BOOLEAN",
        },
        "/bar/1/foo/0/wave": {
            "set_cmd": "/bar/1/foo/0/wave",
            "get_cmd": "/bar/1/foo/0/wave",
            "label": "/bar/1/foo/0/wave",
            "section": "bar",
            "group": "bar 0",
            "tooltip": "tooltip",
            "datatype": "BOOLEAN",
        },
        "/bar/0/foo/1/wave": {
            "set_cmd": "/bar/0/foo/1/wave",
            "get_cmd": "/bar/0/foo/1/wave",
            "label": "/bar/0/foo/1/wave",
            "section": "bar",
            "group": "QAChannel 0",
            "tooltip": "tooltip",
            "datatype": "BOOLEAN",
        },
        "/bar/0/foo/0/wave": {
            "set_cmd": "/bar/0/foo/0/wave",
            "get_cmd": "/bar/0/foo/0/wave",
            "label": "/bar/0/foo/0/wave",
            "section": "bar",
            "group": "bar 0",
            "tooltip": "tooltip",
            "datatype": "BOOLEAN",
        },
        "/bar/1/foo/1/wave": {
            "set_cmd": "/bar/1/foo/1/wave",
            "get_cmd": "/bar/1/foo/1/wave",
            "label": "/bar/1/foo/1/wave",
            "section": "AWG Section",
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
                    "set_cmd": "/bar/0/foo/0/wave",
                    "get_cmd": "/bar/0/foo/0/wave",
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
                    "set_cmd": "/bar/0/foo/1/wave",
                    "get_cmd": "/bar/0/foo/1/wave",
                    "Label": "Bar - 0 - Foo - 1 - Wave",
                    "Section": "Bar",
                    "Group": "QAChannel 0",
                    "tooltip": "tooltip",
                    "datatype": "BOOLEAN",
                },
            ),
            (
                "Bar - 0 - Foo - 2 - Wave",
                {
                    "set_cmd": "/bar/0/foo/2/wave",
                    "get_cmd": "/bar/0/foo/2/wave",
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
                    "set_cmd": "/bar/1/foo/0/wave",
                    "get_cmd": "/bar/1/foo/0/wave",
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
                    "set_cmd": "/bar/1/foo/1/wave",
                    "get_cmd": "/bar/1/foo/1/wave",
                    "Label": "Bar - 1 - Foo - 1 - Wave",
                    "Section": "AWG Section",
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
        session.about = Mock()
        session.about.version = Mock(return_value="0.2.2")
        return DeviceConfig(uhfli, session, settings_json, "normal")

    def test_generate_quants_from_indexes_dev(self, dev_conf):
        r = dev_conf._quant_paths("/awgs/*/waveform/waves/*", ["dev", 4])
        assert r == [
            "/awgs/0/waveform/waves/0",
            "/awgs/0/waveform/waves/1",
            "/awgs/0/waveform/waves/2",
            "/awgs/0/waveform/waves/3",
        ]

    def test_generate_quants_from_indexes_no_idx(self, dev_conf):
        r = dev_conf._quant_paths("/awgs/*/markers", [])
        assert r == ["/awgs/0/markers"]

    def test_general_settings(self, dev_conf, settings_json):
        assert dev_conf.general_settings == {
            "General settings": {
                "driver_path": "Zurich_Instruments_UHFLI",
                "interface": "Other",
                "name": "Zurich Instruments UHFLI",
                "startup": "Do nothing",
                "support_arm": True,
                "support_hardware_loop": True,
                "version": f"0.2.2#{ __version__}#{settings_json['version']}"
            }
        }

@patch("zhinst.labber.generator.generator.open_settings_file")
@patch("zhinst.labber.generator.generator.Session")
def test_generate_labber_drivers_amt_uhfli(
    gen_ses, settings, uhfli, session, settings_json
):
    gen_ses.return_value = session
    settings.return_value = settings_json
    session.connect_device = Mock(return_value=uhfli)
    with tempfile.TemporaryDirectory() as tmpdirname:
        created, _ = generate_labber_files(tmpdirname, "normal", "dev1234", "localhost")
    # Dataserver + device + amount of zimodules. Times 3 (.json file, .ini, file, .py file)
    assert len(settings_json["misc"]["ziModules"]) == 1
    # No SHFQA_Sweeper: Minus 1 from ziModules lengths
    assert len(created) == (1 + len(settings_json["misc"]["ziModules"]) - 1 + 1) * 3


@patch("zhinst.labber.generator.generator.open_settings_file")
@patch("zhinst.labber.generator.generator.Session")
def test_generate_labber_drivers_amt_shfqa(
    gen_ses, settings, shfqa, session, settings_json
):
    gen_ses.return_value = session
    settings.return_value = settings_json
    shfqa.features = Mock()
    shfqa.features.options = Mock(return_value="FOO\nBAR")
    session.connect_device = Mock(return_value=shfqa)
    with tempfile.TemporaryDirectory() as tmpdirname:
        created, _ = generate_labber_files(tmpdirname, "normal", "dev1234", "localhost")
    # Dataserver + device + amount of zimodules. Times 3 (.json file, .ini, file, .py file)
    assert len(settings_json["misc"]["ziModules"]) == 1
    # SHFQA_Sweeper included
    assert len(created) == (1 + len(settings_json["misc"]["ziModules"]) + 1) * 3

    files = [
        f"{str(tmpdirname)}\\Zurich_Instruments_SHFQA4_FOO_BAR\\Zurich_Instruments_SHFQA4_FOO_BAR.py",
        f"{str(tmpdirname)}\\Zurich_Instruments_SHFQA4_FOO_BAR\\settings.json",
        f"{str(tmpdirname)}\\Zurich_Instruments_SHFQA4_FOO_BAR\\Zurich_Instruments_SHFQA4_FOO_BAR.ini"
    ]
    for file in files:
        assert file in list(map(str, created))
