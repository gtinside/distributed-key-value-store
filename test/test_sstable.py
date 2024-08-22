import pytest
import json
from unittest.mock import patch, MagicMock
from lsmt.sstable import SSTable
from utils.model import Data

@pytest.fixture(scope='session')
def sstable():
    yield SSTable()

@patch.object(SSTable, 'read_data_file')
@patch('json.load')
@patch('glob.glob')
@patch('builtins.open')
def test_get_data(mock_open, mock_glob, mock_json, mock_read_data_file, sstable):
    mock_file = MagicMock()
    mock_glob.return_value = ["dummy_index_file.index"]
    mock_open.return_value = mock_file
    mock_json.return_value = {"name": {"key":"name", "start": 1, "end": 10}}

    result = sstable.get_data("name")
    assert isinstance(result, MagicMock)

@patch('builtins.open')
def test_read_data_file(mock_open, sstable):
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    mock_file.seek.return_value = None
    mock_file.read.return_value = "name:noname:12345:False".encode()

    assert sstable.read_data_file('mock_file.data', 1, 10) == Data(key="name", value="noname", timestamp=12345, deleted=False)







