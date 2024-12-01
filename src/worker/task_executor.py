import time
import json
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
import numpy as np

class TaskExecutor:
    def __init__(self):
        self.executor = ThreadPoolExecutor(
            max_workers=multiprocessing.cpu_count()
        )
        self.task_handlers = {
            'computation': self.handle_computation,
            'io_operation': self.handle_io_operation,
            'data_processing': self.handle_data_processing
        }
        self.update_callback = None
        
    def get_capabilities(self):
        return list(self.task_handlers.keys())

    def execute_task(self, task_data):
        """Execute task and report progress"""
        try:
            task_type = task_data['type']
            if task_type not in self.task_handlers:
                raise ValueError(f"Unsupported task type: {task_type}")
                
            handler = self.task_handlers[task_type]
            
            # Simulate progress updates
            total_steps = 10
            for step in range(total_steps):
                # Do actual work
                if step == total_steps - 1:
                    result = handler(task_data['data'])
                
                # Send progress update through worker's socket connection
                progress = int((step + 1) / total_steps * 100)
                if self.update_callback:
                    self.update_callback(task_data['id'], 'running', progress)
                time.sleep(0.5)  # Simulate work
                
            return result
            
        except Exception as e:
            raise Exception(f"Task execution error: {str(e)}")
        
    def handle_computation(self, data):
        """Handle computational tasks like mathematical operations"""
        try:
            operation = data.get('operation', 'sum')
            numbers = data.get('numbers', [])
            
            if operation == 'sum':
                return {'result': sum(numbers)}
            elif operation == 'average':
                return {'result': sum(numbers) / len(numbers)}
            elif operation == 'matrix_multiply':
                matrix1 = np.array(data.get('matrix1'))
                matrix2 = np.array(data.get('matrix2'))
                result = np.matmul(matrix1, matrix2)
                return {'result': result.tolist()}
            else:
                raise ValueError(f"Unsupported operation: {operation}")
                
        except Exception as e:
            raise Exception(f"Computation error: {str(e)}")
            
    def handle_io_operation(self, data):
        """Handle I/O operations like file processing"""
        try:
            operation = data.get('operation')
            
            if operation == 'read':
                with open(data['filename'], 'r') as f:
                    content = f.read()
                return {'content': content}
                
            elif operation == 'write':
                with open(data['filename'], 'w') as f:
                    f.write(data['content'])
                return {'status': 'success'}
                
            else:
                raise ValueError(f"Unsupported I/O operation: {operation}")
                
        except Exception as e:
            raise Exception(f"I/O error: {str(e)}")
            
    def handle_data_processing(self, data):
        """Handle data processing tasks like filtering, sorting, etc."""
        try:
            operation = data.get('operation')
            input_data = data.get('data', [])
            
            if operation == 'sort':
                return {
                    'result': sorted(
                        input_data,
                        key=lambda x: x.get(data.get('key', 'id'))
                    )
                }
                
            elif operation == 'filter':
                condition = data.get('condition', {})
                filtered = [
                    item for item in input_data
                    if all(item.get(k) == v for k, v in condition.items())
                ]
                return {'result': filtered}
                
            elif operation == 'transform':
                transformation = data.get('transformation', {})
                transformed = []
                for item in input_data:
                    new_item = item.copy()
                    for key, transform in transformation.items():
                        if transform == 'uppercase':
                            new_item[key] = str(new_item.get(key, '')).upper()
                        elif transform == 'lowercase':
                            new_item[key] = str(new_item.get(key, '')).lower()
                    transformed.append(new_item)
                return {'result': transformed}
                
            else:
                raise ValueError(f"Unsupported data processing operation: {operation}")
                
        except Exception as e:
            raise Exception(f"Data processing error: {str(e)}")