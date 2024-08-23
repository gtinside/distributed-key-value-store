import pytest
from unittest.mock import patch, MagicMock
from compaction.compaction import Compaction
from collections import defaultdict

# Fixing the scope this will make sure that the compaction object is created only once
@pytest.fixture(scope='session')
def compaction():
    yield Compaction(max_data_files=2, data_dir='/tmp')

@patch('glob.glob')
def test_can_compact(mock_glob, compaction):
    mock_glob.return_value = ['file1.index', 'file2.index']
    assert compaction.can_compact() == True

@patch('json.load')
@patch('builtins.open')
def test_prepare_data(mock_open, mock_json_load, compaction):
    index_files = ['file1.index', 'file2.index']
    key_offset_map = dict()
    file_key_map = defaultdict(set)
    mock_json_load.return_value = {"name": {"key": "name", "value": "somename", "timestamp": 123456, "deleted": False}}
    compaction.prepare_data(index_files=index_files, file_key_map=file_key_map, 
                            key_offset_map=key_offset_map)
    assert len(key_offset_map) != 0

@patch('os.rename')
@patch('json.dump')
@patch('builtins.open')
def test_create_compacted_files(mock_open, mock_json_dump, mock_os_rename, compaction):
    mock_compacted_data_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_compacted_data_file
    file_key_map = {"sample_data_1.data":["key1", "key2"], "sample_data_2.data":["key3"]}
    key_offset_map = {"key1": {"start": 1, "end": 10, "timestamp": 12345, "deleted": "False"},
                      "key2": {"start": 11, "end": 20, "timestamp": 12355, "deleted": "False"},
                      "key3": {"start": 21, "end": 30, "timestamp": 12365, "deleted": "False"},
                      "key4": {"start": 31, "end": 40, "timestamp": 12375, "deleted": "False"}
                      }
    mock_compacted_data_file.seek.return_value = 1
    mock_compacted_data_file.read.return_value = "something".encode()
    writes  = MagicMock()
    mock_compacted_data_file.write = writes
    compaction.data_dir = "/tmp"
    compaction.create_compacted_files(file_key_map=file_key_map, key_offset_map=key_offset_map, 
                                      index_files=["sample_data_1.index", "sample_data_2.index"])
    writes.assert_called_with("something".encode())
    writes.assert_called()
    assert writes.call_count == 3
    mock_os_rename.assert_called()
    assert mock_os_rename.call_count == 4


    

