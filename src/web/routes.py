# src/web/routes.py

from flask import current_app
from flask_socketio import SocketIO
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import emit
from ..server.task_manager import TaskManager
from ..utils.logger import logger

routes = Blueprint('routes', __name__)
task_manager = None
socketio = None

def init_routes(socketio_instance):
    global task_manager, socketio
    socketio = socketio_instance
    task_manager = TaskManager(socketio_instance)
    
    # Socket.IO event handlers
    @socketio.on('connect')
    def handle_connect():
        logger.info('Client connected')

    @socketio.on('subscribe_task')
    def handle_task_subscription(task_id):
        logger.info(f'Client subscribed to task: {task_id}')

@routes.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('routes.login'))
    return render_template('dashboard.html')

@routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # For demo purposes, use simple authentication
        if username == "admin" and password == "admin":
            session['user_id'] = username
            logger.info(f"User {username} logged in successfully")
            return redirect(url_for('routes.index'))
        
        logger.warning(f"Failed login attempt for user {username}")
        return render_template('login.html', error="Invalid credentials")
    
    return render_template('login.html')

@routes.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('routes.login'))

@routes.route('/api/tasks', methods=['POST'])
def create_task():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    task_data = request.json
    priority = int(task_data.get('priority', 2))
    task_id = task_manager.submit_task(task_data, priority)
    
    logger.info(f"New task created: {task_id}")
    return jsonify({'task_id': task_id})

@routes.route('/api/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    task = task_manager.get_task_status(task_id)
    if task is None:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(task)

@routes.route('/api/workers', methods=['GET'])
def get_workers():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    workers = task_manager.get_worker_status()
    return jsonify(workers)

def handle_task_update(task_id, status):
    """Emit task update to connected clients"""
    if socketio:
        socketio.emit('task_update', {
            'task_id': task_id,
            'status': status
        }, broadcast=True)