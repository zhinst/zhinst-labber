import pytest
import json
from pathlib import Path
from zhinst.toolkit import Session
from unittest.mock import patch


@pytest.fixture
def settings_json():
    settings_file = Path(__file__).parent.parent / "src/zhinst/labber/resources/settings.json"
    with open(settings_file, "r") as json_f:
        return json.load(json_f)

@pytest.fixture()
def data_dir():
    yield Path(__file__).parent / "data" / "toolkit"


@pytest.fixture()
def nodedoc_zi_json(data_dir):
    json_path = data_dir / "nodedoc_zi.json"
    with json_path.open("r", encoding="UTF-8") as file:
        return file.read()

@pytest.fixture()
def session(nodedoc_zi_json, mock_connection):
    mock_connection.return_value.listNodesJSON.return_value = nodedoc_zi_json
    yield Session("localhost")


@pytest.fixture()
def mock_connection():
    with patch(
        "zhinst.toolkit.session.core.ziDAQServer", autospec=True
    ) as connection:
        with patch(
        "zhinst.toolkit.driver.modules.shfqa_sweeper.ziDAQServer", autospec=True
        ) as _:
            connection.return_value.host = "localhost"
            connection.return_value.port = 8004
            yield connection
