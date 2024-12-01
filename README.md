# Distributed Task Scheduler

A scalable distributed task scheduling system built with Python, featuring a central server, multiple worker nodes, and a web interface for task management.

## Features

- Distributed task execution across multiple worker nodes
- Real-time task status updates via WebSocket
- Secure communication with SSL/TLS
- Web interface for task submission and monitoring
- Priority-based task scheduling
- Automatic task retries
- Worker node health monitoring

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd distributed_task_scheduler
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
- Copy `.env.example` to `.env`
- Modify the variables as needed

## Running the System

1. Start the server:
```bash
python -m src.server.main
```

2. Start worker nodes (can run multiple):
```bash
python -m src.worker.main
```

3. Start the web interface:
```bash
python -m src.web.app
```

## Usage

1. Access the web interface at `http://localhost:5000`
2. Log in with your credentials
3. Submit tasks through the dashboard
4. Monitor task progress in real-time

## Testing

Run the test suite:
```bash
pytest tests/
```

## Security

- All communication is encrypted using SSL/TLS
- Authentication required for all operations
- Secure token-based session management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details