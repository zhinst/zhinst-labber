import time
from queue import Empty
from operator import itemgetter
import numpy as np
import time
import traceback
from math import inf

from InstrumentDriver_Interface import Interface

timer = time.perf_counter


class InstrumentQuantity(object):
    """ "Represents a quantity that can be written to and/or read from
    an instrument."""

    BOOLEAN = 1
    BOTH = 0
    BUTTON = 8
    COMBO = 2
    COMPLEX = 5
    DOUBLE = 0
    NONE = 3
    PATH = 7
    READ = 1
    STRING = 3
    VECTOR = 4
    VECTOR_COMPLEX = 6
    WRITE = 2

    def __init__(
        self,
        name="",
        unit="",
        datatype=0,
        def_value=0.0,
        combo_defs=[],
        cmd_def=[],
        low_lim=-inf,
        high_lim=inf,
        group=None,
        enabled=True,
        state_quant=None,
        state_value=None,
        permission=0,
        get_cmd="",
        set_cmd="",
        sweep_cmd=None,
        sweep_res=None,
        stop_cmd=None,
        sweep_check_cmd=None,
        x_name="Time",
        x_unit="s",
        model_value=[],
        option_value=[],
        section="",
        tooltip="",
        show_in_measurement_dlg=False,
        label=None,
        sweep_rate=0.0,
        sweep_minute=False,
        sweep_rate_low=0.0,
        sweep_rate_high=inf,
    ):
        pass

    def getCmdStringFromValue(self, value=None, dVisa={}):
        pass

    def getDictWithCfg(self):
        """returns the quantity config as a dict"""

    def getLabelWithUnit(self, bUseFullName=True):
        """Return a string with name and unit in the form: Voltage [V]"""

    def getSweepRate(self):
        """Return current sweep rate, taken from internal value"""

    def getTimeStatistics(self):
        """Return tuple (time per call, n of calls) with timing statistics"""

    def getTimeStatisticsStr(self):
        """Return tuple (time per call, n of calls) with timing stats, as str"""

    def getValue(self):
        """Return current control value, taken from internal value"""

    def getValueArray(self):
        """Return current value as numpy array, taken from internal value"""

    def getValueFromCmdString(self, sValue, dVisa={}):
        """Inspect a string coming from an instrument and extract a value"""

    def getValueIndex(self, value=None):
        """Return current control value as a number, taken internally"""

    def getValueString(self, value=None, unit=None, digits=4):
        """Return current control value as a string"""

    def getValueStringWithIndex(self, value=None):
        """Return current control value as a string including the index"""

    def isActive(self, lActive, instrCfg=None):
        """Check if quantity is active, given the state of the quantities given in the lActive input list."""

    def isComplex(self):
        """Return true if quanity value is represented by a complex number"""

    def isPermissionNone(self):
        """Check the instrument read/write permission state of the quantity"""

    def isPermissionRead(self):
        """Check the instrument read/write permission state of the quantity"""

    def isPermissionReadWrite(self):
        """Check the instrument read/write permission state of the quantity"""

    def isPermissionWrite(self):
        """Check the instrument read/write permission state of the quantity"""

    def isReadable(self):
        """Check if quantity can be read"""

    def isSweepable(self):
        """Check if the quantitiy is sweepable"""

    def isValueChangedAfterSet(self):
        """Return true if valid changed after last set value call"""

    def isVector(self):
        """Return true if quanity is a vector"""

    def isWritable(self):
        """Check if quantity can be set"""

    def limits(self):
        """returns a list with the limits"""

    def resetTimeStatistics(self):
        """Reset timing statistics"""

    def setValue(self, value, rate=None):
        """Set control value, and update GUI control, if it exists. The function
        returns the same value, potentially typecast into the correct format"""

    def updateTimeStatistics(self, dt, bSet=False):
        """Update counters for timing statistics for setting value"""

    def getTraceDict(
        value=[],
        x0=0.0,
        dx=1.0,
        bCopy=False,
        x1=None,
        x=None,
        logX=False,
        t0=None,
        dt=None,
    ):
        """Format the value into a trace dict, with vector in numpy format"""

    def getTraceXY(dTrace, bVsN=False):
        """Get (x,y)-traces (1D vectors) from trace dictionary"""


class InstrumentComCfg(object):
    """Class for instruments communication configuration."""

    ASRL = "serial"
    DO_NOTHING = "Do nothing"
    GET_CONFIG = "Get config"
    GPIP = "GPIB"
    INTERFACE_OPTS = ["GPIB", "TCPIP", "USB", "PXI", "Serial", "VISA", "Other", "None"]
    NONE = "None"
    OTHER = "Other"
    PXI = "PXI"
    SET_CONFIG = "Set config"
    STARTUP_OPTS = ["Set config", "Get config", "Do nothing"]
    TCPIP = "TCPIP"
    USB = "USB"
    VISA = "VISA"

    def __init__(self, dComCfg):
        self._dComCFG = dComCfg
        self.address = "DEV1234"
        self.bNoCom = False
        self.dAdvanced = "Not implemented"
        self.lAdvanced = "Not implemented"
        self.interface = "Other"
        self.lock = False
        self.name = "Test"
        self.server = "localhost"
        self.show_advanced = False
        self.startup = "Do nothing"

    def getAddressString(self):
        """Return a human-readable string describing the address"""

    def getComCfgDict(self):
        """Return a dict with the settings given by the GUI controls"""

    def getServer(self):
        """Return the server name, default to localhost if no name is given"""

    def isEqual(self, comCfg, bCheckServer=False):
        """Check if two ComConfigs are equal. Configs are considered equal if
        name or address are the same"""

    def setAdvancedValue(self, sQuant, value):
        """Set the value of a advanced setting"""

    def setNoCommunication(self, bNoCom):
        """For instruments with no communication"""

    def getDefaultConfigDict():
        """Define the default config"""

    def getNamesAndDatatypesForHDf5():
        """Create lists of names, python datatype and hdf5 datatypes"""

    def updateServerList(lServer):
        """Update internal server list set for combo box option"""


class InstrumentCfg(object):
    """Complete definition of an instrument, including a comCfg object."""

    def __init__(self, comCfg, dInstrCfg):
        self.comCfg = comCfg
        self.dInstrCfg = dInstrCfg  # content of ini file as dict
        self.dQuantReplace = {}
        self.dQuantity = (
            {}
        )  # dict of each quantity to its object 'Preset - Factory Reset':<InstrumentConfig.InstrumentQuantity object at 0x000001F63F9AEF60>
        self.fUpgradeDriverCfg = None
        self.in_server = False
        self.instrCfgCtrl = None
        self.lIni = []  # ?
        self.lKeys = []  # list of all quantities
        self.lOption = []
        self.oldVersion = None
        self.sModel = "SHFQA4"

    def addQuantity(self, cfg):
        """Add a quantity to the instument driver.
        The cfg variable should be a dict defining at least the
        following keywords:
            name: (string)
            datatype: DOUBLE (possible types defined in InstrumentQuantity)
        and optionally defining these keywords:
            unit: (string)
            def_value: default value, type depending on datatype
            combo_defs: list of string containing combo box labels
            low_lim: lowest allowable value
            high_lim: highest allowable
            group: name of group containing similar quantities
            enabled: default enabled state
            state_quant: quantity setting availibility of this quantity
            state_value: list of state values for which this quantity is active
            permission: access to instrument, options are both/read/write/none"""

    def getActiveQuantities(self, bOnlyDefaultShow=False):
        """Return a list with all quantities that are active in the
        current instrument state. The quantities are returned in insertion
        order."""

    def getActiveQuantitiesByGroup(self):
        """Return (lGroup, dQuant[group]) with active groups and quantities"""

    def getActiveQuantitiesString(self, bWithUnit=False):
        """Return a list of strings with all quantities that are active in the
        current instrument state. The quantities are returned in insertion
        order."""

    def getBaseName(self, bWithAddress=False):
        """Return a string with the base name, for making channels unique"""

    def getControlGroups(self, lQuantity):
        """Find and return a list of strings with all groups in the quants"""

    def getControlSections(self, lQuant=None):
        """Find and return a list of strings with all sections in the items"""

    def getCopy(self, reload_definition=False):
        """Create a copy of the current instrCfg, removing any GUI references"""

    def getHardwareAndComCfgDict(self):
        """Return hardware name and ComCfg dict, for talking to server"""

    def getHardwareName(self, bWithAddress=False, bWithName=False):
        """Return a string with the name of the controlled hardware"""

    def getIdString(self):
        """Return a unique ID string representing the instrument"""

    def getInstrCfgDict(self):
        pass

    def getItemsBySection(self, bOnlyActive=False):
        """Return (lSection, dItem[section]) with active section and items"""

    def getOptionsDict(self):
        """Return a dict with current instrument option settings"""

    def getQuantitiesInSetOrder(self, bReturnAll=False):
        """Return a list with all quantites that are valid in the
        current instrument state. The quantities are sorted by permission
        group, in order:
            {none, write, read, both}.
        Within each subgroup, the quantities are returned in insertion order."""

    def getQuantitiesInsertOrder(self):
        pass

    def getQuantity(self, name, bConvertOldVersion=False):
        """Return the quantitiy defined by name"""

    def getQuantityNames(self):
        """Return a list of strings with all quantities, in insertion order"""

    def getScriptForUpgradingCfg(self):
        """Look for a user-defined function for updating old versions of the
        driver"""

    def getValuesDict(
        self,
        bOnlyActive=True,
        bIncludeReadOnly=True,
        bIncludeVector=True,
        strip_vector_values=False,
    ):
        """Return a dict with quantity name and values of all active quants in
        the current instrument state."""

    def getVectorQuantities(self, bOnlyActive=True, bRead=True, bWrite=True):
        """Return a list with all quantities that are active in the
        current instrument state and return vectors."""

    def getVersion(self):
        """Return a string with the name of the controlled hardware"""

    def get_instrument_config_as_dict(self, include_id=False):
        """Get instruments configuration as a python dictionary"""

    def isController(self):
        """Return True if instrument is a controller"""

    def isEqual(self, sHardware, comCfg, bCheckServer=False):
        """Compare the instr described by hardware and ComCfg and
        check if is equal to self. Configs are considered equal if hardware
        and ComCfg name or address are the same."""

    def isSignalAnalyzer(self):
        """Return True if instrument is a signal analyzer"""

    def isSignalGenerator(self):
        """Return True if instrument is a signal generator"""

    def runScriptForUpgradingCfg(self, dValue={}, dOption=[]):
        """Run user-defined script many times until we get latest version"""

    def setInstalledOptions(self, lOption):
        """Convenience function for setting instrument installed options"""

    def setModel(self, sModel):
        """Convenience function for setting instrument model string"""

    def setOptionsDict(self, dOption):
        """Set installed options and update control, if given"""

    def setValuesDict(self, dValue):
        """Update the quantities with the values in the (name,value) dict"""

    def supportArm(self):
        """Check if instrument supports arming"""

    def supportHardwareLoop(self):
        """Check if instrument supports hardware loop mode"""

    def update_controller_signals(self, instruments):
        """Update list of possible signals for controllers"""

    def createHDF5Entry_List(hdfRef, lInstrCfg):
        pass

    def createInstrListFromHdf5(
        hdfRef, bShowError=False, bViewOnly=False, in_server=False, raise_error=False
    ):
        pass

    def create_instrument_list_from_dict(
        configs, reload_definitions=False, show_error_dlg=False, raise_error=False
    ):
        """Create list of instruments from config in list of dict"""

    def get_list_of_drivers(show_error_dlg=False, include_optimizer=False):
        """Reload driver definitions and store in class variable"""

    def reload_driver(name):
        """Reload driver definition for given driver name"""

    def show_error_dlg_missing_driver(hardware, error):
        """Show error message dialog if failing to load driver def file"""

    def updateHDF5InstrValues_List(hdfRef, lInstrCfg):
        """Static method for updating instrCfg values in a Hdf5 file"""


class Error(Exception):
    """Base error class for Labber drivers"""

    pass


class VisaLibraryError(Error):
    pass


class InstrStateError(Error):
    """Error raised if instrument driver is in the wrong state"""

    def __init__(self, operation, sHardware, message="", sQuant=""):
        self.operation = operation
        self.name = sHardware
        self.message = message
        self.sQuant = sQuant

    def __str__(self):
        sMsg = (
            "An error occurred when performing the following operation:\n"
            + "%s\n\nInstrument: %s"
        ) % (Interface.OP_NAMES[self.operation], self.name)
        if self.sQuant != "":
            sMsg += "\nQuantity: %s" % self.sQuant
        if self.message != "":
            sMsg += "\n\nError message:\n" + self.message
        return sMsg


class LabberDriver(object):
    """Base class for Labber drivers"""

    def __init__(
        self,
        dInstrCfg=None,
        dComCfg=None,
        dValues=None,
        dOption=None,
        dPrefs={},
        queueIn=None,
        queueOut=None,
        logger=None,
    ):
        """Create an instrument driver with settings given by the dicts"""
        super(LabberDriver, self).__init__()
        # make sure controller input/outputs are string, not combo
        # dInstrCfg = make_controller_signal_str(dInstrCfg)
        # save references to local variables
        self.dInstrCfg = dInstrCfg
        self.dComCfg = dComCfg
        self.dPrefs = dPrefs
        self.logger = logger
        # store queue objects
        self.queueIn = queueIn
        sel = Interface(queueIn, queueOut, from_driver=True)
        self.lOp = []
        # create local config objects
        self.comCfg = InstrumentComCfg(dComCfg)
        self.instrCfg = InstrumentCfg(comCfg=self.comCfg, dInstrCfg=dInstrCfg)
        self.instrCfg.setOptionsDict(dOption)
        self.instrCfg.setValuesDict(dValues)
        # time to wait between sweep checks
        self.WAIT_CHECK_SWEEP = 0# TODO ZHINST: removed for testingself.dPrefs["Interval for checking swept instruments"]
        # create a dictionary with all quantities for easy searching (key=name)
        self.dQuantities = dict()
        # TODO ZHINST: removed for testing
        # for quant in self.instrCfg.getQuantitiesInsertOrder():
        #     self.dQuantities[quant.name] = quant
        # create string describing worker name, type and address
        sName = "TestInstrument"# TODO ZHINST: removed for testingself.dInstrCfg["name"]
        self.sAddress = "DEV1234"# TODO ZHINST: removed for testing
        self.sName = "%s - %s" % (sName, self.sAddress)
        # variable signalling that the event loop has been stopped
        self.bStopped = False
        self.bClosed = False
        self.bError = False
        self.bAbortOperation = False
        # keep track if config has been updated
        self.bCfgUpdated = True
        # value from dialog
        self.valueDialog = None

    #        # log list of modules, for bug testing
    #        import sys
    #        b=sys.modules.keys()
    #        for a in sorted(list(b)):
    #            self.log(str(a))

    def mainLoop(self):
        """Main loop of the driver"""
        # keep looping as long as the driver is open
        while not self.bClosed:
            # perform operation, or wait for new ones
            if len(self.lOp) == 0:
                # wait until new operation appears
                self.getOperationsFromCaller(wait=True)
            else:
                # operation available, check if delayed
                delay = self.lOp[0]["delay"] - time.monotonic()
                if delay > 0:
                    # operation available, but should be delayed => keep waiting
                    self.getOperationsFromCaller(wait=True, timeout=delay)
                else:
                    # no need to wait, get operation to perform
                    dOp = self.lOp.pop(0)
                    callId = dOp.pop("call_id")
                    # perform operation
                    self.processOperation(dOp, callId)

    def getOperationsFromCaller(self, wait=True, timeout=None):
        """Read operations from caller queue and store in internal list"""
        # keep getting operation until queue is empty
        while wait or (not self.queueIn.empty()):
            # get operation, may block if first call and waiting
            try:
                dOp = self.queueIn.get(block=True, timeout=timeout)
            except Empty:
                # no object returned after timeout time, just return
                return
            # clear wait flag after first call
            wait = False
            timeout = None
            # check if operation is new value from user dialog
            if dOp["operation"] == Interface.VALUE_FROM_USER:
                self.valueDialog = dOp["value"]
                # just continue if new dialog value, no new operation to add
                continue
            # check if operation will stop/abort running operations
            if dOp["operation"] == Interface.ABORT_OPERATION:
                self.bAbortOperation = True
            if dOp["operation"] == Interface.FORCE_CLOSE:
                self.bStopped = True
            # add to list of delayed operations
            self.lOp.append(dOp)
            # sort operations by time
            self.lOp.sort(key=itemgetter("delay"))
            # add info to log
            nOp = self.getNumberOfOpsInQueue()
            self.log(
                "%s: Operation added, # of ops in queue: %d"
                % (self.getOpDescription(dOp), nOp),
                level=10,
            )

    def getNumberOfOpsInQueue(self):
        """Return the number of non-performed operations in the queue"""
        return len(self.lOp)

    def clearOperationQueue(self):
        """Remove all operations from the queue"""
        self.lOp = []

    def _callback_UserClosed(self, value):
        # callback close, save dialog value
        self.newValue = value

    def getValueFromUserDialog(
        self, value=None, text="Enter value:", title="User input"
    ):
        """Show dialog and wait for user response"""
        # clear old user dialog value
        self.valueDialog = None
        # send request to GUI
        self.interface.requestValueFromUser(value, text, title)
        # block until stopped or user dialog returns
        while self.valueDialog is None:
            # sleep for a while
            self.wait(0.05)
            # keep checking for data from caller
            self.getOperationsFromCaller(wait=False)
            if self.isStopped():
                return value
        # finally, return new value
        return self.valueDialog

    def getValue(self, sQuant):
        """Helper function for getting values of other quantities"""
        quant = self.instrCfg.getQuantity(sQuant)
        return quant.getValue()

    def setValue(self, sQuant, value, sweepRate=None):
        """Helper function for setting value of other quantity"""
        quant = self.instrCfg.getQuantity(sQuant)
        # convert to rate / sec
        if quant.sweep_minute and sweepRate is not None:
            sweepRate /= 60.0
        # if vector, create copy of data to avoid unwanted confusion
        if quant.isVector():
            value = quant.getTraceDict(value, bCopy=True)
        quant.setValue(value, sweepRate)
        # operation ok, emit success signal
        self.interface.reportSet(quant, value, sweepRate, None)
        # self.emit(SIGNAL("WorkerSet"), sQuant, value, sweepRate, None) #self)
        return value

    def getValueArray(self, sQuant):
        """Helper function for getting values of other quantities"""
        quant = self.instrCfg.getQuantity(sQuant)
        return quant.getValueArray()

    def getValueIndex(self, sQuant):
        """Helper function for getting values of other quantities"""
        quant = self.instrCfg.getQuantity(sQuant)
        return quant.getValueIndex()

    def getCmdStringFromValue(self, sQuant):
        """Helper function for getting cmd string of other quantities"""
        # get quants with combo options
        quant = self.instrCfg.getQuantity(sQuant)
        return quant.getCmdStringFromValue()

    def getModel(self):
        """Get model string"""
        dCfg = self.instrCfg.getOptionsDict()
        return dCfg["model"]

    def getQuantity(self, sQuant):
        """Get other quantity"""
        return self.instrCfg.getQuantity(sQuant)

    def getOptions(self):
        """Get list of strings describing installed options"""
        dCfg = self.instrCfg.getOptionsDict()
        return dCfg["options"]

    def getName(self):
        """Return name of instrument, as defined in the user-interface dialog"""
        return self.dComCfg["name"]

    def getInterface(self):
        """Return interface string for instrument, as defined in the dialog"""
        return self.dComCfg["interface"]

    def getAddress(self):
        """Return address string for instrument, as defined in the dialog"""
        return self.dComCfg["address"]

    def getCommunicationCfg(self):
        """Return communication configuration as a dictionary"""
        return self.dComCfg.copy()

    def setModel(self, validName):
        """Set model string"""
        self.instrCfg.setModel(validName)

    def setInstalledOptions(self, lOption):
        """Set list of installed options"""
        self.instrCfg.setInstalledOptions(lOption)

    def readValueFromOther(self, sQuant, options={}):
        """Read value of other quantity from instrument"""
        quant = self.instrCfg.getQuantity(sQuant)
        # call perfromGetValue for this quantity
        value = self.performGetValue(quant, options=options)
        quant.setValue(value)
        # check if value changed, if so mark that config is updated
        if quant.isPermissionReadWrite() and quant.isValueChangedAfterSet():
            self.bCfgUpdated = True
        # if vector, create copy of data to avoid issues if changing array
        if quant.isVector():
            value = quant.getTraceDict(value, bCopy=True)
        # operation ok, emit success signal
        self.interface.reportGet(quant, value, None)
        # self.emit(SIGNAL("WorkerGet"), sQuant, value, None) # self)
        return value

    def sendValueToOther(self, sQuant, value, sweepRate=0.0, options={}):
        """Send value of other quantity to instrument"""
        quant = self.instrCfg.getQuantity(sQuant)
        # convert to rate / sec
        if quant.sweep_minute:
            sweepRate /= 60.0
        # copy vector, to avoid confusion with shared data
        if quant.isVector():
            value = quant.getTraceDict(value, bCopy=True)
        value = self._performSetValue(
            quant, value, sweepRate, bWaitForSweepInFunction=True, options=options
        )
        quant.setValue(value, sweepRate)
        # mark that config is updated
        if quant.isValueChangedAfterSet():
            self.bCfgUpdated = True
        # operation ok, emit success signal
        self.interface.reportSet(quant, value, sweepRate, None)
        # self.emit(SIGNAL("WorkerSet"), sQuant, value, sweepRate, None) #self)
        return value

    def getOpDescription(self, dOp):
        """Create a string describing the operation, for logging purposes"""
        # create string depending on operation
        if dOp["operation"] == Interface.SET:
            quant = self.dQuantities[dOp["quant"]]
            sOp = "Set value: %s = %s" % (
                dOp["quant"],
                quant.getValueString(dOp["value"]),
            )
        elif dOp["operation"] == Interface.GET:
            sOp = "Get value: %s" % dOp["quant"]
        else:
            # get generic operation descriptor
            sOp = Interface.OP_NAMES[dOp["operation"]]
        return self.sName + ": " + sOp

    def isStopped(self):
        """Check if current operation has been told to stop"""
        # first check interface for operations, ignore resource errors
        try:
            self.getOperationsFromCaller(wait=False)
        except:
            pass
        # with QMutexLocker(self.mutexOp):
        return self.bStopped or self.bAbortOperation

    def reportProcessPerformed(self, dOp, bAbort=False):
        """Keep track of number of processes and emit WorkerFinished signal
        if no more processes in the queue"""
        # with QMutexLocker(self.mutexOp):
        nOp = self.getNumberOfOpsInQueue()
        # add info to log
        if bAbort:
            self.log(
                "%s: Driver aborted, # of ops in queue: %d"
                % (self.getOpDescription(dOp), nOp),
                level=15,
            )
        else:
            self.log(
                "%s: Driver finished in %.0f ms, # of ops in queue: %d"
                % (self.getOpDescription(dOp), 1000 * (timer() - self.timeT0), nOp),
                level=15,
            )
        # if no more operations in queue, emit inactive signal
        if nOp == 0:
            # emit final signal
            self.interface.reportInactive(self.bClosed)
            # self.emit(SIGNAL("WorkerInactive"), self.bClosed)
        # remove callId
        self.callId = None
        self.dOp = None

    def processOperation(self, dOp, callId):
        """Processes the operation defined in the dict dOp, checking if the
        worker has been stopped and emitting an error signal on failure."""
        # store callId for report purposes
        self.callId = callId
        self.dOp = dOp
        # add info to log
        self.log("%s: Driver started" % self.getOpDescription(dOp), level=15)
        # store start time
        self.timeT0 = timer()
        # check if stopped, if so don't run anything except the abort or close
        if self.isStopped() and dOp["operation"] not in (
            Interface.ABORT_OPERATION,
            Interface.FORCE_CLOSE,
            Interface.CLOSE,
        ):
            # run the post-process function to update the number of processes
            self.reportProcessPerformed(dOp, bAbort=True)
        else:
            # not stopped, resume normal call
            try:
                # try to perform the given operation
                self.performOperation(dOp, callId)
            except Exception as e:
                # error occurred, close instrument
                self.performControlledClose(dOp)
                # create failure message
                sError = self.errorMessage(dOp, str(e))
                try:
                    # add traceback, if available
                    sTraceBack = "".join(traceback.format_tb(e.__traceback__))
                    #                    sTraceBack = traceback.format_exc()
                    sError += "\n\nUnfiltered error message:\n%s" % sTraceBack
                except Exception:
                    pass
                # add to log
                # self.log('Unfiltered error message: \n%s' % sTraceBack, level=40)
                # emit failure signal
                self.interface.reportError(sError, self.get_call_id())
                # self.emit(SIGNAL("WorkerError"), sError, callId)
                # clear any further operation
                self.clearOperationQueue()
            finally:
                # run the post-process function to update the number of processes
                self.reportProcessPerformed(dOp)

    def performOperation(self, dOp, callId):
        """Perform the operation defined in the dict dOp"""
        # update extra values, if available in options dictionary
        if "extra_config" in dOp:
            for quant_name, value in dOp["extra_config"].items():
                self.sendValueToOther(quant_name, value)
        # not stopped, resume normal call
        if dOp["operation"] == Interface.OPEN:
            self.performOpen(options=dOp)
            # operation ok, emit success signal to GUI with instrument options
            dOption = self.instrCfg.getOptionsDict()
            self.interface.reportOpen(dOption, callId)
        #
        elif dOp["operation"] == Interface.SET:
            # get quantity and perform set (do not wait for sweeps)
            quant = self.dQuantities[dOp["quant"]]
            value = self._performSetValue(
                quant,
                dOp["value"],
                dOp["sweep_rate"],
                bWaitForSweepInFunction=dOp["wait_for_sweep"],
                options=dOp,
            )
            quant.setValue(value, dOp["sweep_rate"])
            # mark that config is updated
            if quant.isValueChangedAfterSet():
                self.bCfgUpdated = True
            # with multiprocessing, no longer necessary to copy vector
            if quant.isVector():
                value = quant.getTraceDict(value, bCopy=False)
            # emit success
            self.interface.reportSet(
                quant, value, dOp["sweep_rate"], callId, timer() - self.timeT0
            )
            # self.emit(SIGNAL("WorkerSet"), dOp['quant'], value,
            #           dOp['sweep_rate'], callId)
        #
        elif dOp["operation"] == Interface.REPEAT_SET:
            # get quantity and perform rest of repeated-set sequence
            quant = self.dQuantities[dOp["quant"]]
            value = self.performRepeatSet(
                quant, dOp["value"], dOp["sweep_rate"], options=dOp
            )
            quant.setValue(value, dOp["sweep_rate"])
            self.bCfgUpdated = True
            # emit signal, without signalling back to caller
            self.interface.reportSet(quant, value, dOp["sweep_rate"], None)
            # self.emit(SIGNAL("WorkerSet"), dOp['quant'], value, dOp['sweep_rate'], None)
        #
        elif dOp["operation"] == Interface.WAIT_FOR_SWEEP:
            # get parameters
            quant = self.dQuantities[dOp["quant"]]
            value = dOp["value"]
            # start with reading current value
            currValue = self.performGetValue(quant, options=dOp)
            quant.setValue(currValue)
            if quant.isValueChangedAfterSet():
                self.bCfgUpdated = True
            # compare to threshold or final value
            if value is None or value == quant.sweep_target:
                bWait = self.checkIfSweeping(quant, options=dOp)
            else:
                bSweepUp = value < quant.sweep_target
                bWait = (currValue < value) if bSweepUp else (currValue > value)
            # check if sweep has finished/reached a certain value
            if bWait:
                # still waiting, emit current value, then call again
                self.reportCurrentValue(quant, currValue)
                try:
                    self.interface.addOperation(
                        dOp, callId, delay=self.WAIT_CHECK_SWEEP
                    )
                except InstrStateError:
                    # ignore driver state errors, driver was probably closed
                    pass
            else:
                # value reached, emit final signal with original callId
                self.interface.reportWaitForSweep(quant, currValue, callId)
                # self.emit(SIGNAL("WorkerSet"), dOp['quant'], currValue, None, callId)
        #
        elif dOp["operation"] == Interface.ARM:
            # get quantities, perform arm function
            lNames = dOp["lQuant"]
            self.performArm(lNames, options=dOp)
            # operation ok, emit success signal
            self.report_arm_completed()
        #
        elif dOp["operation"] == Interface.GET:
            # get quantity and perform get
            quant = self.dQuantities[dOp["quant"]]
            value = self.performGetValue(quant, options=dOp)
            quant.setValue(value)
            # check if value changed, if so mark that config is updated
            if quant.isPermissionReadWrite() and quant.isValueChangedAfterSet():
                self.bCfgUpdated = True
            # return value from quant, to catch possible conversion
            value = quant.getValue()
            # operation ok, emit success signal
            self.interface.reportGet(quant, value, callId, timer() - self.timeT0)
            # self.emit(SIGNAL("WorkerGet"), dOp['quant'], value, callId)
        #
        elif dOp["operation"] == Interface.SET_CFG:
            # get list of quantities
            lNames = dOp["lQuant"]
            lValues = dOp["lValue"]
            lRate = dOp["lRate"]
            always_update_all = dOp.get("always_update_all", True)
            # create list of quants to set
            lQuantToSet = []
            for n, sQuant in enumerate(lNames):
                # get quantity to set
                quant = self.dQuantities[sQuant]
                # uupdate local value here unless sweeping with local set
                if not (
                    lRate[n] > 0 and self._get_sweep_interval_with_repeat_set(quant) > 0
                ):
                    quant.setValue(lValues[n], lRate[n])
                if quant.isValueChangedAfterSet():
                    self.bCfgUpdated = True
                elif not always_update_all:
                    # value not updated, don't send to hardware
                    continue
                # check permission
                if quant.isPermissionReadWrite() or quant.isPermissionWrite():
                    # add to set list
                    lQuantToSet.append((quant, n))
            # run init case
            if always_update_all:
                self.initSetConfig()
            # do actual set, keep track of call number
            options = dict()
            options["n_calls"] = len(lQuantToSet)
            for callN, (quant, n) in enumerate(lQuantToSet):
                # add option for call number
                options["call_no"] = callN
                # perform set
                newValue = self._performSetValue(
                    quant,
                    lValues[n],
                    lRate[n],
                    bWaitForSweepInFunction=True,
                    options=options,
                )
                # update with the actual set value
                quant.setValue(newValue, lRate[n])
                lValues[n] = newValue
            # run final case
            if always_update_all:
                self.finalSetConfig()
            # operation ok, emit success signal
            self.interface.reportSetCfg(lNames, lValues, lRate, callId)
            # self.emit(SIGNAL("WorkerSetConfig"), lNames, lValues, lRate, callId)
        #
        elif dOp["operation"] == Interface.GET_CFG:
            # get list of quantities to get
            lNames = dOp["lQuant"]
            lAllQuant = []
            for name in lNames:
                lAllQuant.append(self.dQuantities[name])
            # init lists with active quantities/values
            lActiveQuant = []
            lActiveNames = []
            lActiveValues = []
            # go through all quantities and check their active status
            for quant, oldValue in zip(lAllQuant, dOp["lValue"]):
                # if active, get value
                if quant.isActive(lActiveQuant, self.instrCfg):
                    # add to active list
                    lActiveQuant.append(quant)
                    lActiveNames.append(quant.name)
                    # check if quantity is read/writeable
                    if quant.isPermissionReadWrite():
                        # get value
                        value = self.performGetValue(quant)
                        quant.setValue(value)
                        if quant.isValueChangedAfterSet():
                            self.bCfgUpdated = True
                        # update value list
                        lActiveValues.append(value)
                    else:
                        # use old value for these quants
                        lActiveValues.append(oldValue)
            # operation ok, emit success signal
            self.interface.reportGetCfg(lActiveNames, lActiveValues, callId)
            # self.emit(SIGNAL("WorkerGetConfig"), lActiveNames, lActiveValues, callId)
        #
        elif dOp["operation"] == Interface.ABORT_OPERATION:
            # perform abort
            self.performAbortOperation(options=dOp)
            # ok, emit signal
            self.interface.reportAbort(callId)
            # self.emit(SIGNAL("WorkerAbort"), callId)
        #
        elif dOp["operation"] in (Interface.CLOSE, Interface.FORCE_CLOSE):
            # set stopped and closed variables
            # with QMutexLocker(self.mutexOp):
            self.bStopped = True
            self.bClosed = True
            # perform close
            self.performAbortOperation()
            self.performClose(options=dOp)
            # ok, emit signal
            self.interface.reportClose(callId)
            # self.emit(SIGNAL("WorkerClose"), callId)

    def report_arm_completed(self):
        """Send signal to caller telling thar arming has been completed"""
        # makes sure the arm completed signal is only sent once
        if self.dOp["operation"] == Interface.ARM:
            # only send a total of one arm completed signal
            if not self.dOp.get("arm_completed", False):
                self.interface.reportArm(self.callId)
            self.dOp["arm_completed"] = True

    def performAbortOperation(self, options={}):
        """Abort current operation"""
        # clear the abort operation flag
        # with QMutexLocker(self.mutexOp):
        self.bAbortOperation = False
        # stop all sweeping
        for quant in self.dQuantities.values():
            if quant.isSweepable():
                # check if sweeping, if so clear sweep target and stop sweep
                if self.checkIfSweeping(quant):
                    self.stopSweep(quant)

    def performControlledClose(self, dOp):
        """Perform controlled close if an error occurred before"""
        # set stopped and closed variables
        # with QMutexLocker(self.mutexOp):
        self.bStopped = True
        self.bClosed = True
        self.bError = True
        try:
            self.performAbortOperation()
            self.performClose(bError=True, options=dOp)
        except:
            # ignore if more errors occur during closing
            pass

    def errorMessage(self, dOp, sError=""):
        """Create failure message"""
        sInstr = self.dInstrCfg["name"]
        if self.dComCfg["name"] != "":
            sInstr += " (%s)" % self.dComCfg["name"]
        # create first part of string depending on operation
        if dOp["operation"] == Interface.OPEN:
            sMsg = (
                "An error occurred when trying to establish a "
                + "connection with an instrument.\n\n"
                + "Instrument name: %s\nAddress: %s \n\n"
                "Check that the device is connected and powered on."
                % (sInstr, self.sAddress)
            )
        elif dOp["operation"] == Interface.SET:
            quant = self.dQuantities[dOp["quant"]]
            sMsg = (
                "An error occurred when sending a "
                + "value to an instrument.\n\n"
                + "Instrument name: %s \nAddress: %s \n"
                + "Quantity: %s \nValue: %s"
            )
            sMsg = sMsg % (
                sInstr,
                self.sAddress,
                dOp["quant"],
                quant.getValueString(dOp["value"]),
            )
        elif dOp["operation"] == Interface.GET:
            sMsg = (
                "An error occurred when reading a "
                + "value from an instrument.\n\n"
                + "Instrument name: %s\nAddress: %s\nQuantity: %s"
                % (sInstr, self.sAddress, dOp["quant"])
            )
        elif dOp["operation"] == Interface.ARM:
            sMsg = (
                "An error occurred when arming the instrument.\n\n"
                + "Instrument name: %s\nAddress: %s\nQuantities: %s"
                % (sInstr, self.sAddress, str(dOp["lQuant"]))
            )
        elif dOp["operation"] == Interface.SET_CFG:
            sMsg = (
                "An error occurred when setting the instrument "
                + "configuration.\n\n"
                + "Instrument name: %s\nAddress: %s" % (sInstr, self.sAddress)
            )
        elif dOp["operation"] == Interface.GET_CFG:
            sMsg = (
                "An error occurred when reading the instrument "
                + "configuration.\n\n"
                + "Instrument name: %s\nAddress: %s" % (sInstr, self.sAddress)
            )
        elif dOp["operation"] in (Interface.CLOSE, Interface.FORCE_CLOSE):
            sMsg = (
                "An error occurred when closing the instrument "
                + "connection.\n\n"
                + "Instrument name: %s\nAddress: %s" % (sInstr, self.sAddress)
            )
        elif dOp["operation"] in (Interface.ABORT_OPERATION,):
            sMsg = (
                "An error occurred when aborting an operation.\n\n"
                + "Instrument name: %s\nAddress: %s" % (sInstr, self.sAddress)
            )
        elif dOp["operation"] in (Interface.WAIT_FOR_SWEEP,):
            sMsg = (
                "An error occurred when waiting for a sweep value.\n\n"
                + "Instrument name: %s\nAddress: %s" % (sInstr, self.sAddress)
            )
        else:
            sMsg = "An error occurred.\n\nInstrument name: %s\nAddress: %s" % (
                sInstr,
                self.sAddress,
            )
        # add error from driver
        if sError != "":
            #            sMsg += "\n\n" + sError
            sMsg += "\n\nError message:\n" + sError
        return sMsg

    def _get_sweep_interval_with_repeat_set(self, quant):
        """Check if sweeping is done with repeat set for given quantity"""
        sCmd = quant.sweep_cmd
        sSweep = "***REPEAT SET***"
        # if quantity is not sweepable, fall back to repeat-set
        if not quant.isSweepable():
            sCmd = sSweep
        if sCmd is not None and sCmd.find(sSweep) >= 0:
            # get sweep interval from command string
            sRest = sCmd[sCmd.find(sSweep) + len(sSweep) :].strip()
            if len(sRest) > 0:
                interval = float(sRest)
            else:
                interval = 0.1
            return interval
        else:
            return 0.0

    def _performSetValueNoNone(self, quant, value, sweepRate=0.0, options={}):
        """Perform set value and make sure reply is not None"""
        new_value = self.performSetValue(
            quant, value, sweepRate=sweepRate, options=options
        )
        # if driver function returns None, return input set value
        return value if (new_value is None) else new_value

    def _performSetValue(
        self, quant, value, sweepRate=0.0, bWaitForSweepInFunction=False, options={}
    ):
        """Perform the Set Value instrument operation, implementing the internal
        sweep function."""
        # if sweep rate is zero, don't sweep, call normal set value function
        if sweepRate is None or sweepRate == 0.0:
            return self._performSetValueNoNone(quant, value, 0.0, options)
        # in sweep mode, store target sweep value
        quant.sweep_target = value
        # check if repeat set sweeping is used
        repeat_interval = self._get_sweep_interval_with_repeat_set(quant)
        if repeat_interval > 0.0:
            # repeat interval is non-zero, use repeat set
            # remove first/last info from options dict for repeated set sweeping
            optsNew = options.copy()
            for sOpt in ["call_no", "n_calls"]:
                if sOpt in optsNew:
                    optsNew.pop(sOpt)
            # first, get old value
            currValue = self.performGetValue(quant, options=optsNew)
            if value == currValue:
                # already at the final value, return
                return currValue
            # get number of steps
            dSweepTime = abs(value - currValue) / sweepRate
            nStep = int(np.ceil(dSweepTime / repeat_interval))
            # create step points, excluding start and end point
            vStep = np.linspace(currValue, value, nStep + 1)
            t0 = timer()
            if bWaitForSweepInFunction:
                # function should wait for sweep to finish
                for n, stepValue in enumerate(vStep[1:-1]):
                    # perform new step
                    newValue = self._performSetValueNoNone(
                        quant, stepValue, sweepRate=0.0, options=optsNew
                    )
                    quant.setValue(newValue)
                    # emit signal to update local GUI
                    self.reportCurrentValue(quant, newValue)
                    # self.emit(SIGNAL("WorkerSet"), quant.name, newValue, sweepRate, None)
                    # check if stopped
                    if self.isStopped():
                        return newValue
                    dt = timer() - t0
                    # wait some time, if necessary
                    waitTime = repeat_interval * (n + 1) - dt
                    if waitTime > 0.0:
                        self.wait(waitTime)
                # if loop didn't break, do final step value
                value = self._performSetValueNoNone(
                    quant, value, sweepRate=0.0, options=options
                )
            else:
                # function should not wait for sweep to finish, setup new calls
                dCfg = {
                    "values": vStep,
                    "index": 1,
                    "t0": t0,
                    "interval": repeat_interval,
                }
                optsNew["repeat_set_cfg"] = dCfg
                # call repeat set function for first step
                quant.is_repeat_sweeping = True
                value = self.performRepeatSet(quant, vStep[1], sweepRate, optsNew)
        else:
            # otherwise, call normal set value function with given sweep rate
            # convert to rate / min, if wanted
            sweepScale = 60.0 if quant.sweep_minute else 1.0
            value = self._performSetValueNoNone(
                quant, value, sweepRate * sweepScale, options
            )
            if bWaitForSweepInFunction:
                while self.checkIfSweeping(quant) and (not self.isStopped()):
                    # wait some time, then get new value
                    self.wait(self.WAIT_CHECK_SWEEP)
                # check if driver was stopped from outside, if so stop sweep
                if self.isStopped():
                    self.stopSweep(quant)
                    # get final value if stopped
                    value = self.performGetValue(quant, options=options)
                else:
                    # NB! only get target value if final call, to allow sweeping
                    # of multiple quantities within a driver (ETH compact, for example)
                    # If not, getting the value here could return the wrong value
                    # in case performSetValue is executed only for the last quantity
                    if False or self.isFinalCall(options):
                        # temporarily disable getting value, always return sweep target
                        # value = self.performGetValue(quant, options=options)
                        value = quant.sweep_target
                    else:
                        value = quant.sweep_target
        return value

    def performRepeatSet(self, quant, value, sweepRate=0.0, options={}):
        """Perform a repeated set-type sweep, without blocking the driver"""
        # make sure target value is valied
        dCfg = options["repeat_set_cfg"]
        n = dCfg["index"]
        if (not quant.is_repeat_sweeping) or quant.sweep_target != dCfg["values"][-1]:
            # target value doesn't match this sweep, abort and return last value
            return quant.getValue()
        # perform new step
        newValue = self._performSetValueNoNone(
            quant, value, sweepRate=0.0, options=options
        )
        # add counter, check if we have reached target
        n += 1
        if n == len(dCfg["values"]):
            # final value reached, turn off sweeping
            quant.is_repeat_sweeping = False
        else:
            # calculate time to next step
            dt = timer() - dCfg["t0"]
            waitTime = dCfg["interval"] * n - dt
            # convert to millisecond int, with minimum 20 ms
            delay = max(waitTime, 0.020)
            # add new operation, with delay
            dCfg["index"] = n
            options["operation"] = Interface.REPEAT_SET
            options["value"] = dCfg["values"][n]
            options["sweep_rate"] = sweepRate
            options["repeat_set_cfg"] = dCfg
            try:
                self.interface.addOperation(options, callId=None, delay=delay)
            except InstrStateError:
                # if driver state errors, driver was probably closed
                quant.is_repeat_sweeping = False
        return newValue

    def stopSweep(self, quant, options={}):
        """Stop sweep"""
        quant.is_repeat_sweeping = False
        self.performStopSweep(quant, options=options)

    def initSetConfig(self):
        """This function is run before setting values in Set Config"""
        pass

    def finalSetConfig(self):
        """This function is run after setting values in Set Config"""
        pass

    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection"""
        pass

    def performClose(self, bError=False, options={}):
        """Perform the close instrument connection operation"""
        pass

    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform the Set Value instrument operation. This function should
        return the actual value set by the instrument"""
        return value

    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation"""
        return quant.getValue()

    def performArm(self, quant_names, options={}):
        """Perform the instrument arm operation"""
        pass

    def performStopSweep(self, quant, options={}):
        """Send command to instrument to stop current sweep"""
        pass

    def checkIfSweeping(self, quant, options={}):
        """Check if instrument is sweeping the given quantity"""
        # if repeat-set mode, sweeping is set by sweep_target not being none
        sCmd = quant.sweep_cmd
        if sCmd is not None and sCmd.find("***REPEAT SET***") >= 0:
            return quant.is_repeat_sweeping  # (quant.sweep_target is not None)
        # read value and compare to target within tolerance
        target_value = quant.sweep_target
        if target_value is None:
            return False
        currValue = self.performGetValue(quant, options=options)
        # emit signal to update local GUI
        self.reportCurrentValue(quant, currValue)
        # self.emit(SIGNAL("WorkerSet"), quant.name, currValue, None, None)
        if quant.sweep_res is None:
            # default resolution is 9 digits, to avoid float errors
            resolution = max(abs(target_value), abs(currValue)) / 1e9
        else:
            resolution = quant.sweep_res
        # return true if value is within resolution
        return abs(target_value - currValue) > resolution

    def getValuesFromUpdatedPath(self, quant_name, value):
        """Get new values based on an updated path quantity"""
        return {}

    def isConfigUpdated(self, bReset=True):
        """Helper function, returns true if any instrument non-read only
        quantity has been updated since last call"""
        bUpdated = self.bCfgUpdated
        # reset flag
        if bReset:
            self.bCfgUpdated = False
        return bUpdated

    def isHardwareTrig(self, options):
        """Helper function, checks if the caller is in hardware trig mode"""
        trig_mode = options.get("trig_mode", False)
        return trig_mode

    def getTrigChannel(self, options):
        """Helper function, get trig channel for instrument, or None if N/A"""
        trig_channel = options.get("trig_channel", None)
        return trig_channel

    def isHardwareLoop(self, options):
        """Helper function, checks if the caller is in hardware loop mode"""
        if "n_seq" in options:
            return True
        else:
            return False

    def getHardwareLoopIndex(self, options):
        """Helper function, get hardware loop number"""
        n_seq = options.get("n_seq", 1)
        seq_no = options.get("seq_no", 0)
        return (seq_no, n_seq)

    def isFirstCall(self, options):
        """Helper function, checks options dict if this is the first call in a
        series of call, for example from Set/Get config or Measurement"""
        if "call_no" in options:
            return options["call_no"] == 0
        else:
            return True

    def isFinalCall(self, options):
        """Helper function, checks options dict if this is the final call in a
        series of call, for example from Set/Get config or Measurement"""
        if "call_no" not in options:
            return True
        iCall = options["call_no"]
        nCall = options["n_calls"] if "n_calls" in options else 0
        return (iCall + 1) >= nCall

    def get_call_id(self):
        """Get current call id. May retrun next id if current op is arming"""
        # special case for arm/get - if already completed, use id of next call
        if self.dOp.get("arm_completed", False):
            # get new calls
            try:
                self.getOperationsFromCaller(wait=False)
            except Exception:
                pass
            # use call id for first get-operation in queue
            for d in self.lOp:
                if d["operation"] == Interface.GET:
                    return d["call_id"]
        return self.callId

    def reportStatus(self, message):
        """Report status message to instrument server and connected clients.

        Parameters
        ----------
        message : str
            Message to send to the instrument server and clients.
        """
        # special case for arm/get - if already completed, use id of next call
        self.interface.reportStatus(message, self.get_call_id())

    def reportProgress(self, progress):
        """Report progress to instrument server and connected clients.

        Parameters
        ----------
        progress : float
            The progress should be a floating point number between 0.0 and 1.0.
        """
        # special case for arm/get - if already completed, use id of next call
        self.interface.reportProgress(progress, self.get_call_id())

    def reportCurrentValue(self, quant, value):
        """Report current value to instrument server and connected clients.

        Parameters
        ----------
        quant : quantity object
            Quantity for which to report current value.
        value : float or boolean
            The current value of the quantity.
        sweep_rate : float, optional
            The current sweep rate of the active quantity.
        """
        # only report status to client if set/get/wait for active quantity
        quant_name = quant.name
        if (
            self.dOp["operation"]
            in (Interface.SET, Interface.GET, Interface.WAIT_FOR_SWEEP)
            and quant_name == self.dOp["quant"]
        ):
            callId = self.callId
        else:
            callId = None
        # send signal to other thread
        self.interface.reportCurrentValue(quant_name, value, callId)
        # self.emit(SIGNAL("WorkerCurrentValue"), quant_name, value, callId)

    def log(self, *args, **keywords):
        """Log a message to instrument logger. Log level is an integer ranging
        from 40 (error), 30 (warning, always shown) to 10 (debug, only show in
        debug mode)"""
        # get log level from keywords
        level = keywords.get("level", 20)
        # convert all other arguments to string
        message = " ".join([str(x) for x in args])
        # log message
        self.logger.log(level, message)
        # # only report if level exceeds or is equal to set log level
        # if level >= self.logLevel:
        #     self.interface.reportLog(message, level)

    def wait(self, wait_time=0.05):
        """Delay execution for the given time (in seconds)"""
        time.sleep(wait_time)
