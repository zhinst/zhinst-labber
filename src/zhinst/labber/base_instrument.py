import typing as t
import json
from enum import Enum


from BaseDriver import LabberDriver
from InstrumentDriver_Interface import Interface

from zhinst.toolkit import Session
from zhinst.toolkit.driver.devices import DeviceType
from zhinst.toolkit.driver.modules import ModuleType

from zhinst.labber.snapshot_manager import SnapshotManager

Quantity = t.TypeVar("Quantity")

created_sessions = {}

class BaseType(Enum):
    """Supported Instrument Types"""

    SESSION = 0,
    MODULE = 1,
    DEVICE = 2,

class BaseDevice(LabberDriver):
    """Implement a Labber Driver for the Zurich Instruments SHFSG"""

    def __init__(self, *args, settings_file, **kwargs):
        super().__init__(*args, **kwargs)
        self._session = None
        self._instrument = None
        self._base_type = None
        self._transaction = None
        self._snapshot = None

        with settings_file.open("r") as file:
            self._settings = json.loads(file.read())

    def _get_session(self, data_server_info:t.Dict[str, t.Any]) -> Session:
        target_host = data_server_info.get("host", "localhost")
        target_hf2 = data_server_info.get("hf2", False)
        target_port = data_server_info.get("port", 8005 if target_hf2 else 8004)
        if data_server_info.get("shared_session", True):
            for (host, port), session in created_sessions.items():
                if target_host == host and target_port == port:
                    return session
        new_session = Session(target_host, target_port, hf2=target_hf2)
        created_sessions[(target_host, target_port)] = new_session
        return new_session

    def _create_instrument(self, instrument_info:t.Dict[str, t.Any]) -> t.Union[Session, DeviceType, ModuleType]:
        base_type = instrument_info.get(base_type, "session")
        if base_type == "session":
            self._base_type = BaseType.SESSION
            return self._session
        if base_type == "module":
            self._base_type = BaseType.MODULE
            try:
                return getattr(self._session.modules, instrument_info["type"].lower())
            except KeyError as error:
                raise RuntimeError(
                    "Settingsfile is specifing a module as instrument but is "
                    "missing the \"type\" property."
                    ) from error
            except AttributeError as error:
                raise RuntimeError(
                    f"LabOne module with name {instrument_info['type'].lower()}"
                    " does not exist in toolkit."
                )
        self._base_type = BaseType.DEVICE
        return self._session.connect_device(self.comCfg.getAddressString())


    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection."""

        self._session = self._get_session(self._settings["data_server"])
        self._instrument = self._create_instrument(self._settings["instrument"])
        self._snapshot = SnapshotManager(self._instrument.root)

    def performClose(self, bError=False, options={}):
        """Perform the close instrument connection operation."""
        pass

    def initSetConfig(self):
        """Run before setting values in Set Config."""
        pass

    def performSetValue(
        self,
        quant: Quantity,
        value: t.Any,
        sweepRate: float = 0.0,
        options: t.Dict = {},
    ) -> t.Any:
        """Perform the Set Value instrument operation.

        It is important that the code inspects the sweepRate parameter to see if
        the user wants to set the value directly (sweepRate=0.0), or perform
        sweeping (sweepRate>0.0). Note that in sweep mode (sweepRate>0.0), the
        function should not wait for the sweep to finish, since the sweep
        checking/waiting is handled by the Instrument Server. The sweepRate
        parameter is defined in terms of change per second or change per
        minute, as set by the sweep_minute configuration parameter
        defined in the section above.

        Args:
            quant: Quantity that should be set
            value: Value to be set
            sweepRate: sweep rate. 0 if no sweep should be performed
            options: additional options for setting/getting a value
                Set:
                {
                    'operation':1
                    'quant':'QA Channel 1 - Trigger Level'
                    'value':0.501
                    'sweep_rate':0.0
                    'wait_for_sweep':True
                    'delay':693483.64
                }
                Get:
                {
                    'operation':2
                    'quant':'QA Channel 1 - Trigger Level'
                    'delay':693555.843
                }

        Returns:
            Value that was set. (if None Labber will automatically use the input
            value instead)
        """
        if sweepRate > 0.0:
            # TODO support sweeping of values?
            return value
        if quant.set_cmd:
            # Normal set of value
            return self._set_value_toolkit(quant, value, options=options)
        # Quants without a set_cmd ?
        return value

    def _set_value_toolkit(
        self, quant: Quantity, value: t.Any, *, options: t.Dict = {}
    ) -> None:
        if "call_no" in options and not self._transaction:
            # start transaction
            self._transaction = self._instrument.set_transaction
            self._transaction.__enter__()
        self._instrument[quant.set_cmd](value)
        if self._transaction and self.isFinalCall():
            # end transaction
            self._transaction.__exit__()
            self._transaction = None

    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation."""
        if quant.get_cmd:
            if self.dOp["operation"] == Interface.GET_CFG:
                # use a snapshot for the GET_CFG command
                return self._snapshot.get_value(quant.get_cmd)
            # clear snapshot if GET_CFG is finished
            self._snapshot.clear()
            return self._instrument[quant.get_cmd]()
        # TODO quant without a get_cmd
        return None

    def performArm(self, quant_names, options={}):
        """Perform the instrument arm operation"""
        # TODO

    def update_from_session(self, quant_name: str) -> None:
        """Read the value from the session and update the Labber controller.

        Args:
            quant_name: Name of the quant that should be updated
        """
        value = self.readValueFromOther(quant_name)
        self.setValue(quant_name, value)
