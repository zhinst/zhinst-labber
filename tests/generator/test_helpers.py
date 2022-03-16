import typing as t
import pytest
from zhinst.labber.generator import helpers


@pytest.mark.parametrize("inp, out", (
    ("/foo/0/bar/", "foo/0/bar"),
    ("foo/0/bar/", "foo/0/bar"),
    ("foo", "foo"),
    ("", ""),
    ("/", ""),
))
def test_remove_leading_trailing_slashes(inp, out):
    assert helpers.remove_leading_trailing_slashes(inp) == out

def test_matching_name():
    def find_nth_occurence(s, target, idx):
        return s.find(target, s.find(target) + idx)

    assert find_nth_occurence('d/*/s/*', '*', 1) == 6

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
    assert helpers._replace_characters(s) == 'a:d:S percent :`'


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
