import pytest
from src.worker.main import WorkerNode
from src.worker.task_executor import TaskExecutor

@pytest.fixture
def worker():
    worker = WorkerNode()
    yield worker
    worker.stop()

def test_worker_initialization(worker):
    assert worker.worker_id.startswith('worker-')
    assert isinstance(worker.task_executor, TaskExecutor)

def test_task_execution():
    executor = TaskExecutor()
    task_data = {
        'type': 'computation',
        'data': {
            'operation': 'sum',
            'numbers': [1, 2, 3, 4, 5]
        }
    }
    result = executor.execute_task(task_data)
    assert result['result'] == 15
