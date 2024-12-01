# src/server/main.py

import os
import ssl
import socket
import threading
import json
from flask import Flask
from flask_socketio import SocketIO
from dotenv import load_dotenv
from ..utils.crypto import encrypt_message, decrypt_message
from .task_manager import TaskManager
from .auth import AuthManager

load_dotenv()

class DistributedServer:
    def __init__(self):
        self.host = os.getenv('SERVER_HOST', 'localhost')
        self.port = int(os.getenv('SERVER_PORT', 5000))
        self.task_manager = TaskManager()
        self.auth_manager = AuthManager()
        self.workers = []
        self.clients = []
        self.running = True

        # Initialize Flask app
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app)
        self.setup_routes()

        # Setup SSL context
        self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.ssl_context.load_cert_chain(
            certfile="certificates/server.crt",
            keyfile="certificates/server.key"
        )

        # Initialize server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)

    def setup_routes(self):
        @self.socketio.on('connect')
        def handle_connect():
            print("Client connected via WebSocket")

        @self.socketio.on('submit_task')
        def handle_task(data):
            task_id = self.task_manager.submit_task(data)
            return {'task_id': task_id}

        @self.socketio.on('task_status')
        def handle_status(task_id):
            status = self.task_manager.get_task_status(task_id)
            return {'status': status}

    def start(self):
        # Start Flask in a separate thread
        flask_thread = threading.Thread(
            target=self.socketio.run,
            args=(self.app,),
            kwargs={
                'host': self.host,
                'port': int(os.getenv('FLASK_PORT', 8000)),
                'debug': False
            }
        )
        flask_thread.start()

        # Start accepting connections
        print(f"Server listening on {self.host}:{self.port}")
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                ssl_socket = self.ssl_context.wrap_socket(
                    client_socket,
                    server_side=True
                )
                print(f"New connection from {address}")

                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(ssl_socket, address)
                )
                client_thread.start()

            except Exception as e:
                print(f"Error accepting connection: {e}")

    def handle_client(self, client_socket, address):
        try:
            # Perform authentication
            auth_data = json.loads(decrypt_message(
                client_socket.recv(1024)
            ).decode())
            
            if not self.auth_manager.authenticate(
                auth_data.get('username'),
                auth_data.get('password')
            ):
                client_socket.send(
                    encrypt_message(
                        json.dumps({'status': 'error', 'message': 'Authentication failed'})
                    )
                )
                client_socket.close()
                return

            # Handle client messages
            while self.running:
                try:
                    data = decrypt_message(client_socket.recv(1024))
                    if not data:
                        break

                    message = json.loads(data.decode())
                    response = self.process_message(message)
                    
                    client_socket.send(encrypt_message(
                        json.dumps(response)
                    ))

                except Exception as e:
                    print(f"Error handling client {address}: {e}")
                    break

        finally:
            client_socket.close()

    def process_message(self, message):
        try:
            if message['type'] == 'task_submit':
                task_id = self.task_manager.submit_task(message['data'])
                return {'status': 'success', 'task_id': task_id}

            elif message['type'] == 'task_status':
                status = self.task_manager.get_task_status(message['task_id'])
                return {'status': 'success', 'task_status': status}

            elif message['type'] == 'register_worker':
                self.workers.append(message['worker_info'])
                return {'status': 'success', 'message': 'Worker registered'}

            return {'status': 'error', 'message': 'Unknown message type'}

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def stop(self):
        self.running = False
        self.server_socket.close()

if __name__ == "__main__":
    server = DistributedServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("Shutting down server...")
        server.stop()

