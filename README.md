# Lease Exit System

A comprehensive workflow automation system for managing lease exit processes using AI-powered agents and the Crew AI framework.

## Overview

The Lease Exit System automates the complex process of exiting leases, managing forms, approvals, and notifications to all stakeholders. The application orchestrates multiple specialized AI agents to handle different aspects of the lease exit workflow.

## Key Features

- **AI-Powered Workflow Management**: Automated process orchestration using specialized AI agents
- **Dynamic Form Generation**: Context-aware form creation and validation
- **Approval Management**: Structured approval processes with role-based permissions
- **Automated Notifications**: Timely notifications to all stakeholders
- **Audit Trail**: Complete history of all activities and decisions
- **Integration Capabilities**: Connects with external systems via APIs

## Architecture

### Backend

- **Framework**: FastAPI
- **Database**: MongoDB
- **AI Orchestration**: Crew AI Framework
- **Task Queue**: Celery with Redis

### Frontend

- **Framework**: React with Material UI
- **State Management**: React Query
- **Forms**: Formik with Yup validation

## Specialized Agents

- **Workflow Designer Agent**: Designs and optimizes lease exit workflows
- **Form Creator Agent**: Generates dynamic forms based on lease context
- **Approval Architect Agent**: Manages the approval process
- **Notification Specialist Agent**: Handles all stakeholder communications

## Setup and Installation

### Prerequisites

- Python 3.9+
- Node.js 16+
- MongoDB
- Redis (for Celery task queue)
- OpenAI API key (for AI agents)

### Environment Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/lease-exit-system.git
   cd lease-exit-system
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Configure your `.env` file with the following variables:
   ```
   # Database Configuration
   MONGODB_URI=mongodb://localhost:27017/lease_exit_system

   # OpenAI Configuration
   OPENAI_API_KEY=your-openai-api-key
   OPENAI_MODEL=gpt-4

   # Email Configuration
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-specific-password
   FROM_EMAIL=your-email@gmail.com

   # Redis/Celery Configuration
   REDIS_URL=redis://localhost:6379/0
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
   ```

### Installing Redis on macOS

1. Install Redis using Homebrew:
   ```bash
   brew install redis
   ```

2. Start Redis as a service (optional):
   ```bash
   brew services start redis
   ```

3. Alternatively, start Redis manually:
   ```bash
   redis-server
   ```

### Installing and Configuring Celery on macOS

1. Celery should already be installed as part of the requirements.txt, but you can install it separately if needed:
   ```bash
   pip install celery
   ```

2. Install Flower for monitoring Celery tasks:
   ```bash
   pip install flower
   ```

3. If you encounter permissions issues with Celery on macOS, you may need to:
   ```bash
   # Create a celery user group (if it doesn't exist)
   sudo dscl . -create /Groups/celery
   sudo dscl . -create /Groups/celery PrimaryGroupID 1000
   
   # Add your user to the celery group
   sudo dscl . -append /Groups/celery GroupMembership $(whoami)
   ```

4. If you encounter issues with Celery not finding the Redis socket, ensure Redis is running and check your Redis URL in the .env file.

### Running the Backend

1. Start MongoDB (if not running already):
   ```bash
   # Using Docker
   docker run -d -p 27017:27017 --name mongodb mongo:5.0
   ```

2. Reset and seed the database with initial data:
   ```bash
   # Run the database seeding script
   python reset_and_seed_db.py
   ```
   This will populate the database with:
   - Form templates required by the frontend
   - Sample users with different roles
   - A sample lease exit record

3. Start Redis (if not started already):
   ```bash
   redis-server
   ```

4. Start Celery worker using the simplified script:
   ```bash
   python start_worker.py
   ```

5. Start Celery Flower (optional, for monitoring):
   ```bash
   celery -A celery_app flower --port=5555
   ```

6. Run the FastAPI application:
   ```bash
   uvicorn main:app --reload
   ```

   The API will be available at: http://localhost:8000  
   API Documentation: http://localhost:8000/docs  
   Celery Flower Dashboard: http://localhost:5555

### Running the Frontend

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

   The frontend will be available at: http://localhost:3000

### Quick Start Commands

For convenience, here are the commands to start all services in separate terminals:

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery worker
python start_worker.py

# Terminal 3: Start Celery Flower (optional)
celery -A celery_app flower --port=5555

# Terminal 4: Start FastAPI backend
uvicorn main:app --reload

# Terminal 5: Start React frontend
cd frontend && npm start
```

### Troubleshooting Celery on macOS

1. **Celery worker not starting**:
   - Check if Redis is running: `redis-cli ping` (should return PONG)
   - Verify your Redis URL in .env file
   - Try running with debug logging: `python start_worker.py --loglevel=debug`

2. **Permission issues**:
   - Ensure your user has appropriate permissions
   - Try running in a virtual environment

3. **Redis connection issues**:
   - Verify Redis is running: `brew services list | grep redis`
   - Check Redis logs: `tail -f /usr/local/var/log/redis.log`
   - Restart Redis: `brew services restart redis`

### Docker Setup (Alternative)

For a simplified setup using Docker:

1. Make sure Docker and Docker Compose are installed
2. Configure your `.env` file
3. Start all services:
   ```bash
   docker-compose up -d
   ```
4. Access the application at http://localhost:3000

## Database Initialization

The application requires certain data to be present in the database to function properly. The `reset_and_seed_db.py` script is provided to initialize the database with:

1. **Form Templates**: Required by the frontend to render dynamic forms
2. **Sample Users**: Users with different stakeholder roles (Lease Exit Management, Advisory, IFM)
3. **Sample Lease Exit**: A test lease exit record to demonstrate the application functionality

To run the database seeding script:
```bash
python reset_and_seed_db.py
```

This script is idempotent - it will only create the necessary data if it doesn't already exist, making it safe to run multiple times.

## Using the Application

1. **Create a New Lease Exit**:
   - Navigate to http://localhost:3000
   - Click "New Lease Exit" button
   - Fill out the lease exit form with required details
   - Submit the form

2. **View Lease Exits**:
   - The dashboard displays all lease exits with their status
   - Click "View" to see details of a specific lease exit

3. **Process Approvals**:
   - Navigate to the Approvals page
   - Review pending approvals
   - Submit approval decisions

4. **View Notifications**:
   - Navigate to the Notifications page
   - View and manage notifications

5. **Monitor Background Tasks**:
   - Navigate to http://localhost:5555 for Celery Flower
   - Monitor task execution and worker status
   - View real-time metrics on task processing

## Development

### Adding New Agents

1. Create a new agent class in the `agents/` directory
2. Register the agent in `config/agents.yaml`
3. Add the agent to the appropriate workflow in `config/workflows.yaml`

### Creating New Tasks

1. Define task class in the `tasks/` directory
2. Register task in `config/tasks.yaml`
3. Implement task execution logic

## Testing

Run tests using pytest:
```bash
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 