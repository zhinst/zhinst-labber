from zhinst.toolkit.nodetree import NodeTree, Node


class SnapshotManager:
    def __init__(self, nodetree: NodeTree):
        self._values = {}
        self._nodetree = nodetree

    def get_value(self, path):
        if not self._values:
            self._values = self._nodetree["*"]()
        try:
            return self._values[self._nodetree[path]]
        except KeyError:
            # node not found in snapshot
            print(f"{path} not found in snapshot")
            return self._nodetree[path]()

    def clear(self):
        self._values = {}


class TransactionManager:
    def __init__(self, tk_instrument, labber_instrument):
        self._transaction = None
        self._tk_instrument = tk_instrument
        self._labber_instrument = labber_instrument
        self._functions = None

    def start(self) -> None:
        self._transaction = self._tk_instrument.set_transaction()
        self._transaction.__enter__()
        self._functions = []

    def add_function(self, name: str, path: str) -> None:
        self._functions.append((name, path))

    def end(self) -> None:
        self._transaction.__exit__(None, None, None)
        self._transaction = None
        # Call every function only once
        functions = [
            func
            for n, func in enumerate(self._functions)
            if func not in self._functions[:n]
        ]
        for function in functions:
            self._labber_instrument.call_toolkit_function(function[0], function[1])
        self._functions = None

    def is_running(self) -> bool:
        return self._transaction is not None
