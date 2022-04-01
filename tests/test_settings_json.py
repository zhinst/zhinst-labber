import jsonschema
import pytest
from pathlib import Path
import json


@pytest.fixture
def settings_json_schema():
    settings_file = Path(__file__).parent.parent / "src/zhinst/labber/resources/settings_json_schema.json"
    with open(settings_file, "r") as json_f:
        return json.load(json_f)


def test_validate_json(settings_json_schema, settings_json):
    jsonschema.validate(
        instance=settings_json,
        schema=settings_json_schema,
        cls=jsonschema.Draft4Validator,
    )
