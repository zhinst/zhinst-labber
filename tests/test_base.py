import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import sys


sys.path.insert(0, "/Users/tobiasa/git/zhinst-labber/tests/labber")
from zhinst.labber.base_instrument import BaseDevice


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
    instrument = BaseDevice(settings=settings)
    instrument.comCfg = MagicMock()
    instrument.instrCfg = MagicMock()
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
        "instrument": {"base_type": "module", "type": "AWG"},
    }
    instrument = BaseDevice(settings=settings)
    instrument.comCfg = MagicMock()
    instrument.instrCfg = MagicMock()
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
    instrument = BaseDevice(settings=settings)
    instrument.comCfg = MagicMock()
    instrument.instrCfg = MagicMock()
    return instrument


class TestBase:
    def test_performOpen_device(self, mock_toolkit_session, device_driver):
        device_driver.comCfg.getAddressString.return_value = "DEV1234"
        device_driver.performOpen()
        mock_toolkit_session.assert_called_with("localhost", 8004, hf2=False)
        mock_toolkit_session.return_value.connect_device.assert_called_with("DEV1234")

    def test_performOpen_module(self, mock_toolkit_session, module_driver):
        module_driver.comCfg.getAddressString.return_value = "DEV1234"
        module_driver.performOpen()
        mock_toolkit_session.assert_called_with("localhost", 8004, hf2=False)
        assert (
            module_driver._instrument == mock_toolkit_session.return_value.modules.awg
        )

        # Missing type property
        del module_driver._settings["instrument"]["type"]
        with pytest.raises(RuntimeError):
            module_driver.performOpen()

    def test_performOpen_session(self, mock_toolkit_session, session_driver):
        session_driver.comCfg.getAddressString.return_value = "DEV1234"
        session_driver.performOpen()
        mock_toolkit_session.assert_called_with("localhost", 8004, hf2=False)
        assert session_driver._instrument == session_driver._session
