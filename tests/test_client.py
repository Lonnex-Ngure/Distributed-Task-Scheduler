import pytest
import requests
from src.client.client import DistributedClient

@pytest.fixture
def client():
    return DistributedClient('localhost', 5000)

def test_client_connection(client):
    assert client.connect() is True

def test_task_submission(client):
    task_data = {
        'type': 'computation',
        'data': {'operation': 'sum', 'numbers': [1, 2, 3]}
    }
    response = client.submit_task(task_data)
    assert 'task_id' in response
    
def test_task_status(client):
    task_data = {
        'type': 'computation',
        'data': {'operation': 'sum', 'numbers': [1, 2, 3]}
    }
    response = client.submit_task(task_data)
    task_id = response['task_id']
    status = client.get_task_status(task_id)
    assert 'status' in status