class Interface:
    """Helper object for interfacing data between the GUI and the driver"""

    ABORT_OPERATION = 7
    ARM = 10
    CLOSE = 5
    CURRENT = 15
    ERROR = 11
    FORCE_CLOSE = 6
    GET = 2
    GET_CFG = 4
    INACTIVE = 12
    LOG = 16
    OPEN = 0
    OP_INTERNAL = (18,)
    OP_NAMES = [
        "Open",
        "Set value",
        "Get value",
        "Set config",
        "Get config",
        "Close",
        "Force close",
        "Abort operation",
        "Wait for sweep",
        "Repeat set value",
        "Arm instrument",
        "Error",
        "Inactive",
        "Status",
        "Progress",
        "Current value",
        "Log",
        "Terminated",
        "Value from user",
    ]
    OP_STATUS = (13, 14, 15, 16)
    PROGRESS = 14
    REPEAT_SET = 9
    SET = 1
    SET_CFG = 3
    STATUS = 13
    TERMINATED = 17
    VALUE_FROM_USER = 18
    WAIT_FOR_SWEEP = 8

    def __init__(self, queueIn, queueOut, from_driver=False):
        pass

    def addOperation(self, dOp, callId, delay=None, callback=None):
        """Add a dict defining an operation to the queue"""

    def addOperationAbort(self, quant=None, callId=None):
        """Abort current operations"""

    def addOperationArm(self, lQuantNames, callId=None, options={}, delay=None):
        """Arm instrument for future call"""

    def addOperationCloseInstr(self, bForceQuit=False, callId=None, delay=None):
        """Open instrument communication"""

    def addOperationGetCfg(self, lQuantNames, lOldValues, callId=None, delay=None):
        """Get instrument config, by getting a list of quantities"""

    def addOperationGetValue(
        self, quant, callId=None, options={}, delay=None, callback=None
    ):
        """Get instrument value"""

    def addOperationOpenInstr(self, callId=None, delay=None):
        """Open instrument communication"""

    def addOperationSetCfg(
        self, lQuantNames, lValues, lRate, always_update_all, callId=None, delay=None
    ):
        """Set instrument config, by setting a list of quantities"""

    def addOperationSetValue(
        self,
        quant,
        value,
        rate=0.0,
        wait_for_sweep=True,
        callId=None,
        options={},
        delay=None,
        callback=None,
    ):
        """Set instrument value"""

    def addOperationWaitForSweep(
        self, quant, value=None, callId=None, options={}, delay=None
    ):
        """Set instrument value"""

    def isInterfaceStopped(self):
        """Return True if process stopped running or will stop shortly"""

    def popOpenCalls(self):
        """Remove and return a list of all open call references"""

    def reportAbort(self, callId=None):
        """Report abort current operations"""

    def reportArm(self, callId=None):
        """Report inactivity"""

    def reportClose(self, callId=None):
        """Report close operation"""

    def reportCurrentValue(self, quant_name, value, callId=None):
        """Report status"""

    def reportError(self, error, callId=None, at_init=False):
        """Open instrument communication"""

    def reportGet(self, quant, value, callId=None, dt=None):
        """Report instrument value"""

    def reportGetCfg(self, lQuantNames, lValues, callId=None):
        """REPORT GET instrument config, by getting a list of quantities"""

    def reportInactive(self, closed=False):
        """Report inactivity"""

    def reportLog(self, message, level=20):
        """Report log message"""

    def reportOpen(self, dInstrOpt, callId=None):
        """Open instrument communication"""

    def reportOperation(self, dOp, callId=None):
        """Report operation to caller"""

    def reportProgress(self, progress, callId=None):
        """Report progress"""

    def reportSet(self, quant, value, sweep_rate=None, callId=None, dt=None):
        """Report set value"""

    def reportSetCfg(self, lQuantNames, lValues, lRate, callId=None):
        """Report SET instrument config, by setting a list of quantities"""

    def reportStatus(self, message, callId=None):
        """Report status"""

    def reportTerminated(self):
        """Report status"""

    def reportWaitForSweep(self, quant, value, callId=None, dt=None):
        """Report instrument value"""

    def requestValueFromUser(self, value, text, title):
        """Report request for value from user dialog"""

    def sendDialogValue(self, value):
        """Report request for value from user dialog"""

    def setInterfaceStopped(self):
        """Set variable for defining that process has been stopped"""

    def updateResponseFromDriver(self, dOp):
        """Read response from driver"""
