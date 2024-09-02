import pytest
from unittest.mock import patch, MagicMock
from impl.consistent_hashing import ConsistentHashingImpl
from lsmt.mem_table import MemTable
from lsmt.sstable import SSTable
from scheduler.scheduler import Scheduler
from exception.exceptions import NoDataFoundException
from server.server import Server
from utils.model import Data


# Fixture scoped to the entire test session
@pytest.fixture(scope="session")
def server():
    with patch("server.server.KazooClient") as MockKazooClient:
        # Return a single instance of the Server object
        yield Server(
            zk_host="localhost",
            zk_port=2181,
            host="localhost",
            port=8000,
            private_ip="127.0.0.1",
        )


def test_server_initialization(server):
    assert isinstance(server._consistent_hash, ConsistentHashingImpl)
    assert isinstance(server._cache, MemTable)
    assert isinstance(server._ss_table, SSTable)
    assert isinstance(server._scheduler, Scheduler)


@patch("lsmt.mem_table.MemTable.add")
def test_add_data(mock_add, server):
    data = Data(key="key", value="value")
    server.add_data(data)
    mock_add.assert_called_once_with(data)


@patch("lsmt.mem_table.MemTable.get_data")
@patch("lsmt.sstable.SSTable.get_data")
def test_get_data(mock_sstable_get, mock_cache_get, server):
    data = Data(key="key", value="value")
    mock_cache_get.return_value = data
    assert server.get_data("key").value == data.value

    mock_cache_get.side_effect = NoDataFoundException("Not found")
    mock_sstable_get.return_value = data
    assert server.get_data("key") == data

    data.deleted = True
    with pytest.raises(NoDataFoundException):
        server.get_data("key")


@patch("kazoo.client.KazooClient")
@patch("impl.consistent_hashing.ConsistentHashingImpl.add_node")
@patch("server.server.Server.check_if_leader")
def test_watch_for_child_nodes(
    mock_check_if_leader, mock_add_node, mock_kazoo_client, server
):
    mock_zk = mock_kazoo_client.return_value
    mock_zk.get_children.return_value = ["n_1"]
    mock_zk.get.return_value = (b"localhost:8000", None)
    mock_check_if_leader.return_value = True

    server._id_host_map = {}
    event = MagicMock(state="CONNECTED")
    server.zk_connection = mock_zk
    server.watch_for_child_nodes(event)
    mock_add_node.assert_called_once_with("1")
    assert server._id_host_map["1"] == "localhost:8000"


@patch("kazoo.client.KazooClient")
def test_check_if_leader(mock_kazoo_client, server):
    mock_zk = mock_kazoo_client.return_value
    mock_zk.get_children.return_value = ["n_1", "n_2"]

    server.identifier = 1
    assert server.check_if_leader() is True

    server.identifier = 2
    assert server.check_if_leader() is False


@patch("kazoo.client.KazooClient")
def test_get_all_nodes(mock_kazoo_client, server):
    mock_zk = mock_kazoo_client.return_value
    server.zk_connection = mock_zk
    mock_zk.get_children.return_value = ["n_1", "n_2"]

    nodes = server.get_all_nodes()
    assert nodes == ["n_1", "n_2"]


@patch("kazoo.client.KazooClient")
def test_start_server(mock_kazoo_client, server):
    mock_zk = mock_kazoo_client.return_value
    mock_zk.ensure_path.return_value = True
    mock_zk.create.return_value = "/election/n_1"
    mock_zk.get_children.return_value = []
    server.zk_connection = mock_zk

    server.start()
    mock_zk.create.assert_called_once_with(
        "/election/n_", ephemeral=True, sequence=True, value=b"127.0.0.1:8000"
    )
    assert server.identifier == 1
    mock_zk.get_children.assert_called_once_with(
        "/election", watch=server.watch_for_child_nodes
    )
