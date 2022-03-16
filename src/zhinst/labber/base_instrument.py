import typing as t
from enum import Enum
from pathlib import Path
from itertools import repeat
import inspect
import fnmatch
import logging
import os
import sys
import json

import numpy as np
import csv

from BaseDriver import LabberDriver
from InstrumentDriver_Interface import Interface

from zhinst.toolkit import Session, Waveforms
from zhinst.toolkit.driver.devices import DeviceType
from zhinst.toolkit.driver.modules import ModuleType

from zhinst.labber.snapshot_manager import SnapshotManager, TransactionManager

Quantity = t.TypeVar("Quantity")
NumpyArray = t.TypeVar("NumpyArray")

created_sessions = {}

logger = logging.getLogger("")
logger.setLevel(logging.DEBUG)
# fh = logging.FileHandler('my_log_info.log')
sh = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%a, %d %b %Y %H:%M:%S",
)
# fh.setFormatter(formatter)
sh.setFormatter(formatter)
# logger.addHandler(fh)
logger.addHandler(sh)


class BaseType(Enum):
    """Supported Instrument Types"""

    SESSION = 0
    MODULE = 1
    DEVICE = 2


class BaseDevice(LabberDriver):
    """Implement a Labber Driver for the Zurich Instruments SHFSG"""

    def __init__(self, *args, settings, **kwargs):
        super().__init__(*args, **kwargs)
        self._session = None
        self._instrument = None
        self._base_type = None
        self._transaction = None
        self._snapshot = None
        self._settings = settings
        logger.debug(f"PID: {os.getpid()}")

    def performOpen(self, options: t.Dict = {}) -> None:
        """Perform the operation of opening the instrument connection."""
        self._session = self._get_session(self._settings["data_server"])
        self._instrument = self._create_instrument(self._settings["instrument"])
        self._snapshot = SnapshotManager(self._instrument.root)
        self._transaction = TransactionManager(self._instrument, self)
        self._path_seperator = self._settings.get("path_seperator", " - ")

        settings_file = Path(__file__).parent / "settings.json"
        self._node_info = {}
        self._function_info = {}
        if settings_file.exists():
            with settings_file.open("r") as file:
                node_info = json.loads(file.read())
                self._node_info = node_info["common"].get("quants", {})
                device = self._settings["instrument"].get("type", None)
                if device:
                    device_info = node_info.get(device, {}).get("quants", {})
                    self._node_info = {**self._node_info, **device_info}
                self._function_info = node_info.get("functions", {})
        else:
            logger.error(f"{settings_file} not found!")

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
        if "call_no" in options and not self._transaction.is_running():
            self._transaction.start()
        try:
            if sweepRate > 0.0:
                # TODO support sweeping of values?
                logger.error(f"{quant.name}: Sweeping not supported")
                return value
            if quant.set_cmd:
                info = self._get_node_info(quant.name)
                if info.get("function", ""):
                    quant.setValue(value)
                    self.call_toolkit_function(
                        info["function"],
                        (
                            self._quant_to_path(quant.name)
                            / info.get("function_path", ".")
                        ).resolve(),
                    )
                    return value
                return self._set_value_toolkit(
                    quant, value, options=options, wait_for=info.get("wait_for", False)
                )
            return value
        finally:
            if self._transaction.is_running() and self.isFinalCall(options):
                self._transaction.end()

    def performGetValue(self, quant: Quantity, options: t.Dict = {}):
        """Perform the Get Value instrument operation."""
        info = self._get_node_info(quant.name)
        if info.get("function", ""):
            if self.dOp["operation"] != Interface.GET_CFG:
                self.call_toolkit_function(
                    info["function"],
                    (
                        self._quant_to_path(quant.name) / info.get("function_path", ".")
                    ).resolve(),
                )
            return quant.getValue()
        if quant.get_cmd:
            if self.dOp["operation"] == Interface.GET_CFG:
                # use a snapshot for the GET_CFG command
                try:
                    value = self._snapshot.get_value(quant.get_cmd)
                    value = value if value is not None else quant.getValue()
                    return value
                except KeyError:
                    logger.error(f"{quant.get_cmd} not found")
                    return quant.getValue()
            # clear snapshot if GET_CFG is finished
            self._snapshot.clear()
            try:
                value = self._instrument[quant.get_cmd]()
                logger.debug(f"{quant.name}: get {value}")
                return value
            except Exception as error:
                logger.error(error)
        logger.debug(
            f"{quant.name}: does not have a get_cmd and is not part of a function"
        )
        return quant.getValue()

    # def performClose(self, bError: bool = False, options: t.Dict = {}) -> None:
    #     """Perform the close instrument connection operation."""
    #     pass

    # def initSetConfig(self) -> None:
    #     """Run before setting values in Set Config."""
    #     pass

    # def performArm(self, quant_names: str, options: t.Dict = {}) -> None:
    #     """Perform the instrument arm operation"""
    #     pass

    def _get_session(self, data_server_info: t.Dict[str, t.Any]) -> Session:
        """Return a Session to the dataserver.

        One single session to each data server is reused per default in Labber.
        The "shared_session" option in the settings can disable this behavior.

        Args:
            data_server_info: settings info for the Data Server.

        Returns:
            Valid toolkit Session object.
        """
        target_host = data_server_info.get("host", "localhost")
        target_hf2 = data_server_info.get("hf2", False)
        target_port = data_server_info.get("port", 8005 if target_hf2 else 8004)
        logger.info(f"Data Server Session {target_host}:{target_port}")
        if data_server_info.get("shared_session", True):
            for (host, port), session in created_sessions.items():
                if target_host == host and target_port == port:
                    return session
        new_session = Session(target_host, target_port, hf2=target_hf2)
        created_sessions[(target_host, target_port)] = new_session
        return new_session

    def _create_instrument(
        self, instrument_info: t.Dict[str, t.Any]
    ) -> t.Union[Session, DeviceType, ModuleType]:
        """Create a connection through toolkit to the Instrument.

        Instrument in this case means a Labber instrument which can be a
        ZI Device, LabOne module or data server sessions itself.

        Args:
            instrument_info: settings info for the Labber Instrument.

        Returns:
            toolkit object for the specified Instrument.
        """
        base_type = instrument_info.get("base_type", "session")
        if base_type == "session":
            self._base_type = BaseType.SESSION
            logger.info("Created Session Instrument")
            return self._session
        if base_type == "module":
            self._base_type = BaseType.MODULE
            logger.info(
                f"Created Instrument for LabOne Module {instrument_info.get('type','unknown').lower()}"
            )
            try:
                return getattr(self._session.modules, instrument_info["type"].lower())
            except KeyError as error:
                raise RuntimeError(
                    "Settingsfile is specifing a module as instrument but is "
                    'missing the "type" property.'
                ) from error
            except AttributeError as error:
                raise RuntimeError(
                    f"LabOne module with name {instrument_info['type'].lower()}"
                    " does not exist in toolkit."
                )
        self._base_type = BaseType.DEVICE
        logger.info(f"Created Instrument for Device {self.comCfg.getAddressString()}")
        return self._session.connect_device(self.comCfg.getAddressString())

    def _quant_to_path(self, quant_name: str) -> str:
        """Convert Quantity name into its path representation

        Args:
            quant_name: Name of the Quant

        Returns:
            Path (/ seperated string)
        """

        return Path("/" + "/".join(quant_name.split(self._path_seperator)))

    def _get_node_info(self, quant_name: t.Union[str, Path]) -> t.Dict[str, t.Any]:
        """Get the node info for a Quantity

        If there is no Info available the result will be an empty dictionary.

        Args:
            quant_name: Name of the Quant

        Returns:
            Node info.
        """
        node_path = (
            quant_name
            if isinstance(quant_name, Path)
            else self._quant_to_path(quant_name)
        )
        for parent_node, node_info in self._node_info.items():
            if fnmatch.fnmatch(node_path, parent_node):
                return node_info.get("driver", {})
        return {}

    def _set_value_toolkit(
        self,
        quant: Quantity,
        value: t.Any,
        *,
        options: t.Dict = {},
        wait_for: bool = False,
        raise_error: bool = False,
    ) -> None:
        """Set a value through toolkit to a node.

        The function does not raise an Exception but rather logs all errors

        Args:
            quant: Quant of the node to set.
            value: Value.
            options: Labber options for the opperation
            wait_for: Flag if the function should block until the value is set
                on the device.
            raise_error: Flag if the function should raise an error or only log
                it.
        """
        try:
            logger.debug(f"{quant.name}: set {value}")
            self._instrument[quant.set_cmd](value)
            if wait_for and not self._transaction.is_running():
                self._instrument[quant.set_cmd].wait_for_state_change(value)
        except Exception as error:
            logger.error(error)
            if raise_error:
                raise

    @staticmethod
    def _csv_row_to_vector(csv_row: t.List[str]) -> t.Optional[NumpyArray]:
        """Convert a csv row into a numpy array.

        Args:
            csv_row: Parsed CSV row
        Returns:
            Numpy array.
        """
        if not csv_row:
            return None
        datatype = type(eval(csv_row[0]))
        return np.array(csv_row, dtype=datatype.__name__)

    @staticmethod
    def _import_waveforms(
        waves1: Path, waves2: Path = None, markers: Path = None
    ) -> Waveforms:
        """Import Waveforms from CSV files.

        Args:
            waves1: csv for real part waves
            waves2: csv for imag part waves
            marker: csv for markers

        Returns:
            Waveform object.
        """
        wave0_reader = csv.reader(
            waves1.open("r", newline=""), delimiter=",", quotechar="|"
        )
        wave1_reader = repeat([])
        if waves2 and waves2.exists():
            wave1_reader = csv.reader(
                waves2.open("r", newline=""), delimiter=",", quotechar="|"
            )
        marker_reader = repeat([])
        if markers and markers.exists():
            marker_reader = csv.reader(
                markers.open("r", newline=""), delimiter=",", quotechar="|"
            )

        waves = Waveforms()
        for i, row in enumerate(zip(wave0_reader, wave1_reader, marker_reader)):
            if not row[0]:
                continue
            waves[i] = (
                BaseDevice._csv_row_to_vector(row[0]),
                BaseDevice._csv_row_to_vector(row[1]),
                BaseDevice._csv_row_to_vector(row[2]),
            )
        return waves

    def _get_quant_value(self, quant_path: Path) -> t.Any:
        """Get Value from a Quantity.

        The raw value is processed according to the node info.

        Args:
            quant_name: Name of the Quantity

        Returns:
            processed value of the Quantity.
        """
        quant_info = self._get_node_info(quant_path)
        quant_type = quant_info.get("type", "default")
        quant_name = self._path_seperator.join(str(quant_path).split("/")[1:])
        quant_value = self.getValue(quant_name)
        if quant_type == "JSON":
            if str(quant_value) == ".":
                return None
            with open(quant_value, "r") as file:
                return json.loads(file.read())
        if quant_type == "TEXT":
            if str(quant_value) == ".":
                return None
            with open(quant_value, "r") as file:
                return file.read()
        if quant_type == "CSV":
            if str(quant_value) == ".":
                return None
            return self._import_waveforms(quant_value)
        return quant_value

    def _get_toolkit_function(self, path: str) -> t.Callable:
        """Convert a function path into a toolkit function object.

        Args:
            path: Path of the function.

        Returns:
            toolkit function object.
        """
        # get function object
        function = self._instrument
        for name in path.split("/")[1:]:
            if name.isnumeric():
                function = function[int(name)]
            else:
                function = getattr(function, name)
        return function

    def call_toolkit_function(
        self, name: str, path: Path, raise_error: bool = False
    ) -> None:
        """Call an process a toolkit function.

        If this function is called within a transaction the execution is
        delayed if the function allows it (call_type == Bundle).

        Args:
            name: Internal name of the function.
            path: Path of the toolkit function.
        """

        func_info = self._function_info[name]

        if (
            self._transaction.is_running()
            and func_info.get("call_type", "") == "Bundle"
        ):
            self._transaction.add_function(name, path)
            return

        kwargs = {}
        for arg_name, relative_quant_name in func_info.get("Args").items():
            if isinstance(relative_quant_name, list):
                waveform_paths = {}
                for relative_quant_name_el in relative_quant_name:
                    quant_path = (path / relative_quant_name_el).resolve()
                    quant_name = self._path_seperator.join(
                        str(quant_path).split("/")[1:]
                    )
                    path_value = self.getValue(quant_name)
                    waveform_paths[quant_path.stem] = (
                        None if str(path_value) == "." else path_value
                    )
                kwargs[arg_name] = self._import_waveforms(**waveform_paths)
            else:
                quant_name = (path / relative_quant_name).resolve()
                kwargs[arg_name] = self._get_quant_value(quant_name)

        function = self._get_toolkit_function(str(path))
        try:
            return_values = function(**kwargs)
        except Exception as error:
            logger.error(error)
            if raise_error:
                raise
            return

        for relative_quant_name in func_info.get("Returns"):
            quant_path = (path / relative_quant_name).resolve()
            quant_name = self._path_seperator.join(
                    str(quant_path).split("/")[1:]
                )
            info = self._get_node_info(quant_path).get("return_value","")
            try:
                value = eval("return_values" + info)
            except Exception as error:
                logger.error(error)
                value = self.getValue(quant_name)
            try:
                self.setValue(quant_name, value)
            except KeyError as error:
                logger.debug(f"{quant_name} does not exist")
