from zhinst.toolkit.nodetree import NodeTree, Node


class SnapshotManager:
    def __init__(self, nodetree: NodeTree):
        self._values = {}
        self._nodetree = nodetree

    def get_value(self, path):
        if not self._values:
            self._values = Node(self._nodetree, tuple())()
        try:
            return self._values[self._nodetree[path]]
        except KeyError:
            # node not found in snapshot
            print(f"{path} not found in snapshot")
            return self._nodetree[path]()

    def clear(self):
        self._values = {}
