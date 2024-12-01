# src/web/app.py
from socket import socket
from flask import Flask
from flask_socketio import SocketIO
from dotenv import load_dotenv
import os
from pathlib import Path
from ..utils.crypto import generate_token
from ..server.auth import AuthManager
from ..server.task_manager import TaskManager
from .routes import routes, init_routes  # Import the init_routes function

load_dotenv()

# Get the absolute path to the static folder
static_folder = str(Path(__file__).parent.parent / 'static')
template_folder = str(Path(__file__).parent / 'templates')

app = Flask(__name__, 
           static_folder=static_folder,
           static_url_path='/static',
           template_folder=template_folder)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')
socketio = SocketIO(app)
auth_manager = AuthManager()

# Initialize routes with socketio instance
init_routes(socketio)

# Register the blueprint
app.register_blueprint(routes)

if __name__ == '__main__':
    socketio.run(app, 
                host=os.getenv('SERVER_HOST', 'localhost'),
                port=int(os.getenv('FLASK_PORT', 5000)),
                debug=os.getenv('DEBUG', 'False').lower() == 'true')