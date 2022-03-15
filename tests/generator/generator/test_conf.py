from zhinst.labber.generator.conf import LabberConfiguration
import pytest

@pytest.mark.skip(reason="Refactoring")
def test_init():
    obj = LabberConfiguration("SHFQA4", "normal")
    assert obj._mode == "normal"
    assert obj._name == "SHFQA4"
    assert obj._set_name == "SHFQA"

@pytest.mark.skip(reason="Refactoring")
def test_ignored_functions_normal():
    obj = LabberConfiguration("SHFQA4", "normal")
    assert obj.ignored_nodes == [
        "/stats/*",
        "/status/*",
        "/system/activeinterface*",
        "/system/boardrevisions/*",
        "/system/fpgarevision",
        "/system/nics/*",
        "/system/properties/*",
        "/features/*",
        "/qachannels/*/generator/waveforms/*/length",
        "/qachannels/*/generator/sequencer/memoryusage",
        "/qachannels/*/generator/sequencer/status",
        "/qachannels/*/generator/sequencer/triggered",
        "/qachannels/*/generator/elf/*",
    ]

@pytest.mark.skip(reason="Refactoring")
def test_ignored_functions_adv():
    obj = LabberConfiguration("SHFQA4", "adv")
    assert obj.ignored_nodes == [
        "/features/*",
    ]

@pytest.mark.skip(reason="Refactoring")
def test_quants():
    obj = LabberConfiguration("SHFQA2", "normal")
    assert obj.quants == {
        "/clearhistory": {"update": {"datatype": "BOOLEAN"}, "extend": {}},
        "*/imp50": {"update": {"datatype": "BOOLEAN"}, "extend": {}},
        "/save/save": {"update": {"datatype": "BOOLEAN"}, "extend": {}},
        "/clockbase": {"update": {"section": "BOOLEAN"}, "extend": {}},
        "*/commandtable/data": {"update": {"datatype": "PATH", "set_cmd": "*.json"}},
        "/qachannels/*/generator/waveforms/*/wave": {
            "indexes": ["dev", "dev"],
            "conf": {"datatype": "VECTOR_COMPLEX"},
            "extend": {},
            "driver": {},
        },
        "/qachannels/*/generator/sequencer_program": {
            "indexes": ["dev"],
            "conf": {"datatype": "PATH", "set_cmd": "*.csv"},
            "driver": {"function": "qachannels[*].generator.sequencer_program"},
        },
        "scopes/*/result_0": {
            "indexes": ["dev"],
            "conf": {
                "label": "Result_0",
                "datatype": "VECTOR_COMPLEX",
                "show_in_measurement_dlg": "True",
                "x_name": "Length",
                "x_unit": "Sample",
            },
            "driver": {"function": "scopes[*].read", "args": "args[0][0]"},
        },
        "scopes/*/result_1": {
            "indexes": ["dev"],
            "conf": {
                "label": "Result_1",
                "datatype": "VECTOR_COMPLEX",
                "show_in_measurement_dlg": "True",
                "x_name": "Length",
                "x_unit": "Sample",
            },
            "driver": {"function": "scopes[*].read", "args": "args[0][1]"},
        },
        "qachannels/*/generator/wait_done": {
            "indexes": ["dev"],
            "conf": {"datatype": "BOOLEAN"},
            "driver": {"function": "qachannels/*/generator/wait_done"},
        },
        "qachannels/*/generator/pulses": {
            "indexes": [],
            "conf": {"datatype": "PATH"},
            "driver": {"function": "qachannels/*/generator/pulses"},
        },
        "qachannels/*/readout/result/enable": {
            "indexes": [],
            "conf": {},
            "driver": {"driver": {"wait_for": True}},
        },
        "qachannels/*/readout/wait_done": {
            "indexes": [],
            "conf": {},
            "driver": {"wait_for": True},
        },
        "qachannels/*/readout/integration_weights": {
            "indexes": [],
            "conf": {"datatype": "PATH", "set_cmd": "*.csv"},
            "driver": {"function": "qachannels/*/readout/write_integration_weights"},
        },
        "qachannels/*/spectroscopy/result/enable": {
            "indexes": [],
            "conf": {},
            "driver": {"driver": {"wait_for": True}},
        },
        "qachannels/*/spectroscopy/wait_done": {
            "indexes": [],
            "conf": {},
            "driver": {"wait_for": True},
        },
        "scopes/*/enable": {
            "indexes": [],
            "conf": {},
            "driver": {"driver": {"wait_for": True}},
        },
        "scopes/*/wait_done": {"indexes": [], "conf": {}, "driver": {"wait_for": True}},
        "/qachannels/*/awg/sequencer_program": {
            "indexes": ["dev"],
            "conf": {"datatype": "PATH", "set_cmd": "*.json"},
        },
    }

@pytest.mark.skip(reason="Refactoring")
def test_quant_sections():
    obj = LabberConfiguration("SHFQA2", "normal")
    assert obj.quant_sections == {
        "/qachannels/*/input*": "QA Setup",
        "/qachannels/*/generator*": "Generator",
        "/qachannels/*/readout/*": "QA Result",
        "/qachannels/*/spectroscopy/*": "QA Result",
        "/qachannels/*/triggers/*": "Input - Output",
        "/scopes/*": "Scopes",
        "/dios/*": "Input - Output",
        "/qachannels/*": "QA Setup",
        "/scopes/trigger/*": "Input - Output",
        "/system/clocks/*": "Input - Output",
    }

@pytest.mark.skip(reason="Refactoring")
def test_quant_groups():
    obj = LabberConfiguration("SHFQA2", "normal")
    assert obj.quant_groups == {
        "/qachannels/0/*": "QA Channel 0",
        "/qachannels/1/*": "QA Channel 1",
        "/qachannels/2/*": "QA Channel 2",
        "/qachannels/3/*": "QA Channel 3",
        "/qachannels/4/*": "QA Channel 4",
        "/qachannels/5/*": "QA Channel 5",
        "/qachannels/6/*": "QA Channel 6",
        "/qachannels/7/*": "QA Channel 7",
        "/scopes/0/*": "Scope 0",
        "/scopes/1/*": "Scope 1",
        "/scopes/2/*": "Scope 2",
        "/scopes/3/*": "Scope 3",
    }
