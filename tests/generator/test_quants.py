import pytest

from zhinst.labber.generator.quants import Quant, NodeQuant


@pytest.fixture
def node_info():
    return {
        "Node": "/DEV12018/QACHANNELS/0/CENTERFREQ",
        "Description": "The Center Frequency of the analysis band.",
        "Properties": "Read, Write, Setting",
        "Type": "Double",
        "Unit": "Hz",
    }


node_dict_enum = {
    "Node": "/DEV12018/QACHANNELS/0/OUTPUT/FILTER",
    "Description": "Reads the selected analog filter before the Signal Output.",
    "Properties": "Read",
    "Type": "Integer (enumerated)",
    "Unit": "None",
    "Options": {
        "0": '"lowpass_1500": Low-pass filter of 1.5 GHz.',
        "1": '"lowpass_3000": Low-pass filter of 3 GHz.',
        "2": '"bandpass_3000_6000": Band-pass filter between 3 GHz - 6 GHz',
        "3": '"bandpass_6000_10000": Band-pass filter between 6 GHz - 10 GHz',
    },
}


class TestNodeQuant:
    def test_node_quant_no_enum(self, node_info):
        obj = NodeQuant(node_info)
        assert obj.as_dict(flat=False) == {
            "/qachannels/0/centerfreq": {
                "section": "qachannels/0",
                "group": "qachannels",
                "label": "qachannels/0/centerfreq",
                "datatype": "DOUBLE",
                "unit": "Hz",
                "tooltip": "<html><body><p>The Center Frequency of the analysis band.</p><p><b>QACHANNELS/0/CENTERFREQ</b></p></body></html>",
                "permission": "BOTH",
                "set_cmd": "QACHANNELS/0/CENTERFREQ",
                "get_cmd": "QACHANNELS/0/CENTERFREQ",
            }
        }

    def test_node_quant_enum(self):
        obj = NodeQuant(node_dict_enum)
        assert obj.as_dict(flat=False) == {
            "/qachannels/0/output/filter": {
                "section": "qachannels/0",
                "group": "qachannels/output",
                "label": "qachannels/0/output/filter",
                "datatype": "DOUBLE",
                "tooltip": "<html><body><p>Reads the selected analog filter before the Signal Output.</p><p><ul><li>lowpass_1500: Low-pass filter of 1.5 GHz.</li><li>lowpass_3000: Low-pass filter of 3 GHz.</li><li>bandpass_3000_6000: Band-pass filter between 3 GHz - 6 GHz</li><li>bandpass_6000_10000: Band-pass filter between 6 GHz - 10 GHz</li></ul></p><p><b>QACHANNELS/0/OUTPUT/FILTER</b></p></body></html>",
                "permission": "READ",
                "get_cmd": "QACHANNELS/0/OUTPUT/FILTER",
            }
        }

    @pytest.mark.parametrize(
        "node, datatype",
        [
            ("/DEV12018/QACHANNELS/READY", "BOOLEAN"),
            ("/DEV12018/QACHANNELS/ENABLE", "BOOLEAN"),
            ("/DEV12018/QACHANNELS/SINGLE", "BOOLEAN"),
            ("/DEV12018/QACHANNELS/BUSY", "BOOLEAN"),
            ("/DEV12018/QACHANNELS/ON", "BOOLEAN"),
            ("/DEV12018/QACHANNELS/RESET", "BOOLEAN"),
        ],
    )
    def test_node_quant_datatype(self, node_info, node, datatype):
        node_info["Node"] = node
        obj = NodeQuant(node_info)
        assert obj.datatype == datatype


class TestQuantSuffix:
    conf = {"datatype": "BOO", "suffix": "File", "permission": "READ"}
    path = "/qachannels/0/generator/arm/"
    obj = Quant(path, conf)

    def test_title(self):
        assert self.obj.title == "qachannels/0/generator/arm"

    def test_label(self):
        assert self.obj.label == "arm"

    def test_as_dict(self):
        assert self.obj.as_dict() == {
            "qachannels/0/generator/arm/file": {
                "label": "qachannels/0/generator/arm/file",
                "group": "qachannels/0/generator/",
                "section": "qachannels/0",
                "set_cmd": "qachannels/0/generator/arm",
                "get_cmd": "qachannels/0/generator/arm",
                "permission": "READ",
                "datatype": "BOO",
            }
        }


class TestQuant:
    conf = {"datatype": "boo"}
    path = "/qachannels/0/generator/arm"
    obj = Quant(path, conf)

    def test_title(self):
        assert self.obj.title == "qachannels/0/generator/arm"

    def test_label(self):
        assert self.obj.label == "arm"

    def test_as_dict(self):
        assert self.obj.as_dict() == {
            "qachannels/0/generator/arm": {
                "label": "qachannels/0/generator/arm",
                "group": "qachannels/0/generator/",
                "section": "qachannels/0",
                "set_cmd": "qachannels/0/generator/arm",
                "get_cmd": "qachannels/0/generator/arm",
                "permission": "WRITE",
                "datatype": "boo",
            }
        }


def test_long_node_group_idx_over1():
    node = {
        "Node": "/DEV12018/SIGOUTS/1/PRECOMPENSATION/HIGHPASS/0/CLEARING/SLOPE",
        "Description": "The Center Frequency of the analysis band.",
        "Properties": "Read, Write, Setting",
        "Type": "Double",
        "Unit": "Hz",
    }
    obj = NodeQuant(node)
    assert obj.as_dict(flat=False) == {
        "/sigouts/1/precompensation/highpass/0/clearing/slope": {
            "section": "sigouts/1",
            "group": "sigouts/precompensation/highpass",
            "label": "sigouts/1/precompensation/highpass/0/clearing/slope",
            "datatype": "DOUBLE",
            "unit": "Hz",
            "tooltip": "<html><body><p>The Center Frequency of the analysis band.</p><p><b>SIGOUTS/1/PRECOMPENSATION/HIGHPASS/0/CLEARING/SLOPE</b></p></body></html>",
            "permission": "BOTH",
            "set_cmd": "SIGOUTS/1/PRECOMPENSATION/HIGHPASS/0/CLEARING/SLOPE",
            "get_cmd": "SIGOUTS/1/PRECOMPENSATION/HIGHPASS/0/CLEARING/SLOPE",
        }
    }


def test_long_node_group_idx2():
    node = {
        "Node": "/DEV12018/SIGOUTS/7/PRECOMPENSATION/BOUNCES/0/STATUS",
        "Description": "The Center Frequency of the analysis band.",
        "Properties": "Read, Write, Setting",
        "Type": "Double",
        "Unit": "Hz",
    }
    obj = NodeQuant(node)
    assert obj.as_dict(flat=False) == {
        "/sigouts/7/precompensation/bounces/0/status": {
            "section": "sigouts/7",
            "group": "sigouts/precompensation/bounces",
            "label": "sigouts/7/precompensation/bounces/0/status",
            "datatype": "DOUBLE",
            "unit": "Hz",
            "tooltip": "<html><body><p>The Center Frequency of the analysis band.</p><p><b>SIGOUTS/7/PRECOMPENSATION/BOUNCES/0/STATUS</b></p></body></html>",
            "permission": "BOTH",
            "set_cmd": "SIGOUTS/7/PRECOMPENSATION/BOUNCES/0/STATUS",
            "get_cmd": "SIGOUTS/7/PRECOMPENSATION/BOUNCES/0/STATUS",
        }
    }


def test_long_node_group_idx_asd():
    node = {
        "Node": "/DEV12018/QAS/0/CROSSTALK/ROWS/0/COLS/8",
        "Description": "The Center Frequency of the analysis band.",
        "Properties": "Read, Write, Setting",
        "Type": "Double",
        "Unit": "Hz",
    }
    obj = NodeQuant(node)
    assert obj.as_dict(flat=False) == {
        "/qas/0/crosstalk/rows/0/cols/8": {
            "section": "qas/0",
            "group": "qas/crosstalk/rows/cols",
            "label": "qas/0/crosstalk/rows/0/cols/8",
            "datatype": "DOUBLE",
            "unit": "Hz",
            "tooltip": "<html><body><p>The Center Frequency of the analysis band.</p><p><b>QAS/0/CROSSTALK/ROWS/0/COLS/8</b></p></body></html>",
            "permission": "BOTH",
            "set_cmd": "QAS/0/CROSSTALK/ROWS/0/COLS/8",
            "get_cmd": "QAS/0/CROSSTALK/ROWS/0/COLS/8",
        }
    }
