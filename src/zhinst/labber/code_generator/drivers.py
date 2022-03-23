import typing as t
from pathlib import Path

import autoflake
import black
import jinja2


def generate_labber_device_driver_code(
    classname: str, settings_file: t.Union[Path, str]
) -> str:
    data = {"class": {"name": classname}, "settings_file": settings_file}

    fp = Path(__file__).parent / "templates"
    templateLoader = jinja2.FileSystemLoader(searchpath=fp)
    templateEnv = jinja2.Environment(loader=templateLoader)
    fp = Path(__file__).parent / "templates/device_template.py.j2"
    template = templateEnv.get_template("device_template.py.j2")
    result = template.render(data)
    result = black.format_str(result, mode=black.FileMode())
    result = autoflake.fix_code(result, remove_all_unused_imports=True)
    return result
