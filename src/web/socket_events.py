# src/web/socket_events.py
from flask_socketio import emit

def init_socket_events(socketio, task_manager):
    @socketio.on('connect')
    def handle_connect():
        print('Client connected')
        # Send current tasks state
        tasks = task_manager.get_all_tasks()
        emit('initial_tasks', tasks)

    @socketio.on('subscribe_task')
    def handle_task_subscribe(task_id):
        print(f'Client subscribed to task {task_id}')

    return socketio