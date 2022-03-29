import pytest
from unittest.mock import MagicMock, patch
import sys
import tempfile
from pathlib import Path
from zhinst.toolkit import Waveforms
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / "labber"))
import zhinst.labber.driver.base_instrument as labber_driver
from zhinst.labber.driver.base_instrument import logger


@pytest.fixture()
def mock_toolkit_session():
    with patch(
        "zhinst.labber.driver.base_instrument.Session", autospec=True
    ) as session:
        yield session


@pytest.fixture()
def device_driver():
    settings = {
        "data_server": {
            "host": "localhost",
            "port": 8004,
            "hf2": False,
            "shared_session": True,
        },
        "instrument": {"base_type": "device", "type": "SHFQA"},
    }
    # reset session cache
    labber_driver.created_sessions = {}
    instrument = labber_driver.BaseDevice(settings=settings)
    instrument.comCfg = MagicMock()
    instrument.instrCfg = MagicMock()
    instrument.interface = MagicMock()
    instrument.dOp = {"operation": 0}
    return instrument


@pytest.fixture()
def shfqa_sweeper():
    settings = {
        "data_server": {
            "host": "localhost",
            "port": 8004,
            "hf2": False,
            "shared_session": True,
        },
        "instrument": {"base_type": "module", "type": "shfqa_sweeper"},
    }
    # reset session cache
    labber_driver.created_sessions = {}
    instrument = labber_driver.BaseDevice(settings=settings)
    instrument.comCfg = MagicMock()
    instrument.instrCfg = MagicMock()
    instrument.interface = MagicMock()
    instrument.dOp = {"operation": 0}
    return instrument


@pytest.fixture()
def daq_module():
    settings = {
        "data_server": {
            "host": "localhost",
            "port": 8004,
            "hf2": False,
            "shared_session": True,
        },
        "instrument": {"base_type": "module", "type": "daq"},
    }
    # reset session cache
    labber_driver.created_sessions = {}
    instrument = labber_driver.BaseDevice(settings=settings)
    instrument.comCfg = MagicMock()
    instrument.instrCfg = MagicMock()
    instrument.interface = MagicMock()
    instrument.dOp = {"operation": 0}
    return instrument

@pytest.fixture()
def sweeper_module():
    settings = {
        "data_server": {
            "host": "localhost",
            "port": 8004,
            "hf2": False,
            "shared_session": True,
        },
        "instrument": {"base_type": "module", "type": "sweeper"},
    }
    # reset session cache
    labber_driver.created_sessions = {}
    instrument = labber_driver.BaseDevice(settings=settings)
    instrument.comCfg = MagicMock()
    instrument.instrCfg = MagicMock()
    instrument.interface = MagicMock()
    instrument.dOp = {"operation": 0}
    return instrument


@pytest.fixture()
def session_driver():
    settings = {
        "data_server": {
            "hf2": False,
            "shared_session": True,
        },
        "instrument": {"base_type": "DataServer"},
    }
    # reset session cache
    labber_driver.created_sessions = {}
    instrument = labber_driver.BaseDevice(settings=settings)
    instrument.comCfg = MagicMock()
    instrument.instrCfg = MagicMock()
    instrument.interface = MagicMock()
    instrument.dOp = {"operation": 0}
    return instrument


def create_quant_mock(name, instrument, set_cmd, get_cmd):
    quant = MagicMock()
    quant.name = name
    quant.set_cmd = set_cmd
    quant.get_cmd = get_cmd
    instrument._node_quant_map[instrument._quant_to_path(name)] = name
    return quant


def compare_waveforms(a, b):
    for tar, act in zip(a.keys(), b.keys()):
        assert tar == act
        assert all(a[tar][0] == b[act][0])
        if a[tar][1] is not None and b[act][1] is not None:
            assert all(a[tar][1] == b[act][1])
        else:
            assert a[tar][1] == b[act][1]
        if a[tar][2] is not None and b[act][2] is not None:
            assert all(a[tar][2] == b[act][2])
        else:
            assert a[tar][2] == b[act][2]


class TestBase:
    def test_logger_path(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            log_path = Path(tmpdirname) / "test.log"
            settings = {
                "data_server": {
                    "host": "localhost",
                    "port": 8004,
                    "hf2": False,
                    "shared_session": True,
                },
                "instrument": {"base_type": "device", "type": "SHFQA"},
                "logger_path": log_path.resolve(),
            }
            labber_driver.BaseDevice(settings=settings)
            assert log_path.exists()
            # Remove handler so tmpdirname can be unlinked.
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)

            with open(Path(tmpdirname) / "test.log") as f:
                assert "" in f.read()

    def test_performOpen_device(self, mock_toolkit_session, device_driver):
        device_driver.comCfg.getAddressString.return_value = "DEV1234"
        device_driver.performOpen()
        mock_toolkit_session.assert_called_with("localhost", 8004, hf2=False)
        mock_toolkit_session.return_value.connect_device.assert_called_with("DEV1234")

    def test_performOpen_module(self, mock_toolkit_session, shfqa_sweeper):
        shfqa_sweeper.performOpen()
        mock_toolkit_session.assert_called_with("localhost", 8004, hf2=False)
        assert (
            shfqa_sweeper._instrument
            == mock_toolkit_session.return_value.modules.create_shfqa_sweeper.return_value
        )

        # Missing type property
        del shfqa_sweeper._instrument_settings["instrument"]["type"]
        with pytest.raises(RuntimeError):
            shfqa_sweeper.performOpen()

    def test_performOpen_session(self, mock_toolkit_session, session_driver):
        session_driver.comCfg.getAddressString.return_value = "testee:6543"
        session_driver.performOpen()
        mock_toolkit_session.assert_called_with("testee", 6543, hf2=False)
        assert session_driver._instrument == session_driver._session

    def test_performSet_node(self, mock_toolkit_session, device_driver):
        device_driver.comCfg.getAddressString.return_value = "DEV1234"
        device_driver.performOpen()

        # Standart node set
        quant = create_quant_mock("Test - Name", device_driver, "test/node", "")
        device_driver.performSetValue(quant, 0)
        device_driver._instrument[quant.set_cmd].assert_called_with(0)

        # Wait for node
        quant = create_quant_mock(
            "qachannels - 0 - readout - result - enable",
            device_driver,
            "qachannels/0/readout/result/enable",
            "qachannels/0/readout/result/enable",
        )
        device_driver.performSetValue(quant, 1)
        device_driver._instrument[quant.set_cmd].assert_called_with(1)
        device_driver._instrument[
            quant.set_cmd
        ].wait_for_state_change.assert_called_with(1)

        # With exception
        device_driver._instrument[quant.set_cmd].side_effect = RuntimeError(
            "Test Exception"
        )
        with patch("zhinst.labber.driver.base_instrument.logger") as logger:
            device_driver.performSetValue(quant, -1)
        logger.error.assert_called_with(
            "%s", device_driver._instrument[quant.set_cmd].side_effect
        )

        # Without set command
        quant = create_quant_mock("Test - Name", device_driver, "", "")
        assert device_driver.performSetValue(quant, 0) == quant.getValue()

    def test_performSet_transaction_node(self, mock_toolkit_session, device_driver):
        device_driver.comCfg.getAddressString.return_value = "DEV1234"
        device_driver.performOpen()

        # Standart node set
        quant = create_quant_mock("Test - Name", device_driver, "test/node", "")
        device_driver.performSetValue(quant, 0, options={"call_no": 0, "n_calls": 3})
        device_driver._instrument[quant.set_cmd].assert_called_with(0)

        quant = create_quant_mock("Test - 2", device_driver, "test/2", "")
        device_driver.performSetValue(quant, 5.0, options={"call_no": 1, "n_calls": 3})
        device_driver._instrument[quant.set_cmd].assert_called_with(5.0)

        quant = create_quant_mock("Test - 3", device_driver, "test/3", "")
        device_driver.performSetValue(
            quant, "Test", options={"call_no": 2, "n_calls": 3}
        )
        device_driver._instrument[quant.set_cmd].assert_called_with("Test")
        device_driver._instrument.root.set_transaction.assert_called_once()
        device_driver._instrument.root.set_transaction.return_value.__enter__.assert_called_once()
        device_driver._instrument.root.set_transaction.return_value.__exit__.assert_called_once()

        # Node that does not support a transaction
        quant = create_quant_mock("System - Identify", device_driver, "test/3", "")
        with patch("zhinst.labber.driver.base_instrument.logger") as logger:
            assert "Test" == device_driver.performSetValue(
                quant, "Test", options={"call_no": 2, "n_calls": 3}
            )
        logger.info.assert_called_with(
            "%s: Transaction is not supported for this node. Please set value manually.",
            quant.name,
        )

        # Error during end transaction
        quant = create_quant_mock("Test - Name", device_driver, "test/node", "")
        error = RuntimeError("testee")
        device_driver._instrument.root.set_transaction().__exit__.side_effect = error
        with patch("zhinst.labber.driver.base_instrument.logger") as logger:
            device_driver.performSetValue(
                quant, 0, options={"call_no": 0, "n_calls": 1}
            )
        logger.error.assert_called_with("Error during ending a transaction: %s", error)

    def test_performSet_sweep(self, mock_toolkit_session, device_driver):
        device_driver.comCfg.getAddressString.return_value = "DEV1234"
        device_driver.performOpen()

        # Currently the sweepRate keyword does not have any effect
        quant = create_quant_mock("Test - Name", device_driver, "test/node", "")
        device_driver.performSetValue(quant, 1.0, sweepRate=1)
        device_driver._instrument[quant.set_cmd].assert_called_with(1.0)

    def test_performSet_csv(self, mock_toolkit_session, device_driver):
        device_driver.comCfg.getAddressString.return_value = "DEV1234"
        device_driver.performOpen()

        # Generator Wave
        input = Path("tests/data/pulses.csv")
        device_driver.instrCfg.getQuantity.return_value.getValue.return_value = input

        quant = create_quant_mock(
            "qachannels - 0 - generator - pulses", device_driver, "*.csv", ""
        )
        assert input == device_driver.performSetValue(quant, input)
        target = Waveforms()
        target[0] = np.array([1.0 + 5.0j, 2.0 + 5.0j, 5.0 + 0.0j])
        target[1] = np.array([1, 4, 6])
        target[3] = np.array([1.0 + 1.0j, 0.0 + 6.0j, 7.0 + 0.0j])

        actual = device_driver._instrument.qachannels[
            0
        ].generator.write_to_waveform_memory.call_args[1]["pulses"]
        compare_waveforms(target, actual)

        # Empty generator waveform
        input = Path(".")
        device_driver.instrCfg.getQuantity.return_value.getValue.return_value = input
        assert input == device_driver.performSetValue(quant, input)
        device_driver._instrument.qachannels[
            0
        ].generator.write_to_waveform_memory.call_args[1]["pulses"]._waveforms == {}

        # AWG Wave
        waves1 = Path("tests/data/waves1.csv")
        waves2 = Path("tests/data/waves2.csv")
        markers = Path("tests/data/markers.csv")

        device_driver.instrCfg.getQuantity.return_value.getValue.side_effect = [
            waves1,
            waves2,
            markers,
        ]
        quant = create_quant_mock("awgs - 0 - waves1", device_driver, "*.csv", "")
        assert input == device_driver.performSetValue(quant, input)
        target = Waveforms()
        target[0] = (
            np.array([1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0]),
            np.array([5.0, -5.0, 5.0, -5.0, 5.0, -5.0, 5.0, -5.0]),
            None,
        )
        target[2] = (
            np.array([2.0, -2.0, 2.0, -2.0, 2.0, -2.0, 2.0, -2.0]),
            np.array([8.0, -8.0, 8.0, -8.0, 8.0, -8.0, 8.0, -8.0]),
            np.array([1, 1, 1, 0, 1, 1, 1, 1]),
        )
        actual = device_driver._instrument.awgs[0].write_to_waveform_memory.call_args[
            1
        ]["waveforms"]
        compare_waveforms(target, actual)

        # AWG Wave without marker
        waves1 = Path("tests/data/waves1.csv")
        waves2 = Path("tests/data/waves2.csv")
        markers = Path(".")

        device_driver.instrCfg.getQuantity.return_value.getValue.side_effect = [
            waves1,
            waves2,
            markers,
        ]
        quant = create_quant_mock("awgs - 0 - waves1", device_driver, "*.csv", "")
        assert input == device_driver.performSetValue(quant, input)
        target = Waveforms()
        target[0] = (
            np.array([1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0]),
            np.array([5.0, -5.0, 5.0, -5.0, 5.0, -5.0, 5.0, -5.0]),
            None,
        )
        target[2] = (
            np.array([2.0, -2.0, 2.0, -2.0, 2.0, -2.0, 2.0, -2.0]),
            np.array([8.0, -8.0, 8.0, -8.0, 8.0, -8.0, 8.0, -8.0]),
            None,
        )
        actual = device_driver._instrument.awgs[0].write_to_waveform_memory.call_args[
            1
        ]["waveforms"]
        compare_waveforms(target, actual)

        # None existing wave
        waves1 = Path("tests/data/wav.csv")
        waves2 = Path(".")
        markers = Path(".")
        device_driver.instrCfg.getQuantity.return_value.getValue.side_effect = [
            waves1,
            waves2,
            markers,
        ]
        assert input == device_driver.performSetValue(quant, input)
        actual = device_driver._instrument.awgs[0].write_to_waveform_memory.call_args[
            1
        ]["waveforms"]
        compare_waveforms(Waveforms(), actual)

    def test_performSet_function_delayed(self, mock_toolkit_session, device_driver):
        device_driver.comCfg.getAddressString.return_value = "DEV1234"
        device_driver.performOpen()

        waves1 = Path("tests/data/waves1.csv")
        waves2 = Path("tests/data/waves2.csv")
        markers = Path("tests/data/markers.csv")

        device_driver.instrCfg.getQuantity.return_value.getValue.side_effect = [
            waves1,
            waves2,
            markers,
        ]
        quant = create_quant_mock("awgs - 0 - waves1", device_driver, "*.csv", "")
        device_driver.performSetValue(
            quant, waves1, options={"call_no": 0, "n_calls": 3}
        )
        device_driver._instrument.awgs[0].write_to_waveform_memory.assert_not_called()

        quant = create_quant_mock("awgs - 0 - waves2", device_driver, "*.csv", "")
        device_driver.performSetValue(
            quant, waves2, options={"call_no": 1, "n_calls": 3}
        )
        device_driver._instrument.awgs[0].write_to_waveform_memory.assert_not_called()

        quant = create_quant_mock("awgs - 0 - markers", device_driver, "*.csv", "")
        device_driver.performSetValue(
            quant, markers, options={"call_no": 2, "n_calls": 3}
        )
        device_driver._instrument.awgs[0].write_to_waveform_memory.assert_called_once()

        target = Waveforms()
        target[0] = (
            np.array([1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0]),
            np.array([5.0, -5.0, 5.0, -5.0, 5.0, -5.0, 5.0, -5.0]),
            None,
        )
        target[2] = (
            np.array([2.0, -2.0, 2.0, -2.0, 2.0, -2.0, 2.0, -2.0]),
            np.array([8.0, -8.0, 8.0, -8.0, 8.0, -8.0, 8.0, -8.0]),
            np.array([1, 1, 1, 0, 1, 1, 1, 1]),
        )
        actual = device_driver._instrument.awgs[0].write_to_waveform_memory.call_args[
            1
        ]["waveforms"]
        compare_waveforms(target, actual)

        # no setting function
        quant = create_quant_mock(
            "qachannels - 0 - generator - wait_done", device_driver, "", ""
        )
        device_driver.dOp["operation"] = 3
        device_driver.performSetValue(
            quant, waves2, options={"call_no": 1, "n_calls": 1}
        )
        device_driver._instrument.qachannels[0].generator.wait_done.assert_not_called()

    def test_performSet_json(self, mock_toolkit_session, device_driver):
        device_driver.comCfg.getAddressString.return_value = "DEV1234"
        device_driver.performOpen()

        quant = create_quant_mock(
            "awgs - 0 - commandtable - data", device_driver, "*.json", ""
        )
        # empty input
        input = Path(".")
        device_driver.instrCfg.getQuantity.return_value.getValue.return_value = input
        assert input == device_driver.performSetValue(quant, input)
        device_driver._instrument.awgs[
            0
        ].commandtable.upload_to_device.assert_called_with(ct={})

        # valid input
        input = Path("tests/data/test.json")
        device_driver.instrCfg.getQuantity.return_value.getValue.return_value = input

        assert input == device_driver.performSetValue(quant, input)
        device_driver._instrument.awgs[
            0
        ].commandtable.upload_to_device.assert_called_with(ct={"test": "a"})

    def test_performSet_text(self, mock_toolkit_session, device_driver):
        device_driver.comCfg.getAddressString.return_value = "DEV1234"
        device_driver.performOpen()

        quant = create_quant_mock(
            "awgs - 0 - sequencer_program", device_driver, "*.seqc", ""
        )
        # empty input
        input = Path(".")
        device_driver.instrCfg.getQuantity.return_value.getValue.return_value = input
        assert input == device_driver.performSetValue(quant, input)
        device_driver._instrument.awgs[0].load_sequencer_program.assert_not_called()

        # valid input
        input = Path("tests/data/test.seqc")
        device_driver.instrCfg.getQuantity.return_value.getValue.return_value = input

        assert input == device_driver.performSetValue(quant, input)
        device_driver._instrument.awgs[0].load_sequencer_program.assert_called_with(
            sequencer_program="test\n123\n"
        )

    def test_performSet_node_path(self, mock_toolkit_session, daq_module):
        daq_module.comCfg.getAddressString.return_value = "DEV1234"
        daq_module.performOpen()

        quant = create_quant_mock("Triggernode", daq_module, "triggernode", "")
        daq_module.performSetValue(quant, "test/a/b")
        daq_module._instrument["triggernode"].assert_called_with("/dev1234/test/a/b")

        daq_module.performSetValue(quant, "/test/a/b")
        daq_module._instrument["triggernode"].assert_called_with("/dev1234/test/a/b")

        daq_module.performSetValue(quant, "/dev1234/test/a/b")
        daq_module._instrument["triggernode"].assert_called_with("/dev1234/test/a/b")

    def test_performGet_node(self, mock_toolkit_session, device_driver):
        device_driver.comCfg.getAddressString.return_value = "DEV1234"
        device_driver.performOpen()

        # Standart node get
        quant = create_quant_mock("Test - Name", device_driver, "", "test/node")
        device_driver.performGetValue(quant)
        device_driver._instrument[quant.get_cmd].assert_called_with(
            parse=False, enum=False
        )

        # Parser
        device_driver._instrument[quant.get_cmd].return_value = {"x": 1, "y": 2}
        assert complex(1, 2) == device_driver.performGetValue(quant)
        device_driver._instrument[quant.get_cmd].assert_called_with(
            parse=False, enum=False
        )

        device_driver._instrument[quant.get_cmd].return_value = {
            "dio": [1.5, 4],
            "y": 2,
        }
        assert 1.5 == device_driver.performGetValue(quant)
        device_driver._instrument[quant.get_cmd].assert_called_with(
            parse=False, enum=False
        )

        device_driver._instrument[quant.get_cmd].return_value = {
            "y": 2,
        }
        with patch("zhinst.labber.driver.base_instrument.logger") as logger:
            device_driver.performGetValue(quant)
        logger.error.assert_called_with('Unknown data received %s', {'y': 2})

        # With exception
        device_driver._instrument[quant.get_cmd].side_effect = RuntimeError(
            "Test Exception"
        )
        with patch("zhinst.labber.driver.base_instrument.logger") as logger:
            device_driver.performGetValue(quant, -1)
        logger.error.assert_called_with(
            "%s", device_driver._instrument[quant.get_cmd].side_effect
        )

        # Without set command
        quant = create_quant_mock("Test - Name", device_driver, "", "")
        device_driver.performGetValue(quant)

    def test_performGet_Get_CFG(self, mock_toolkit_session, device_driver):
        device_driver.comCfg.getAddressString.return_value = "DEV1234"
        device_driver.performOpen()

        device_driver.dOp["operation"] = 4

        # Not existing node (in snapshot)
        device_driver._instrument.root["*"].side_effect = [{}, 1]
        quant = create_quant_mock("Test - Name", device_driver, "", "test/node")
        assert device_driver.performGetValue(quant) == 1

        # Not existing node (in snapshot)
        device_driver._instrument.root["*"].side_effect = [{}, KeyError("test")]
        with patch("zhinst.labber.driver.base_instrument.logger") as logger:
            device_driver.performGetValue(quant)
        logger.error.assert_called_with("%s not found", "test/node")
        # existing node
        device_driver._instrument.root["*"].side_effect = None
        device_driver._instrument.root["*"].return_value = {
            device_driver._instrument.root["test/node"]: 0
        }
        assert device_driver.performGetValue(quant) == 0

    def test_performGet_function(self, mock_toolkit_session, shfqa_sweeper):
        shfqa_sweeper.comCfg.getAddressString.return_value = "DEV1234"
        shfqa_sweeper.performOpen()

        shfqa_sweeper._instrument.run.return_value = {
            "vector": np.array([1, 1, 1]),
            "test": "test",
        }
        shfqa_sweeper.instrCfg.getQuantity.return_value.getTraceDict.side_effect = (
            lambda a, **kwarg: a
        )

        quant = create_quant_mock("result", shfqa_sweeper, "", "")

        shfqa_sweeper.performGetValue(quant)
        set_value = shfqa_sweeper.instrCfg.getQuantity.return_value.setValue
        shfqa_sweeper._instrument.run.assert_called_once()
        assert all(set_value.call_args_list[0][0][0] == np.array([1, 1, 1]))

        # get config
        shfqa_sweeper.dOp["operation"] = 4
        assert shfqa_sweeper.performGetValue(quant) == 0
        quant.datatype = quant.STRING
        assert shfqa_sweeper.performGetValue(quant) == ""
        quant.datatype = quant.PATH
        assert shfqa_sweeper.performGetValue(quant) == ""

        # non existing quant
        shfqa_sweeper.dOp["operation"] = None
        shfqa_sweeper.instrCfg.getQuantity.side_effect = KeyError("test")
        with patch("zhinst.labber.driver.base_instrument.logger") as logger:
            shfqa_sweeper.performGetValue(quant)
        logger.debug.assert_any_call("%s does not exist", "result")
        shfqa_sweeper.instrCfg.getQuantity.side_effect = None

        # Invalid return value
        shfqa_sweeper._instrument.run.return_value = None
        with patch("zhinst.labber.driver.base_instrument.logger") as logger:
            shfqa_sweeper.performGetValue(quant)
        logger.error.call_count == 1

        # Exception in function call
        error = RuntimeError("test")
        shfqa_sweeper._instrument.run.side_effect = error
        with patch("zhinst.labber.driver.base_instrument.logger") as logger:
            shfqa_sweeper.performGetValue(quant)
        logger.error.assert_called_with("%s", error)

    def test_module_subscribe(self, mock_toolkit_session, daq_module):
        daq_module.comCfg.getAddressString.return_value = "DEV1234"
        daq_module.performOpen()
        quant = create_quant_mock("Signal - 1", daq_module, "", "")
        daq_module.instrCfg.getQuantity.return_value.getValue.return_value = "test/a/b"
        daq_module.performSetValue(quant, "test/a/b")
        quant.setValue.assert_called_with("test/a/b")
        daq_module._instrument.raw_module.subscribe.assert_called_with(
            "/dev1234/test/a/b"
        )

        quant1 = create_quant_mock("Signal - 2", daq_module, "", "")
        quant2 = create_quant_mock("Signal - 3", daq_module, "", "")
        daq_module.instrCfg.getQuantity.return_value.getValue.side_effect = [
            "test/a/b",
            "/dev1234/test/c/d",
            "",
        ]
        daq_module.performSetValue(quant1, "/dev1234/test/c/d")
        quant.setValue.assert_called_with("test/a/b")
        daq_module._instrument.raw_module.subscribe.assert_called_with(
            "/dev1234/test/c/d"
        )

    def test_module_read(self, mock_toolkit_session, daq_module):
        daq_module.comCfg.getAddressString.return_value = "DEV1234"
        daq_module.performOpen()

        daq_module.instrCfg.getQuantity.return_value.getTraceDict.side_effect = (
            lambda a, **kwarg: a
        )

        # value as default
        signal_quant = create_quant_mock("Signal - 1", daq_module, "", "")
        result_quant = create_quant_mock("Result - 1", daq_module, "", "")
        daq_module.instrCfg.getQuantity.return_value.getValue.return_value = "test/a/b"
        daq_module._instrument.raw_module.read.return_value = {
            "/dev1234/test/a/b": [{"value": np.array([1, 2, 3, 4])}]
        }
        daq_module.performGetValue(result_quant)
        daq_module._instrument.raw_module.read.assert_called_once()
        set_value = daq_module.instrCfg.getQuantity.return_value.setValue.call_args[0][
            0
        ]
        assert all(set_value == np.array([1, 2, 3, 4]))

        # r as default
        daq_module._instrument.raw_module.read.return_value = {
            "/dev1234/test/a/b": [{"r": np.array([1, 2, 3, 4])}]
        }
        daq_module.performGetValue(result_quant)
        set_value = daq_module.instrCfg.getQuantity.return_value.setValue.call_args[0][
            0
        ]
        assert all(set_value == np.array([1, 2, 3, 4]))

        # abs as default
        daq_module._instrument.raw_module.read.return_value = {
            "/dev1234/test/a/b": [{"abs": np.array([1, 2, 3, 4])}]
        }
        daq_module.performGetValue(result_quant)
        set_value = daq_module.instrCfg.getQuantity.return_value.setValue.call_args[0][
            0
        ]
        assert all(set_value == np.array([1, 2, 3, 4]))

        # x as default
        daq_module._instrument.raw_module.read.return_value = {
            "/dev1234/test/a/b": [{"x": np.array([1, 2, 3, 4])}]
        }
        daq_module.performGetValue(result_quant)
        set_value = daq_module.instrCfg.getQuantity.return_value.setValue.call_args[0][
            0
        ]
        assert all(set_value == np.array([1, 2, 3, 4]))

        # custom signal
        daq_module._instrument.raw_module.read.return_value = {
            "/dev1234/test/a/b": [{"sig3": np.array([1, 2, 3, 4])}]
        }
        daq_module.instrCfg.getQuantity.return_value.getValue.return_value = (
            "test/a/b::sig3"
        )
        daq_module.performGetValue(result_quant)
        set_value = daq_module.instrCfg.getQuantity.return_value.setValue.call_args[0][
            0
        ]
        assert all(set_value == np.array([1, 2, 3, 4]))

        # invalid custom signal
        daq_module.instrCfg.getQuantity.return_value.getValue.return_value = (
            "test/a/b::sig4"
        )
        with patch("zhinst.labber.driver.base_instrument.logger") as logger:
            daq_module.performGetValue(result_quant)
        logger.error.assert_called_with(
            "Valid signal for %s needed. Must be one of %s.\
                                 Use node/path::signal to specify a signal",
            "/signal/1",
            ["sig3"],
        )

    def test_module_clear(self, mock_toolkit_session, daq_module):
        daq_module.comCfg.getAddressString.return_value = "DEV1234"
        daq_module.performOpen()
        quant1 = create_quant_mock("Result - 1", daq_module, "", "")
        quant2 = create_quant_mock("Result - 3", daq_module, "", "")
        quant_clear = create_quant_mock("clear_results", daq_module, "", "")
        daq_module.instrCfg.getQuantity.return_value.VECTOR = 4
        daq_module.instrCfg.getQuantity.return_value.datatype = 4

        daq_module.instrCfg.getQuantity.return_value.getTraceDict.side_effect = (
            lambda a, **kwarg: a
        )
        assert daq_module.performSetValue(quant_clear, 1) == 0
        assert daq_module.instrCfg.getQuantity.return_value.setValue.call_count == 2
        assert (
            len(daq_module.instrCfg.getQuantity.return_value.setValue.call_args[0][0])
            == 0
        )

    def test_module_execute(self, mock_toolkit_session, sweeper_module):

        sweeper_module.comCfg.getAddressString.return_value = "DEV1234"
        sweeper_module.performOpen()
        quant = create_quant_mock("Enable", sweeper_module, "", "")

        # Execute
        sweeper_module.instrCfg.getQuantity.return_value.getValue.return_value = 1
        sweeper_module.performSetValue(quant, 1)
        sweeper_module._instrument.raw_module.execute.assert_called_once()
        # Stop
        sweeper_module.instrCfg.getQuantity.return_value.getValue.return_value = 0
        sweeper_module.performSetValue(quant, 0)
        sweeper_module._instrument.raw_module.finish.assert_called_once()
        # Get status
        sweeper_module.dOp["operation"] = 2
        sweeper_module.performGetValue(quant)
        sweeper_module._instrument.raw_module.finished.assert_called_once()
