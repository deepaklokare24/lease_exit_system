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
- Redis

### Backend Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/lease-exit-system.git
   cd lease-exit-system
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Run the application:
   ```
   uvicorn main:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm start
   ```

## Usage

1. Access the application at `http://localhost:3000`
2. Log in with your credentials
3. Create a new lease exit request
4. Follow the guided workflow to complete the process

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
```
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 