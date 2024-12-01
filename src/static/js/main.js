// src/static/js/main.js

let socket;
let activeTasks = new Map();

// Initialize Socket.IO connection
function initializeSocket() {
    socket = io({
        transports: ['websocket'],
        reconnection: true,
        reconnectionAttempts: 5
    });

    socket.on('connect', () => {
        console.log('Connected to WebSocket server');
        showNotification('Connected to server', 'success');
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        showNotification('Connection lost. Attempting to reconnect...', 'error');
    });

    // Handle task updates from server
    socket.on('task_update', (data) => {
        console.log('Received task update:', data);
        updateTaskUI(data);
    });
}

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', () => {
    initializeSocket();
    initializeTaskForm();
});

// Initialize task form
function initializeTaskForm() {
    const taskForm = document.getElementById('taskForm');
    if (!taskForm) return;

    taskForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const submitBtn = taskForm.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        
        const taskData = {
            type: document.getElementById('taskType').value,
            data: document.getElementById('taskData').value,
            priority: parseInt(document.getElementById('priority').value)
        };

        try {
            const response = await fetch('/api/tasks', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': getCsrfToken()
                },
                body: JSON.stringify(taskData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            if (result.task_id) {
                addTaskToUI(result.task_id, taskData);
                socket.emit('subscribe_task', result.task_id);
                showNotification('Task submitted successfully!', 'success');
                taskForm.reset();
            }
        } catch (error) {
            console.error('Error submitting task:', error);
            showNotification('Failed to submit task: ' + error.message, 'error');
        } finally {
            submitBtn.disabled = false;
        }
    });
}

// Add task to UI
function addTaskToUI(taskId, taskData) {
    const taskElement = document.createElement('div');
    taskElement.id = `task-${taskId}`;
    taskElement.className = 'task-item pending';
    
    taskElement.innerHTML = `
        <div class="task-header">
            <h3>Task #${taskId}</h3>
            <span class="task-status">Pending</span>
        </div>
        <div class="task-details">
            <p><strong>Type:</strong> ${taskData.type}</p>
            <p><strong>Priority:</strong> ${getPriorityLabel(taskData.priority)}</p>
            <p><strong>Data:</strong> ${truncateText(taskData.data, 100)}</p>
        </div>
        <div class="task-progress">
            <div class="progress-bar">
                <div class="progress-fill" style="width: 0%"></div>
            </div>
            <span class="progress-text">0%</span>
        </div>
    `;
    
    const activeTasksContainer = document.getElementById('activeTasks');
    if (activeTasksContainer) {
        activeTasksContainer.insertBefore(taskElement, activeTasksContainer.firstChild);
        activeTasks.set(taskId, taskElement);
    }
}

// Update task UI based on server updates
function updateTaskUI(data) {
    const taskElement = document.getElementById(`task-${data.task_id}`);
    if (!taskElement) return;

    // Update status
    const statusSpan = taskElement.querySelector('.task-status');
    if (statusSpan) {
        statusSpan.textContent = data.status;
        taskElement.className = `task-item ${data.status.toLowerCase()}`;
    }

    // Update progress
    if (data.progress !== undefined) {
        const progressFill = taskElement.querySelector('.progress-fill');
        const progressText = taskElement.querySelector('.progress-text');
        if (progressFill && progressText) {
            progressFill.style.width = `${data.progress}%`;
            progressText.textContent = `${data.progress}%`;
        }
    }

    // Remove completed or failed tasks after delay
    if (data.status === 'Completed' || data.status === 'Failed') {
        setTimeout(() => {
            taskElement.classList.add('fade-out');
            setTimeout(() => taskElement.remove(), 500);
            activeTasks.delete(data.task_id);
        }, 5000);
    }
}

// Helper functions
function getPriorityLabel(priority) {
    const labels = { 0: 'High', 1: 'Medium', 2: 'Low' };
    return labels[priority] || 'Unknown';
}

function truncateText(text, maxLength) {
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 500);
    }, 3000);
}

function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.content;
}