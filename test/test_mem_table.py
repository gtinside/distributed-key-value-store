import pytest
from unittest.mock import patch, MagicMock
from lsmt.mem_table import MemTable
from utils.model import Data


@pytest.fixture(scope='session')
def memtable():
    yield MemTable()


@patch('builtins.open')
def test_flush(mock_open, memtable):
    mock_write = MagicMock()
    # this simulates the file object being return my open function
    mock_file = mock_open.return_value.__enter__.return_value
    user_data = Data(key="name", value="somename")
    memtable.add(user_data)

    mock_file.write = mock_write
    memtable.flush()
    
    data = f"name:{user_data.value}:{user_data.timestamp}:{user_data.deleted}".encode()
    mock_write.assert_any_call(data)

