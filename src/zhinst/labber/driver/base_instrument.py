"""Generic Labber base driver for all drivers from Zurich Instruments."""
import csv
import fnmatch
import json
import logging
import os
import string
import sys
import typing as t
from itertools import repeat
from pathlib import Path

import numpy as np
from BaseDriver import LabberDriver
from InstrumentDriver_Interface import Interface
from zhinst.toolkit import Session, Waveforms
from zhinst.toolkit.driver.devices import DeviceType
from zhinst.toolkit.driver.modules import ModuleType

from zhinst.labber.driver.snapshot_manager import SnapshotManager, TransactionManager

Quantity = t.TypeVar("Quantity")
NumpyArray = t.TypeVar("NumpyArray")

GLOBAL_SETTINGS = Path(__file__).parent / "../resources/settings.json"

created_sessions = {}
logger = logging.getLogger(__name__)


class BaseDevice(LabberDriver):
    """Generic Labber base driver for all drivers from Zurich Instruments.

    The driver is based on zhinst-toolkit. It works for devices, LabOne modules
    and a session.

    It requires both local and global settings. The global settings are shared
    with the generator script and contains information about special node
    handling and function calls. The local settings are passed as an argument
    and contain instrument/user specific information. The following fields are
    supported/required:

    * data_server (information about the data server session)
        * host: Address of the data server. (default = "localhost")
        * port: Port of the data server. (default = 8004)
        * hf2: Flag if the data server is for hf2 device. (default = false)
        * shared_session: Flag if the session should be shared with Labber.
            Warning: If set to false some feature may no longer be supported.
            (default = true)
    * instrument: (Labber instrument specific information)
        * base_type: Base type of the instrument. (device, module, session)
        * type: Type of the module. Not used for session.
            module => name of the module in toolkit
            device => device type
    },
    * logger_level: Logging level of python logger. If not specified the global
        settings are used.
    * logger_path: Optional logger path where the logging information will be
        stored (in addition to the std output which is always enabled).

    The driver will accept all arguments and forward them to the
    ``LabberDriver`` directly.

    Args:
        settings: local settings
    """

    def __init__(self, *args, settings=t.Dict, **kwargs):
        super().__init__(*args, **kwargs)
        self._session = None
        self._instrument = None
        self._transaction = None
        self._snapshot = None
        self._instrument_settings = settings
        self._device_type = settings["instrument"].get("type", "")
        instrument_type = settings["instrument"].get("base_type", "")
        log_level = settings.get("logger_level", None)

        # read information from global settings file
        with GLOBAL_SETTINGS.open("r") as file:
            node_info = json.loads(file.read())
            self._node_info = node_info["common"].get("quants", {})
            if self._device_type:
                if instrument_type == "device":
                    dev_type = self._device_type.split("_")[0].rstrip(string.digits)
                    device_info = node_info.get(dev_type).get("quants", {})
                else:
                    device_info = node_info.get(self._device_type).get("quants", {})
                self._node_info = {**self._node_info, **device_info}
            self._function_info = node_info.get("functions", {})
            self._path_seperator = node_info["misc"]["labberDelimiter"]
            # use global log level if no local one is defined
            log_level = node_info["misc"]["LogLevel"] if not log_level else log_level

        # Set up logger
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s: %(message)s",
            datefmt="%a, %d %b %Y %H:%M:%S",
        )
        # always log to std out
        std_out_handler = logging.StreamHandler(sys.stdout)
        std_out_handler.setFormatter(formatter)
        logger.addHandler(std_out_handler)
        # log to path if specified
        if "logger_path" in self._instrument_settings:
            file_handler = logging.FileHandler(self._instrument_settings["logger_path"])
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        logger.setLevel(log_level)
        logger.debug("PID: %d", os.getpid())

        # Set up node to quant map
        self._node_quant_map = {
            self._quant_to_path(quant): quant for quant in self.dQuantities
        }

    def performOpen(self, options: t.Dict = {}) -> None:
        """Perform the operation of opening the instrument connection.

        Args:
            options: Additional information provided by Labber.
        """
        self._session = self._get_session(
            self._instrument_settings["data_server"],
            self._instrument_settings["instrument"].get("base_type", "DataServer"),
        )
        self._instrument = self._create_instrument(
            self._instrument_settings["instrument"]
        )
        self._snapshot = SnapshotManager(self._instrument.root)
        self._transaction = TransactionManager(self._instrument, self)

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

        TODO special treatment for sweeping required?

        Args:
            quant: Quantity that should be set.
            value: Value to be set.
            sweepRate: Sweep rate. 0 if no sweep should be performed.
            options: Additional information provided by Labber.
                {
                    'operation':1
                    'quant':'QA Channel 1 - Trigger Level'
                    'value':0.501
                    'sweep_rate':0.0
                    'wait_for_sweep':True
                    'delay':693483.64
                }


        Returns:
            Value that was set. (If None Labber will automatically use the input
            value instead)
        """
        # Start transaction if necessary
        if "call_no" in options and not self._transaction.is_running():
            self._transaction.start()
        try:
            node_info = self._get_node_info(quant.name)
            if "call_no" in options and not node_info.get("transaction", True):
                logger.info(
                    "%s: Transaction is not supported for this node. "
                    "Please set value manually.",
                    quant.name,
                )
                return value
            if node_info.get("function", ""):
                quant.setValue(False if node_info.get("trigger", False) else value)
                function_path = node_info.get("function_path", ".")
                function_path = self._quant_to_path(quant.name) / function_path
                self.call_toolkit_function(
                    node_info["function"],
                    function_path.resolve(),
                )
                return False if node_info.get("trigger", False) else value
            if not quant.set_cmd:
                logger.info("%s: is read only and will not be set.", quant.name)
                return self.performGetValue(quant)
            return self._set_value_toolkit(
                quant, value, wait_for=node_info.get("wait_for", False)
            )
        # Stop transaction if necessary (should be ended regardless of any exceptions)
        finally:
            if self._transaction.is_running() and self.isFinalCall(options):
                try:
                    self._transaction.end()
                except Exception as error:
                    logger.error("Error during ending a transaction: %s", error)

    def performGetValue(self, quant: Quantity, options: t.Dict = {}) -> t.Any:
        """Perform the Get Value instrument operation.

        Args:
            quant: Quantity that should be set.
            options: Additional information provided by Labber.
                {
                    'operation':2
                    'quant':'QA Channel 1 - Trigger Level'
                    'delay':693555.843
                }

        Returns:
            New value of the quantity.
        """
        node_info = self._get_node_info(quant.name)
        # Call function. (No function execution during GET_CFG)
        if node_info.get("function", "") and self.dOp["operation"] != Interface.GET_CFG:
            function_path = node_info.get("function_path", ".")
            function_path = self._quant_to_path(quant.name) / function_path
            self.call_toolkit_function(
                node_info["function"],
                function_path.resolve(),
            )
        # Get value from toolkit
        elif quant.get_cmd:
            get_cmd = (
                quant.get_cmd[3:]
                if quant.get_cmd.lower().startswith("zi/")
                else quant.get_cmd
            )
            # use a snapshot for the GET_CFG command
            if self.dOp["operation"] == Interface.GET_CFG:
                value = None
                try:
                    value = self._parse_value(self._snapshot.get_value(get_cmd))
                except KeyError:
                    logger.error("%s not found", get_cmd)
                logger.info("%s: get %s", quant.name, value)
                return value if value is not None else quant.getValue()
            # clear snapshot if GET_CFG is finished
            self._snapshot.clear()
            try:
                value = self._parse_value(
                    self._instrument[get_cmd](parse=False, enum=False)
                )
                logger.info("%s: get %s", quant.name, value)
                return value if value is not None else quant.getValue()
            except Exception as error:
                logger.error(error)
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

    def _parse_value(self, value: t.Any) -> t.Any:
        """Parse the value received from toolkit for a node.

        Args:
            value: Received value

        Returns:
            parsed value
        """
        if isinstance(value, dict):
            if "x" in value and "y" in value:
                return complex(value["x"], value["y"])
            if "dio" in value:
                return value["dio"][0]
            logger.error("Unknown data received %s", value)
        return value

    def _get_session(
        self, data_server_info: t.Dict[str, t.Any], base_type: str
    ) -> Session:
        """Return a Session to the dataserver.

        One single session to each data server is reused per default in Labber.
        The "shared_session" option in the settings can disable this behavior.

        Args:
            data_server_info: settings info for the Data Server.
            base_type: BaseType of the Labber Instruement.

        Returns:
            Valid toolkit Session object.
        """
        target_host = data_server_info.get("host", "localhost")
        target_hf2 = data_server_info.get("hf2", False)
        target_port = data_server_info.get("port", 8005 if target_hf2 else 8004)
        # Use the Instrument Address if the Instrument is a DataSever
        if base_type == "DataServer":
            raw_server = self.comCfg.getAddressString()
            split_raw_server = raw_server.split(":")
            target_host = split_raw_server[0]
            if len(split_raw_server) > 1:
                target_port = int(split_raw_server[1])
        logger.info("Data Server Session %s:%s", target_host, target_port)
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
        if base_type in ["session", "DataServer"]:
            logger.info("Created Session Instrument")
            return self._session
        if base_type == "module":
            logger.info(
                "Created Instrument for LabOne Module %s for Device %s",
                instrument_info.get("type", "unknown").lower(),
                self.comCfg.getAddressString(),
            )
            try:
                module = getattr(self._session.modules, instrument_info["type"].lower())
                self._session.connect_device(self.comCfg.getAddressString())
                module.device(self.comCfg.getAddressString())
                return module
            except KeyError as error:
                raise RuntimeError(
                    "Settingsfile is specifing a module as instrument but is "
                    'missing the "type" property.'
                ) from error
            except AttributeError as error:
                raise RuntimeError(
                    f"LabOne module with name {instrument_info['type'].lower()}"
                    " does not exist in toolkit."
                ) from error
        logger.info("Created Instrument for Device %s", self.comCfg.getAddressString())
        return self._session.connect_device(self.comCfg.getAddressString())

    def _quant_to_path(self, quant_name: str) -> Path:
        """Convert Quantity name into its path representation

        Args:
            quant_name: Name of the Quant

        Returns:
            Path (/ seperated string)
        """

        return Path(
            "/" + "/".join(quant_name.lower().split(self._path_seperator))
        ).resolve()

    def _path_to_quant(self, quant_path: Path) -> str:
        try:
            return self._node_quant_map[quant_path.resolve()]
        except KeyError:
            name = self._path_seperator.join(quant_path.parts[1:])
            self._node_quant_map[name] = name
            return name

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
        node_path = "/" + "/".join(node_path.parts[1:]).lower()
        for parent_node, node_info in self._node_info.items():
            if fnmatch.fnmatch(node_path, parent_node):
                return node_info.get("driver", {})
        return {}

    def _set_value_toolkit(
        self,
        quant: Quantity,
        value: t.Any,
        *,
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
            logger.info("%s: set %s", quant.name, value)
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
            processed value of the Quantity, do call empty
        """
        quant_info = self._get_node_info(quant_path)
        quant_type = quant_info.get("type", "default")
        quant_name = self._path_to_quant(quant_path)
        quant_value = self.getValue(quant_name)
        call_empty = quant_info.get("call_empty", True)
        if quant_type == "JSON":
            try:
                with open(Path(quant_value), "r") as file:
                    return json.loads(file.read()), call_empty
            except IOError as error:
                logger.error(error)
                return {}, call_empty
        if quant_type == "TEXT":
            try:
                with open(Path(quant_value), "r") as file:
                    return file.read(), call_empty
            except IOError as error:
                logger.error(error)
                return "", call_empty
        if quant_type == "CSV":
            try:
                return self._import_waveforms(Path(quant_value)), call_empty
            except IOError as error:
                logger.error(error)
                return Waveforms(), call_empty
        return quant_value, call_empty

    def _get_toolkit_function(self, path_list: t.List[str]) -> t.Callable:
        """Convert a function path into a toolkit function object.

        Args:
            path: Path of the function.

        Returns:
            toolkit function object.
        """
        # get function object
        function = self._instrument
        for name in path_list:
            if name.isnumeric():
                function = function[int(name)]
            else:
                function = getattr(function, name.lower())
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

        if self.dOp["operation"] == Interface.SET_CFG and not func_info.get(
            "is_setting", True
        ):
            return

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
                    quant_name = self._path_to_quant(quant_path)
                    path_value = self.getValue(quant_name)
                    waveform_paths[quant_path.stem] = (
                        None if str(path_value) in [".", ""] else Path(path_value)
                    )
                try:
                    kwargs[arg_name] = self._import_waveforms(**waveform_paths)
                except IOError as error:
                    logger.error(error)
                    kwargs[arg_name] = Waveforms()
            else:
                quant_name = (path / relative_quant_name).resolve()
                kwargs[arg_name], call_empty = self._get_quant_value(quant_name)
                if not call_empty and not kwargs[arg_name]:
                    logger.warning(
                        "%s: %s must not be empty",
                        self._path_to_quant(path),
                        quant_name,
                    )
                    return

        function = self._get_toolkit_function(path.parts[1:])

        logger.info("%s: call with %s", self._path_to_quant(path), kwargs)
        try:
            return_values = function(**kwargs)
        except Exception as error:
            logger.error(error)
            if raise_error:
                raise
            return
        logger.info("%s: returned %s", self._path_to_quant(path), return_values)

        for relative_quant_name in func_info.get("Returns"):
            quant_path = (path / relative_quant_name).resolve()
            quant_name = self._path_to_quant(quant_path)
            info = self._get_node_info(quant_path).get("return_value", "")
            try:
                value = eval("return_values" + info)
            except Exception as error:
                logger.error(error)
                value = self.getValue(quant_name)
            try:
                self.setValue(quant_name, value)
            except KeyError:
                logger.debug("%s does not exist", quant_name)
