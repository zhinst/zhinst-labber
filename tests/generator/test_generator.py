from collections import OrderedDict

from zhinst.labber.generator.generator import conf_to_labber_format


def test_conf_to_labber_format():
    conf = {
        "General Settings": {"version": "1.0"},
        "/bar/0/foo/2/wavE": {
            "set_cmd": "/bar/0/foo/2/wavE",
            "get_cmd": "/bar/0/foo/2/wavE",
            "label": "/bar/0/foo/2/wavE",
            "section": "bar",
            "group": "bar 0",
            "tooltip": "tooltip",
            "datatype": "BOOLEAN",
        },
        "/bar/1/foo/0/wavE": {
            "set_cmd": "/bar/1/foo/0/wavE",
            "get_cmd": "/bar/1/foo/0/wavE",
            "label": "/bar/1/foo/0/wavE",
            "section": "bar",
            "group": "bar 0",
            "tooltip": "tooltip",
            "datatype": "BOOLEAN",
        },
        "/bar/0/foo/1/wavE": {
            "set_cmd": "/bar/0/foo/1/wavE",
            "get_cmd": "/bar/0/foo/1/wavE",
            "label": "/bar/0/foo/1/wavE",
            "section": "bar",
            "group": "bar 0",
            "tooltip": "tooltip",
            "datatype": "BOOLEAN",
        },
        "/bar/0/foo/0/wavE": {
            "set_cmd": "/bar/0/foo/0/wavE",
            "get_cmd": "/bar/0/foo/0/wavE",
            "label": "/bar/0/foo/0/wavE",
            "section": "bar",
            "group": "bar 0",
            "tooltip": "tooltip",
            "datatype": "BOOLEAN",
        },
        "/bar/1/foo/1/wavE": {
            "set_cmd": "/bar/1/foo/1/wavE",
            "get_cmd": "/bar/1/foo/1/wavE",
            "label": "/bar/1/foo/1/wavE",
            "section": "bar",
            "group": "bar 0",
            "tooltip": "tooltip",
            "datatype": "BOOLEAN",
        },
    }
    d = conf_to_labber_format(conf, delim=" - ")
    assert d == OrderedDict(
        [
            (
                "Bar - 0 - Foo - 0 - Wave",
                {
                    "set_cmd": "/bar/0/foo/0/wavE",
                    "get_cmd": "/bar/0/foo/0/wavE",
                    "Label": "Bar - 0 - Foo - 0 - Wave",
                    "Section": "Bar",
                    "Group": "Bar 0",
                    "tooltip": "tooltip",
                    "datatype": "BOOLEAN",
                },
            ),
            (
                "Bar - 0 - Foo - 1 - Wave",
                {
                    "set_cmd": "/bar/0/foo/1/wavE",
                    "get_cmd": "/bar/0/foo/1/wavE",
                    "Label": "Bar - 0 - Foo - 1 - Wave",
                    "Section": "Bar",
                    "Group": "Bar 0",
                    "tooltip": "tooltip",
                    "datatype": "BOOLEAN",
                },
            ),
            (
                "Bar - 0 - Foo - 2 - Wave",
                {
                    "set_cmd": "/bar/0/foo/2/wavE",
                    "get_cmd": "/bar/0/foo/2/wavE",
                    "Label": "Bar - 0 - Foo - 2 - Wave",
                    "Section": "Bar",
                    "Group": "Bar 0",
                    "tooltip": "tooltip",
                    "datatype": "BOOLEAN",
                },
            ),
            (
                "Bar - 1 - Foo - 0 - Wave",
                {
                    "set_cmd": "/bar/1/foo/0/wavE",
                    "get_cmd": "/bar/1/foo/0/wavE",
                    "Label": "Bar - 1 - Foo - 0 - Wave",
                    "Section": "Bar",
                    "Group": "Bar 0",
                    "tooltip": "tooltip",
                    "datatype": "BOOLEAN",
                },
            ),
            (
                "Bar - 1 - Foo - 1 - Wave",
                {
                    "set_cmd": "/bar/1/foo/1/wavE",
                    "get_cmd": "/bar/1/foo/1/wavE",
                    "Label": "Bar - 1 - Foo - 1 - Wave",
                    "Section": "Bar",
                    "Group": "Bar 0",
                    "tooltip": "tooltip",
                    "datatype": "BOOLEAN",
                },
            ),
            ("General Settings", {"version": "1.0"}),
        ]
    )
