import typing as t
from pathlib import Path

import autoflake
import black
import jinja2


def generate_labber_device_driver_code(
    classname: str, settings_file: t.Union[Path, str]
) -> str:
    """Generate labber device driver code.
    
    Generates a Python file based on:
    `zhinst/labber/code_generator/templates/device_template.py.j2`
    """
    data = {"class": {"name": classname}, "settings_file": settings_file}

    fp = Path(__file__).parent / "templates"
    templateLoader = jinja2.FileSystemLoader(searchpath=fp)
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template("device_template.py.j2")
    result = template.render(data)
    result = black.format_str(result, mode=black.FileMode())
    result = autoflake.fix_code(result, remove_all_unused_imports=True)
    return result
