import typing as t
import pytest
from zhinst.labber.generator import helpers


def test_matching_name():
    def find_nth_occurrence(s, target, idx):
        return s.find(target, s.find(target) + idx)

    assert find_nth_occurrence("d/*/s/*", "*", 1) == 6


def test_replace_characters():
    s = 'a;d:S%\n;\r"'
    assert helpers._replace_characters(s) == "a:d:S percent :`"


def test_delete_device_from_node_path():
    r = helpers.delete_device_from_node_path("/DEV123/FOO/0/BAR")
    assert r == "/FOO/0/BAR"

    r = helpers.delete_device_from_node_path("/FOO/0/BAR")
    assert r == "/FOO/0/BAR"


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
    assert val == None


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
