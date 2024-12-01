# Quick fix for src/server/task_manager.py
import uuid
import threading
import time

class TaskManager:
    def __init__(self, socketio):
        self.socketio = socketio
        self.tasks = {}
        
    def submit_task(self, task_data, priority):
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {
            'status': 'pending',
            'progress': 0,
            'type': task_data['type'],
            'priority': priority
        }
        
        # Start a thread to simulate progress
        thread = threading.Thread(target=self._simulate_progress, args=(task_id,))
        thread.start()
        
        return task_id
        
    def _simulate_progress(self, task_id):
        """Simulate task progress"""
        progress = 0
        self.tasks[task_id]['status'] = 'running'
        
        while progress < 100:
            time.sleep(0.5)  # Update every 0.5 seconds
            progress += 10
            self.tasks[task_id]['progress'] = progress
            
            if self.socketio:
                self.socketio.emit('task_update', {
                    'task_id': task_id,
                    'status': 'running',
                    'progress': progress
                })
        
        self.tasks[task_id]['status'] = 'completed'
        if self.socketio:
            self.socketio.emit('task_update', {
                'task_id': task_id,
                'status': 'completed',
                'progress': 100
            })