import pytest
import json
from src.server.main import DistributedServer
from src.server.task_manager import TaskManager

@pytest.fixture
def server():
    server = DistributedServer()
    yield server
    server.stop()

def test_server_initialization(server):
    assert server.host == 'localhost'
    assert server.port == 5000
    assert isinstance(server.task_manager, TaskManager)

def test_task_submission(server):
    task_data = {
        'type': 'computation',
        'data': {'operation': 'sum', 'numbers': [1, 2, 3]}
    }
    task_id = server.task_manager.submit_task(task_data)
    assert task_id is not None
    status = server.task_manager.get_task_status(task_id)
    assert status['status'] == 'pending'