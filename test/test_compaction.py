import pytest
from unittest.mock import patch
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

def test_create_compacted_files(compaction):
    
    

