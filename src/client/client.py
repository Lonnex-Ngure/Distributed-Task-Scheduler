#src/client.client.py

import os
import ssl
import socket
import json
import threading
import time
from dotenv import load_dotenv
from ..utils.crypto import encrypt_message, decrypt_message

load_dotenv()

class TaskClient:
    def __init__(self):
        self.host = os.getenv('SERVER_HOST', 'localhost')
        self.port = int(os.getenv('SERVER_PORT', 5000))
        self.auth_token = None
        self.connected = False
        self.task_callbacks = {}
        
        # Setup SSL context
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
    def connect(self):
        """Connect to the task server"""
        try:
            # Create socket and wrap with SSL
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.ssl_socket = self.ssl_context.wrap_socket(self.socket)
            self.ssl_socket.connect((self.host, self.port))
            
            # Start listener thread
            self.listener_thread = threading.Thread(target=self._listen)
            self.listener_thread.daemon = True
            self.listener_thread.start()
            
            self.connected = True
            return True
            
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
            
    def login(self, username, password):
        """Authenticate with the server"""
        auth_data = {
            'type': 'auth',
            'username': username,
            'password': password
        }
        
        self.send_message(auth_data)
        response = self._wait_for_response('auth')
        
        if response and response.get('status') == 'success':
            self.auth_token = response.get('token')
            return True
        return False
        
    def submit_task(self, task_data, callback=None):
        """Submit a task to the server"""
        if not self.auth_token:
            raise Exception("Not authenticated")
            
        message = {
            'type': 'task_submit',
            'token': self.auth_token,
            'data': task_data
        }
        
        self.send_message(message)
        response = self._wait_for_response('task_submit')
        
        if response and response.get('status') == 'success':
            task_id = response.get('task_id')
            if callback:
                self.task_callbacks[task_id] = callback
            return task_id
        return None
        
    def get_task_status(self, task_id):
        """Get the status of a task"""
        if not self.auth_token:
            raise Exception("Not authenticated")
            
        message = {
            'type': 'task_status',
            'token': self.auth_token,
            'task_id': task_id
        }
        
        self.send_message(message)
        response = self._wait_for_response('task_status')
        
        if response and response.get('status') == 'success':
            return response.get('task_status')
        return None
        
    def cancel_task(self, task_id):
        """Cancel a running task"""
        if not self.auth_token:
            raise Exception("Not authenticated")
            
        message = {
            'type': 'cancel_task',
            'token': self.auth_token,
            'task_id': task_id
        }
        
        self.send_message(message)
        response = self._wait_for_response('cancel_task')
        
        return response and response.get('status') == 'success'
        
    def send_message(self, message):
        """Send an encrypted message to the server"""
        if not self.connected:
            raise Exception("Not connected to server")
            
        encrypted_message = encrypt_message(json.dumps(message))
        self.ssl_socket.send(encrypted_message)
        
    def _listen(self):
        """Listen for server messages"""
        while self.connected:
            try:
                data = self.ssl_socket.recv(4096)
                if not data:
                    self.connected = False
                    break
                    
                message = json.loads(decrypt_message(data).decode())
                self._handle_message(message)
                
            except Exception as e:
                print(f"Error in listener: {e}")
                time.sleep(1)
                
    def _handle_message(self, message):
        """Handle incoming messages from the server"""
        message_type = message.get('type')
        
        if message_type == 'task_update':
            task_id = message.get('task_id')
            if task_id in self.task_callbacks:
                self.task_callbacks[task_id](message)
                
        elif message_type == 'error':
            print(f"Server error: {message.get('message')}")
            
    def _wait_for_response(self, message_type, timeout=5):
        """Wait for a specific response from the server"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Implementation of waiting for specific response
            time.sleep(0.1)
        return None
        
    def close(self):
        """Close the connection"""
        self.connected = False
        if hasattr(self, 'ssl_socket'):
            self.ssl_socket.close()

def main():
    """Example usage of the TaskClient"""
    client = TaskClient()
    
    if not client.connect():
        print("Failed to connect to server")
        return
        
    if not client.login('admin', 'admin123'):
        print("Authentication failed")
        return
        
    def task_callback(update):
        print(f"Task update: {update}")
        
    # Example task submission
    task_data = {
        'type': 'computation',
        'data': {
            'operation': 'sum',
            'numbers': [1, 2, 3, 4, 5]
        }
    }
    
    task_id = client.submit_task(task_data, task_callback)
    if task_id:
        print(f"Task submitted with ID: {task_id}")
        
        # Wait for result
        while True:
            status = client.get_task_status(task_id)
            if status['status'] in ['completed', 'failed']:
                print(f"Task finished with status: {status}")
                break
            time.sleep(1)
    
    client.close()

if __name__ == "__main__":
    main()