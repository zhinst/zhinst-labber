import pytest

from zhinst.labber.generator.quants import Quant, NodeQuant, QuantGenerator


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

    def test_permission(self):
        obj = NodeQuant({"Node": "/bar/0", "Properties": "Write"})
        assert obj.permission == "WRITE"

        obj = NodeQuant({"Node": "/bar/0", "Properties": ""})
        assert obj.permission == "NONE"

    def test_title(self):
        obj = NodeQuant({"Node": "/bar/0", "Properties": "Write"})
        assert obj.title == "BAR/0"

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
        assert obj.as_dict(flat=True) == {
            "section": "qachannels/0",
            "group": "qachannels/output",
            "label": "qachannels/0/output/filter",
            "datatype": "DOUBLE",
            "tooltip": "<html><body><p>Reads the selected analog filter before the Signal Output.</p><p><ul><li>lowpass_1500: Low-pass filter of 1.5 GHz.</li><li>lowpass_3000: Low-pass filter of 3 GHz.</li><li>bandpass_3000_6000: Band-pass filter between 3 GHz - 6 GHz</li><li>bandpass_6000_10000: Band-pass filter between 6 GHz - 10 GHz</li></ul></p><p><b>QACHANNELS/0/OUTPUT/FILTER</b></p></body></html>",
            "permission": "READ",
            "get_cmd": "QACHANNELS/0/OUTPUT/FILTER",
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
                "group": "qachannels/generator",
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
        
        obj = Quant("/qachannels", {})
        assert obj.label == "qachannels"

        obj = Quant("/qachannels/0/wave/0", {})
        assert obj.label == "wave/0"

    def test_group(self):
        obj = Quant("/qachannels/0/wave/0", {})
        assert obj.group == "qachannels/wave"

        obj = Quant("/qachannels", {})
        assert obj.group == "qachannels"

    def test_as_dict(self):
        assert self.obj.as_dict() == {
            "qachannels/0/generator/arm": {
                "label": "qachannels/0/generator/arm",
                "group": "qachannels/generator",
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




class TestQuantGenerator:
    @pytest.fixture
    def q_gen(self):
        data = [
            "/DEV1234/FOO/0/BAR/0",
            "/DEV1234/FOO/0/BAR/1",
            "/DEV1234/FOO/1/BAR/0",
            "/DEV1234/FOO/1/BAR/1",
            "/DEV1234/CLOCK",
            "/DEV1234/SYSTEM/BAR",
            "/DEV1234/SYSTEM/FOO/0/FF",
            "/DEV1234/SYSTEM/FOO/1/FF",
            "/QACHANNELS/0/GENERATOR/",
            "/QACHANNELS/1/GENERATOR/"
        ]
        return QuantGenerator(data)

    def test_quant_paths_dev(self, q_gen):
        r = q_gen.quant_paths("/foo/*/bar/*", ["dev", "dev"])
        assert r == ["/foo/0/bar/0", "/foo/0/bar/1", "/foo/1/bar/0", "/foo/1/bar/1"]

        r = q_gen.quant_paths("/system/foo/*/ff", ["dev"])
        assert r == ["/system/foo/0/ff", "/system/foo/1/ff"]

        r = q_gen.quant_paths("/qachannels/*/generator/sequencer_program", ["dev"])
        assert r == ["/qachannels/0/generator/sequencer_program", "/qachannels/1/generator/sequencer_program"]

    def test_quant_paths_number(self, q_gen):
        r = q_gen.quant_paths("/foo/*/bar/*", ["dev", 3])
        assert r == [
            "/foo/0/bar/0",
            "/foo/0/bar/1",
            "/foo/0/bar/2",
            "/foo/1/bar/0",
            "/foo/1/bar/1",
            "/foo/1/bar/2",
        ]
        r = q_gen.quant_paths("/system/foo/*/ff", [1])
        assert r == ["/system/foo/0/ff"]

    def test_quant_paths_no_indexes(self, q_gen):
        r = q_gen.quant_paths("/foo/*/bar/*", [])
        assert r == ["/foo/0/bar/0", "/foo/0/bar/1", "/foo/1/bar/0", "/foo/1/bar/1"]

        r = q_gen.quant_paths("/system/foo/*/ff", [])
        assert r == ["/system/foo/0/ff", "/system/foo/1/ff"]

    def test_quant_paths_no_path(self, q_gen):
        r = q_gen.quant_paths("/foobar/*/asd/*/ff", ["dev", "dev"])
        assert r == []

        r = q_gen.quant_paths("/foobar/*/asd/*/ff", [2, 3])
        assert r == [
            "/foobar/0/asd/0/ff",
            "/foobar/0/asd/1/ff",
            "/foobar/0/asd/2/ff",
            "/foobar/1/asd/0/ff",
            "/foobar/1/asd/1/ff",
            "/foobar/1/asd/2/ff",
        ]

    def test_quant_paths_missing_indexes(self, q_gen):
        r = q_gen.quant_paths("/foo/*/bar/*", ["dev"])
        assert r == ["/foo/0/bar/0", "/foo/0/bar/1", "/foo/1/bar/0", "/foo/1/bar/1"]

    def test_quant_paths_no_wildcard(self, q_gen):
        r = q_gen.quant_paths("/system/bar", [])
        assert r == ['/system/bar']
