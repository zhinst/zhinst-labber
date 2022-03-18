import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import sys
from pathlib import Path
from zhinst.toolkit import Waveforms
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / "labber"))
import zhinst.labber.base_instrument as labber_driver


@pytest.fixture()
def mock_toolkit_session():
    with patch("zhinst.labber.base_instrument.Session", autospec=True) as session:
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
def module_driver():
    settings = {
        "data_server": {
            "host": "localhost",
            "port": 8004,
            "hf2": False,
            "shared_session": True,
        },
        "instrument": {"base_type": "module", "type": "SHFQA_Sweeper"},
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
            "host": "localhost",
            "port": 8004,
            "hf2": False,
            "shared_session": True,
        },
        "instrument": {"base_type": "session"},
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
    def test_performOpen_device(self, mock_toolkit_session, device_driver):
        device_driver.comCfg.getAddressString.return_value = "DEV1234"
        device_driver.performOpen()
        mock_toolkit_session.assert_called_with("localhost", 8004, hf2=False)
        mock_toolkit_session.return_value.connect_device.assert_called_with("DEV1234")

    def test_performOpen_module(self, mock_toolkit_session, module_driver):
        module_driver.performOpen()
        mock_toolkit_session.assert_called_with("localhost", 8004, hf2=False)
        assert (
            module_driver._instrument == mock_toolkit_session.return_value.modules.shfqa_sweeper
        )

        # Missing type property
        del module_driver._instrument_settings["instrument"]["type"]
        with pytest.raises(RuntimeError):
            module_driver.performOpen()

    def test_performOpen_session(self, mock_toolkit_session, session_driver):
        session_driver.performOpen()
        mock_toolkit_session.assert_called_with("localhost", 8004, hf2=False)
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
        with patch("zhinst.labber.base_instrument.logger") as logger:
            device_driver.performSetValue(quant, -1)
        logger.error.assert_called_with(
            device_driver._instrument[quant.set_cmd].side_effect
        )

        # Without set command
        quant = create_quant_mock("Test - Name", device_driver, "", "")
        assert device_driver.performSetValue(quant, 0) == None

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

    def test_performGet_node(self, mock_toolkit_session, device_driver):
        device_driver.comCfg.getAddressString.return_value = "DEV1234"
        device_driver.performOpen()

        # Standart node get
        quant = create_quant_mock("Test - Name", device_driver, "", "test/node")
        device_driver.performGetValue(quant)
        device_driver._instrument[quant.get_cmd].assert_called_with()

        # With exception
        device_driver._instrument[quant.get_cmd].side_effect = RuntimeError(
            "Test Exception"
        )
        with patch("zhinst.labber.base_instrument.logger") as logger:
            device_driver.performGetValue(quant, -1)
        logger.error.assert_called_with(
            device_driver._instrument[quant.get_cmd].side_effect
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
        with patch("zhinst.labber.base_instrument.logger") as logger:
            device_driver.performGetValue(quant)
        logger.error.assert_called_with('%s not found', 'test/node')
        # existing node
        device_driver._instrument.root["*"].side_effect = None
        device_driver._instrument.root["*"].return_value = {
            device_driver._instrument.root["test/node"]: 0
        }
        assert device_driver.performGetValue(quant) == 0

    def test_performGet_function(self, mock_toolkit_session, module_driver):
        module_driver.comCfg.getAddressString.return_value = "DEV1234"
        module_driver.performOpen()

        module_driver._instrument.run.return_value = {'vector': np.array([1, 1, 1]), 'test': "test"}
        module_driver.instrCfg.getQuantity.return_value.getTraceDict.side_effect = (
            lambda a, **kwarg: a
        )

        quant = create_quant_mock("result", module_driver, "", "")

        module_driver.performGetValue(quant, input)
        set_value = module_driver.instrCfg.getQuantity.return_value.setValue
        module_driver._instrument.run.assert_called_once()
        assert all(set_value.call_args_list[0][0][0] == np.array([1, 1, 1]))

        # non existing quant
        module_driver.instrCfg.getQuantity.side_effect = KeyError("test")
        with patch("zhinst.labber.base_instrument.logger") as logger:
            module_driver.performGetValue(quant, input)
        logger.debug.assert_any_call('%s does not exist', 'result')
        module_driver.instrCfg.getQuantity.side_effect = None

        # Invalid return value
        module_driver._instrument.run.return_value = None
        with patch("zhinst.labber.base_instrument.logger") as logger:
            module_driver.performGetValue(quant, input)
        logger.error.call_count == 1

        # Exception in function call
        error = RuntimeError("test")
        module_driver._instrument.run.side_effect = error
        with patch("zhinst.labber.base_instrument.logger") as logger:
            module_driver.performGetValue(quant, input)
        logger.error.assert_called_with(error)
