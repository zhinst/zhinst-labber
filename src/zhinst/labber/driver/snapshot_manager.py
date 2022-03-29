"""Snapshot manager for getting ans settings more than one node at a time."""
import typing as t

from zhinst.toolkit.nodetree import NodeTree


class SnapshotManager:
    """Manages a instrument snapshot.

    Lazy snapshot manager that gets all nodes values from toolkit with a single
    transaction and the reuses the values in later calls until ``clear`` is
    called.

    Args:
        nodetree: Toolkit nodetree which is used for getting the values.
    """

    def __init__(self, nodetree: NodeTree):
        self._values = {}
        self._nodetree = nodetree

    def get_value(self, path: str) -> t.Any:
        """Get a value from the snapshot.

        If the internal snaphot is empty a new one is taken. If the value is
        not present in the snapshot a single get operation is issued.

        Args:
            path: Path of the node (e.g. /test/a)

        Returns:
            Value for the specified node

        Raises:
            KeyError: If the value is not part of the snapshot and also can not
                be fetched with a single get command.
        """
        if not self._values:
            self._values = self._nodetree["*"](parse=False, enum=False)
        try:
            return self._values[self._nodetree[path]]
        except KeyError:
            # node not found in snapshot
            print(f"{path} not found in snapshot")
            return self._nodetree[path]()

    def clear(self) -> None:
        """Clears the current snapshot if there is any."""
        self._values = {}


class TransactionManager:
    """Manages a set transaction

    It both handles nodes and functions. The node transaction is handled within
    toolkit and the functions are cached an called in a loop at the end of the
    transaction.

    Args:
        tk_instrument: toolkit object of the instrument
        labber_instrument: labber object of the instrument
    """

    def __init__(
        self,
        tk_instrument: t.Union["Session", "DeviceType", "ModuleType"],
        labber_instrument: "BaseDevice",
    ):
        self._transaction = None
        self._tk_instrument = tk_instrument
        self._labber_instrument = labber_instrument
        self._functions = None

    def start(self) -> None:
        """Start a new transaction.

        Does not do any sanity checks if a transaction can be started or if
        there is already a running one.
        """
        self._transaction = self._tk_instrument.root.set_transaction()
        self._transaction.__enter__()
        self._functions = []

    def add_function(self, name: str, path: str) -> None:
        """Add function to the transaction.

        Args:
            name: Internal name of the function.
            path: Path of the toolkit function.
        """
        self._functions.append((name, path))

    def end(self) -> None:
        """End a running transaction.

        Does not do any sanity checks if a transaction can be ended or if
        there is even a running one.

        After the toolkit transaction is closed all cached functions are called
        in a loop. (Each function is only called once even if it was cached
        multiple times).
        """
        self._transaction.__exit__(None, None, None)
        self._transaction = None
        # Call every function only once
        functions = [
            func
            for n, func in enumerate(self._functions)
            if func not in self._functions[:n]
        ]
        for function in functions:
            self._labber_instrument.call_function(function[0], function[1])
        self._functions = None

    def is_running(self) -> bool:
        """Check if a transaction is running or not.

        Returns:
            Status of the transaction.
        """
        return self._transaction is not None
