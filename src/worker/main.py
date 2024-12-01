import os
import ssl
import socket
import threading
import json
import time
from dotenv import load_dotenv
from ..utils.crypto import encrypt_message, decrypt_message
from .task_executor import TaskExecutor

load_dotenv()

class WorkerNode:
    def __init__(self):
        self.host = os.getenv('SERVER_HOST', 'localhost')
        self.port = int(os.getenv('SERVER_PORT', 5000))
        self.worker_id = os.getenv('WORKER_ID', f'worker-{os.getpid()}')
        self.task_executor = TaskExecutor()
        self.running = True
        self.current_task = None
        self.use_ssl = False  # Toggle this to True when using SSL in production
        
    def connect(self):
        try:
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            if self.use_ssl:
                # SSL configuration for production
                self.ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
                self.ssl_context.check_hostname = False
                self.ssl_context.verify_mode = ssl.CERT_NONE
                self.connection = self.ssl_context.wrap_socket(
                    self.socket,
                    server_hostname=self.host
                )
            else:
                # Direct socket connection for development
                self.connection = self.socket
            
            # Connect to server
            self.connection.connect((self.host, self.port))
            
            # Register with server
            registration_data = {
                'type': 'register_worker',
                'worker_info': {
                    'id': self.worker_id,
                    'capabilities': self.task_executor.get_capabilities()
                }
            }
            self.send_message(registration_data)
            
            print(f"Successfully connected to server at {self.host}:{self.port}")
            return True
            
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
            
    def start(self):
        if not self.connect():
            return
        
        print(f"Worker {self.worker_id} connected to server")
        
        # Start heartbeat thread
        heartbeat_thread = threading.Thread(target=self.send_heartbeat)
        heartbeat_thread.daemon = True
        heartbeat_thread.start()
        
        # Main work loop
        while self.running:
            try:
                # Request new task if not currently working
                if not self.current_task:
                    self.request_task()
                
                # Process server messages
                self.process_server_messages()
                
                time.sleep(0.1)  # Prevent CPU hogging
                
            except Exception as e:
                print(f"Error in work loop: {e}")
                time.sleep(5)  # Wait before retry
                
    def request_task(self):
        request = {
            'type': 'request_task',
            'worker_id': self.worker_id
        }
        self.send_message(request)
        
    def process_server_messages(self):
        try:
            data = self.connection.recv(4096)
            if not data:
                return
            
            message = json.loads(decrypt_message(data).decode())
            
            if message['type'] == 'task_assignment':
                self.handle_task_assignment(message['task'])
            elif message['type'] == 'cancel_task':
                self.handle_task_cancellation(message['task_id'])
                
        except socket.timeout:
            pass
        except Exception as e:
            print(f"Error processing message: {e}")
            
    def handle_task_assignment(self, task_data):
        self.current_task = task_data
        
        # Set up progress callback
        def progress_callback(task_id, status, progress):
            self.send_status_update(task_id, status, progress)
        
        self.task_executor.update_callback = progress_callback
        
        # Execute task in separate thread
        execution_thread = threading.Thread(
            target=self.execute_task,
            args=(task_data,)
        )
        execution_thread.start()
        
    def execute_task(self, task_data):
        try:
            # Execute the task
            result = self.task_executor.execute_task(task_data)
            
            # Send result back to server
            self.send_task_result(task_data['id'], result)
            
        except Exception as e:
            self.send_task_failure(task_data['id'], str(e))
            
        finally:
            self.current_task = None
            
    def send_task_result(self, task_id, result):
        message = {
            'type': 'task_complete',
            'task_id': task_id,
            'result': result
        }
        self.send_message(message)
        
    def send_task_failure(self, task_id, error):
        message = {
            'type': 'task_failed',
            'task_id': task_id,
            'error': error
        }
        self.send_message(message)
        
    def send_status_update(self, task_id, status, progress=None):
        message = {
            'type': 'status_update',
            'task_id': task_id,
            'status': status,
            'progress': progress
        }
        self.send_message(message)
        
    def send_heartbeat(self):
        while self.running:
            try:
                message = {
                    'type': 'heartbeat',
                    'worker_id': self.worker_id,
                    'status': 'alive',
                    'current_task': self.current_task
                }
                self.send_message(message)
                time.sleep(30)  # Send heartbeat every 30 seconds
            except Exception as e:
                print(f"Error sending heartbeat: {e}")
                
    def send_message(self, message):
        encrypted_message = encrypt_message(json.dumps(message).encode())
        self.connection.send(encrypted_message)
        
    def stop(self):
        self.running = False
        if hasattr(self, 'connection'):
            self.connection.close()

if __name__ == "__main__":
    worker = WorkerNode()
    try:
        worker.start()
    except KeyboardInterrupt:
        print("Shutting down worker...")
        worker.stop()