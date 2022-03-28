from collections import OrderedDict
import pytest
from pathlib import Path
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


class TestLabberConfigUHFLI:
    @pytest.fixture
    def dev_conf(self, uhfli, session, settings_json):
        session.about = Mock()
        session.about.version = Mock(return_value="0.2.2")
        return DeviceConfig(uhfli, session, settings_json, "normal")

    def test_general_settings(self, dev_conf, settings_json):
        assert dev_conf.general_settings == {
            "General settings": {
                "driver_path": "Zurich_Instruments_UHFLI",
                "interface": "Other",
                "name": "Zurich Instruments UHFLI",
                "startup": "Do nothing",
                "support_arm": True,
                "support_hardware_loop": True,
                "version": f"0.2.2#{ __version__}#{settings_json['version']}",
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


@patch("zhinst.labber.generator.generator.Session")
def test_generate_labber_drivers_amt_shfqa(gen_ses, shfqa, session, settings_json):
    gen_ses.return_value = session
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
        Path(tmpdirname)
        / "Zurich_Instruments_SHFQA4_FOO_BAR"
        / "Zurich_Instruments_SHFQA4_FOO_BAR.py",
        Path(tmpdirname) / "Zurich_Instruments_SHFQA4_FOO_BAR" / "settings.json",
        Path(tmpdirname)
        / "Zurich_Instruments_SHFQA4_FOO_BAR"
        / "Zurich_Instruments_SHFQA4_FOO_BAR.ini",
        Path(tmpdirname)
        / "Zurich_Instruments_DataServer"
        / "Zurich_Instruments_DataServer.py",
        Path(tmpdirname) / "Zurich_Instruments_DataServer" / "settings.json",
        Path(tmpdirname)
        / "Zurich_Instruments_DataServer"
        / "Zurich_Instruments_DataServer.ini",
    ]
    for file in files:
        assert file in created


@patch("zhinst.labber.generator.generator.Session")
def test_generate_labber_drivers_exists_shfqa(gen_ses, shfqa, session):
    gen_ses.return_value = session
    shfqa.features = Mock()
    shfqa.features.options = Mock(return_value="FOO\nBAR")
    session.connect_device = Mock(return_value=shfqa)
    with tempfile.TemporaryDirectory() as tmpdirname:
        _, _ = generate_labber_files(
            tmpdirname, "normal", "dev1234", "localhost", upgrade=False
        )
        created, _ = generate_labber_files(
            tmpdirname, "normal", "dev1234", "localhost", upgrade=False
        )
    assert created == []


@patch("zhinst.labber.generator.generator.Session")
def test_generate_labber_drivers_exists_upgrade_shfqa(gen_ses, shfqa, session):
    gen_ses.return_value = session
    shfqa.features = Mock()
    shfqa.features.options = Mock(return_value="FOO\nBAR")
    session.connect_device = Mock(return_value=shfqa)
    with tempfile.TemporaryDirectory() as tmpdirname:
        _, _ = generate_labber_files(
            tmpdirname, "normal", "dev1234", "localhost", upgrade=True
        )
        _, generated = generate_labber_files(
            tmpdirname, "normal", "dev1234", "localhost", upgrade=True
        )
    files = [
        Path(tmpdirname)
        / "Zurich_Instruments_SHFQA4_FOO_BAR"
        / "Zurich_Instruments_SHFQA4_FOO_BAR.py",
        Path(tmpdirname) / "Zurich_Instruments_SHFQA4_FOO_BAR" / "settings.json",
        Path(tmpdirname)
        / "Zurich_Instruments_SHFQA4_FOO_BAR"
        / "Zurich_Instruments_SHFQA4_FOO_BAR.ini",
        Path(tmpdirname)
        / "Zurich_Instruments_DataServer"
        / "Zurich_Instruments_DataServer.py",
        Path(tmpdirname) / "Zurich_Instruments_DataServer" / "settings.json",
        Path(tmpdirname)
        / "Zurich_Instruments_DataServer"
        / "Zurich_Instruments_DataServer.ini",
    ]
    for file in files:
        assert file in generated


class TestLabberConfigSHFQA:
    @pytest.fixture
    def dev_conf(self, shfqa, session, settings_json):
        session.about = Mock()
        session.about.version = Mock(return_value="0.2.2")
        return DeviceConfig(shfqa, session, settings_json, "normal")

    def test_config(self, dev_conf):
        r = dev_conf.config()
        assert r["/qachannels/2/triggers/0/imp50"] == {
            "section": "DIO",
            "group": "QA Channel 2",
            "label": "qachannels/2/triggers/0/imp50",
            "datatype": "BOOLEAN",
            "tooltip": "<html><body><p>Trigger Input impedance: When on, the Trigger Input impedance is 50 Ohm: when off, 1 kOhm.</p><p><ul><li>1_kOhm: 1 k Ohm</li><li>50_Ohm: 50 Ohm</li></ul></p><p><b>QACHANNELS/2/TRIGGERS/0/IMP50</b></p></body></html>",
            "cmd_def_1": "1_kOhm",
            "combo_def_1": "1_kOhm",
            "cmd_def_2": "50_Ohm",
            "combo_def_2": "50_Ohm",
            "permission": "BOTH",
            "set_cmd": "QACHANNELS/2/TRIGGERS/0/IMP50",
            "get_cmd": "QACHANNELS/2/TRIGGERS/0/IMP50",
        }
        assert r["/qachannels/3/readout/discriminators/5/threshold"] == {
            "section": "QA Setup",
            "group": "QA Channel 3 Readout",
            "label": "qachannels/3/readout/discriminators/5/threshold",
            "datatype": "DOUBLE",
            "tooltip": "<html><body><p>Sets the threshold level for the 2-state discriminator on the real signal axis in Vs.</p><p><b>QACHANNELS/3/READOUT/DISCRIMINATORS/5/THRESHOLD</b></p></body></html>",
            "permission": "BOTH",
            "set_cmd": "QACHANNELS/3/READOUT/DISCRIMINATORS/5/THRESHOLD",
            "get_cmd": "QACHANNELS/3/READOUT/DISCRIMINATORS/5/THRESHOLD",
        }
