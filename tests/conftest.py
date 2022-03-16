import pytest
import json
from pathlib import Path


@pytest.fixture
def settings_json():
    settings_file = Path(__file__).parent.parent / "src" / "zhinst" /"labber" / "settings.json"
    with open(settings_file, "r") as json_f:
        return json.load(json_f)
