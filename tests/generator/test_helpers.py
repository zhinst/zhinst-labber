import typing as t
import pytest
from zhinst.labber.generator import helpers


@pytest.mark.parametrize(
    "inp, out",
    (
        ("/foo/0/bar/", "foo/0/bar"),
        ("foo/0/bar/", "foo/0/bar"),
        ("foo", "foo"),
        ("", ""),
        ("/", ""),
    ),
)
def test_remove_leading_trailing_slashes(inp, out):
    assert helpers.remove_leading_trailing_slashes(inp) == out


def test_matching_name():
    def find_nth_occurence(s, target, idx):
        return s.find(target, s.find(target) + idx)

    assert find_nth_occurence("d/*/s/*", "*", 1) == 6


def test_enum_description():
    assert helpers.enum_description("tester: This tests.") == ("tester", "This tests.")
    assert helpers.enum_description("AAsdsd123") == ("", "AAsdsd123")


def test_to_labber_format():
    assert helpers.to_labber_format(str) == "STRING"
    assert helpers.to_labber_format(int) == "DOUBLE"
    assert helpers.to_labber_format(float) == "DOUBLE"
    assert helpers.to_labber_format(dict) == "PATH"
    assert helpers.to_labber_format(bool) == "BOOLEAN"
    assert helpers.to_labber_format(t.Dict) == "PATH"
    assert helpers.to_labber_format(t.List) == "PATH"
    assert helpers.to_labber_format(t.Dict) == "PATH"
    assert helpers.to_labber_format(None) == "STRING"


def test_replace_characters():
    s = 'a;d:S%\n;\r"'
    assert helpers._replace_characters(s) == "a:d:S percent :`"


def test_delete_device_from_node_path():
    r = helpers.delete_device_from_node_path("/DEV123/FOO/0/BAR")
    assert r == "/FOO/0/BAR"

    r = helpers.delete_device_from_node_path("/FOO/0/BAR")
    assert r == "/FOO/0/BAR"


def test_to_labber_combo_def():
    r = helpers.to_labber_combo_def(["foo", "bar"])
    assert r == {
        "cmd_def_1": "foo",
        "cmd_def_2": "bar",
        "combo_def_1": "foo",
        "combo_def_2": "bar",
    }

    r = helpers.to_labber_combo_def({"foo": 1, "bar": "test"})
    assert r == {
        "cmd_def_1": "foo",
        "cmd_def_2": "bar",
        "combo_def_1": "1",
        "combo_def_2": "test",
    }

    from enum import Enum

    class Bar(Enum):
        BAR = 1
        FOO = "d"

    r = helpers.to_labber_combo_def(Bar)
    assert r == {
        "cmd_def_1": "1",
        "cmd_def_2": "d",
        "combo_def_1": "BAR",
        "combo_def_2": "FOO",
    }


@pytest.mark.parametrize(
    "target, data",
    [
        (
            "/qaCHAnnels/0/foobar/1",
            {"/qachannels/*/foobar/*": {"foo": "bar"}},
        ),
        (
            "qachannels/0/foobar/1/bar",
            {"/qachannels/*/foobar/*": {"foo": "bar"}},
        ),
        (
            "qachannels/1/fooBar/",
            {"qachannels/*/": {"foo": "bar"}},
        ),
        (
            "qachannels/11/foobar",
            {"qachannels/*/foobar": {"foo": "bar"}},
        ),
        (
            "/qachannels/11/foobar/12/Wave/",
            {"/qachannels/*/foobar/*/wave": {"foo": "bar"}},
        ),
    ],
)
def test_match_in_dict_keys_match(target, data):
    key_, val = helpers.match_in_dict_keys(target, data)
    assert key_ == list(data.keys())[0]
    assert val == list(data.values())[0]


@pytest.mark.parametrize(
    "target, data",
    [
        (
            "/qaCHAnnels/0/foo",
            {"/qachannels/*/foobar/*": {"foo": "bar"}},
        ),
        (
            "qachannels/0/foobar/asd/bar",
            {"/qachannels/*/foobar/*/asd": {"foo": "bar"}},
        ),
        (
            "qachannels/1/fooBar/",
            {"qachannels/*/bar": {"foo": "bar"}},
        ),
        (
            "qachannels/11/foobar",
            {"qachannelsT/*/foobar": {"foo": "bar"}},
        ),
        (
            "/qachannels/11/foobar/12/Wave/",
            {"/qachannels/*/foobar/*/waves": {"foo": "bar"}},
        ),
    ],
)
def test_match_in_dict_keys_no_match(target, data):
    key_, val = helpers.match_in_dict_keys(target, data)
    assert key_ == ""
    assert val == {}


@pytest.mark.parametrize(
    "target, data, idx",
    [
        ("/qaCHAnnels/0/foobar/1", ["bar/*", "/qachannels/*/foobar/*"], 1),
        ("qachannels/0/foobar/asd/bar", ["/qachannels/*/foobar/*"], 0),
        ("qachannels/11/foobar/12", ["/qachannels/*/foobar/*"], 0),
        ("/qachannels/11/foobar/12/Wave/", ["/qachannels/*/foobar/*"], 0),
    ],
)
def test_match_in_list_match(target, data, idx):
    item = helpers.match_in_list(target, data)
    assert item == data[idx]


@pytest.mark.parametrize(
    "string, target, n, idx",
    [
        ("/qa/*/bar/*/foo", "*", 0, 4),
        ("/qa/*/bar/*/foo", "*", 1, 10),
        ("*/bar/*/foo", "*", 0, 0),
        ("/qa/*/bar/*/foo", "*", 2, -1),
        ("/qa/*/bar/*/foo", "*", 3, -1),
        ("/qa/*/bar/*/foo", "*", 4, -1),
        ("/awgs/*/waveform/waves/*", "*", 0, 6),
        ("/awgs/*/waveform/waves/*", "*", 1, 23),
    ],
)
def test_find_nth_occurrence(string, target, n, idx):
    assert helpers.find_nth_occurence(string, target, n) == idx


@pytest.mark.parametrize(
    "tp, node, enum, out",
    [
        ("Test tooltip.", None, None, "<html><body><p>Test tooltip.</p></body></html>"),
        ("", None, None, "<html><body><p></p></body></html>"),
        (
            "Test tooltip.",
            None,
            ["foo: 1", "bar: 2"],
            "<html><body><p>Test tooltip.</p><p><ul><li>foo: 1</li><li>bar: 2</li></ul></p></body></html>",
        ),
        (
            "Test tooltip.",
            "/bar",
            None,
            "<html><body><p>Test tooltip.</p><p><b>/bar</b></p></body></html>",
        ),
    ],
)
def test_tooltip(tp, node, enum, out):
    assert helpers.tooltip(tp, node, enum) == out
