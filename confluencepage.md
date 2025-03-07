# Lease Exit System - Technical Documentation

## Table of Contents

1. [Introduction](#introduction)
2. [System Architecture](#system-architecture)
   - [Backend](#backend)
   - [Frontend](#frontend)
   - [Database](#database)
   - [AI-Powered Components](#ai-powered-components)
3. [Code Structure](#code-structure)
4. [Control Flow](#control-flow)
   - [Lease Exit Workflow](#lease-exit-workflow)
   - [Agent Interactions](#agent-interactions)
   - [Data Flow](#data-flow)
5. [Installation & Setup](#installation--setup)
   - [Prerequisites](#prerequisites)
   - [Environment Setup](#environment-setup)
   - [Installing Redis on macOS](#installing-redis-on-macos)
   - [Running Locally](#running-locally)
   - [Quick Start Commands](#quick-start-commands)
   - [Running with Docker](#running-with-docker)
6. [API Documentation](#api-documentation)
7. [AI Agent System](#ai-agent-system)
   - [Workflow Designer Agent](#workflow-designer-agent)
   - [Form Creator Agent](#form-creator-agent)
   - [Approval Architect Agent](#approval-architect-agent)
   - [Notification Specialist Agent](#notification-specialist-agent)
8. [Task Management](#task-management)
9. [Troubleshooting](#troubleshooting)
10. [Extending the System](#extending-the-system)

## Introduction

The Lease Exit System is a comprehensive workflow automation application built to streamline and manage the complex process of exiting leases. It leverages AI-powered agents through the Crew AI framework to handle different aspects of the lease exit process, from designing workflows to creating forms, managing approvals, and sending notifications.

The system provides a structured approach to the lease exit process, ensuring all stakeholders are informed and all required steps are completed in the correct sequence. By automating many of the routine tasks and providing intelligent guidance, the system significantly improves efficiency and reduces errors in the lease exit process.

**Key Features:**

- **AI-Powered Workflow Management**: Automated process orchestration using specialized AI agents
- **Dynamic Form Generation**: Context-aware form creation and validation based on lease properties
- **Approval Management**: Structured approval processes with role-based permissions
- **Automated Notifications**: Timely notifications to all stakeholders
- **Audit Trail**: Complete history of all activities and decisions
- **Integration Capabilities**: Connects with external systems via APIs

## System Architecture

The Lease Exit System follows a modern, microservice-oriented architecture, with clear separation of concerns between different components. The system is containerized using Docker for easy deployment and scalability.

![Architecture Diagram](https://example.com/architecture-diagram.png)

### Backend

The backend is built with FastAPI, a modern Python web framework that provides high performance and automatic API documentation. Key components include:

- **FastAPI Application**: Serves as the API layer for the frontend and other clients
- **Crew AI Framework**: Orchestrates the AI agents and workflow execution
- **Celery**: Handles background tasks and asynchronous processing
- **Redis**: Acts as a message broker for Celery and provides caching capabilities

The backend is structured around several core modules:

- **API Routes**: Handle HTTP requests and responses
- **Agents**: AI-powered components that handle specialized tasks
- **Tasks**: Predefined workflow steps and operations
- **Database Models**: Data structures that represent the business entities
- **Utils**: Common utilities for validation, notification, and other shared functionality

### Frontend

The frontend is built with React and Material UI, providing a responsive and intuitive user interface. Key features include:

- **Dynamic Forms**: Renders forms based on JSON definitions from the backend
- **Workflow Visualization**: Displays the current state and progress of lease exit workflows
- **User Dashboard**: Shows tasks, notifications, and lease exit status
- **Document Management**: Upload, view, and manage documents associated with lease exits

### Database

MongoDB is used as the primary database, with the following collections:

- **lease_exits**: Stores lease exit records and their current status
- **users**: User accounts and roles
- **forms**: Form templates and submissions
- **notifications**: Notification records and delivery status
- **documents**: Metadata about uploaded documents

### Database Initialization

The system requires specific data to be present in the database for proper functionality. The `seed_db.py` script is provided to initialize the MongoDB collections with essential data:

#### Form Templates
The script creates form templates in the `form_templates` collection, which are used by the frontend to dynamically render forms. These include:

1. **Initial Form**: Used when creating a new lease exit, with fields for lease ID, property address, exit date, and reason for exit.
2. **Advisory Form**: Used by the Advisory department, with fields for lease requirements, cost information, and document uploads.
3. **IFM Form**: Used by the IFM department, with fields for exit requirements, scope details, and timeline.

#### Sample Users
The script creates sample users in the `users` collection with different stakeholder roles:

1. **Lease Exit Management**: Admin user responsible for overseeing the lease exit process.
2. **Advisory**: User responsible for providing advisory input on lease exits.
3. **IFM**: User responsible for facility management aspects of lease exits.

#### Sample Lease Exit
The script creates a sample lease exit record in the `lease_exits` collection to demonstrate the application functionality. This includes:

1. **Basic Information**: Lease ID, property details, and status.
2. **Approval Chain**: Pending approval steps for different stakeholders.
3. **Metadata**: Creation timestamps and other metadata.

The seeding script is designed to be idempotent, meaning it can be run multiple times without creating duplicate data. It checks if collections already contain data before inserting new records.

### AI-Powered Components

The system uses specialized AI agents to handle different aspects of the lease exit process:

1. **Workflow Designer Agent**: Creates and optimizes workflow definitions based on lease properties
2. **Form Creator Agent**: Generates dynamic forms with appropriate fields and validation rules
3. **Approval Architect Agent**: Designs approval chains and processes approval decisions
4. **Notification Specialist Agent**: Generates notifications and ensures delivery to stakeholders

## Code Structure

```
lease_exit_system/
├── agents/                   # AI agent implementations
│   ├── workflow_designer.py  # Workflow designer agent
│   ├── form_creator.py       # Form creator agent
│   ├── approval_architect.py # Approval architect agent
│   └── notification_specialist.py # Notification specialist agent
├── api/                      # API endpoints
│   ├── routes/               # API route definitions
│   │   ├── workflow.py       # Workflow-related endpoints
│   │   ├── forms.py          # Form-related endpoints
│   │   ├── approval.py       # Approval-related endpoints
│   │   └── notifications.py  # Notification-related endpoints
│   └── server.py             # API server configuration
├── config/                   # Configuration files
│   ├── agents.yaml           # Agent configuration
│   ├── workflows.yaml        # Workflow definitions
│   ├── tasks.yaml            # Task definitions
│   └── config.py             # Configuration loader
├── database/                 # Database access
│   ├── models.py             # Data models
│   └── connection.py         # Database connection management
├── frontend/                 # React frontend
│   ├── public/               # Static files
│   ├── src/                  # React source code
│   │   ├── components/       # React components
│   │   │   └── DynamicForm.jsx # Dynamic form renderer
│   │   ├── pages/            # Page components
│   │   ├── services/         # API services
│   │   └── App.js            # Main application component
│   └── package.json          # Frontend dependencies
├── tasks/                    # Task implementations
│   ├── workflow_tasks.py     # Workflow-related tasks
│   ├── form_tasks.py         # Form-related tasks
│   ├── approval_tasks.py     # Approval-related tasks
│   └── notification_tasks.py # Notification-related tasks
├── utils/                    # Utility functions
│   ├── logger.py             # Logging utilities
│   ├── form_validator.py     # Form validation utilities
│   ├── email_sender.py       # Email sending utilities
│   └── validators.py         # General validation utilities
├── workflows/                # Workflow definitions
│   ├── base_workflow.py      # Base workflow class
│   └── lease_exit_flow.py    # Lease exit workflow implementation
├── .env.example              # Example environment variables
├── Dockerfile                # Docker image definition
├── docker-compose.yml        # Docker Compose configuration
├── main.py                   # Application entry point
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

## Control Flow

### Lease Exit Workflow

The lease exit process follows a structured workflow:

1. **Initiation**: The Lease Exit Management Team submits the initial form with lease exit details.
2. **Notification**: The system automatically notifies Advisory, IFM, and Legal roles.
3. **Advisory Review**: Advisory completes the Lease Requirements & Cost Information form.
4. **Notification**: The system notifies Legal, IFM, and Accounting.
5. **IFM Review**: IFM completes the Exit Requirements Scope form.
6. **Notification**: The system notifies MAC.
7. **MAC Review**: MAC completes their review and form.
8. **Notification**: The system notifies PJM.
9. **PJM Review**: PJM completes their review and form.
10. **Notification**: The system notifies the Lease Exit Management Team.
11. **Final Review**: The Lease Exit Management Team reviews all information and marks it as Ready for Approval.
12. **Approval Process**: All stakeholders provide Approve/Reject decisions.
13. **Completion**: Based on approvals, the lease exit is marked as Ready for Exit or sent back for review.

### Agent Interactions

The system's AI agents work together to automate different aspects of the workflow:

1. **Workflow Designer Agent**:
   - Analyzes lease exit properties to design appropriate workflow steps
   - Customizes workflow based on lease type and property details
   - Identifies bottlenecks and suggests improvements

2. **Form Creator Agent**:
   - Generates context-aware forms with appropriate fields
   - Creates validation rules based on field types and requirements
   - Customizes forms for different stakeholder roles

3. **Approval Architect Agent**:
   - Designs approval chains based on workflow requirements
   - Processes approval decisions and updates workflow status
   - Triggers notifications based on approval status

4. **Notification Specialist Agent**:
   - Creates notifications for different workflow events
   - Ensures delivery to appropriate stakeholders
   - Resends failed notifications

### Data Flow

1. **Lease Exit Creation**:
   - Frontend submits lease exit data to the API
   - API creates lease exit record in the database
   - Workflow Designer Agent creates a workflow instance
   - Notification Specialist Agent notifies initial stakeholders

2. **Form Submission**:
   - Frontend submits form data to the API
   - Form Creator Agent validates the submission
   - API updates lease exit record with form data
   - Workflow advances to the next step
   - Notification Specialist Agent notifies next stakeholders

3. **Approval Process**:
   - Frontend submits approval decisions to the API
   - Approval Architect Agent processes decisions
   - API updates lease exit status based on approvals
   - Notification Specialist Agent notifies stakeholders of approval status

## Installation & Setup

### Prerequisites

To run the Lease Exit System, you need the following prerequisites:

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

3. Install Python dependencies:
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

Redis is required for the Celery task queue. Here's how to install and run it on macOS:

1. Install Redis using Homebrew:
   ```bash
   brew install redis
   ```

2. Start Redis as a service (runs in the background):
   ```bash
   brew services start redis
   ```

3. Alternatively, start Redis manually in a terminal:
   ```bash
   redis-server
   ```

4. To verify Redis is running:
   ```bash
   redis-cli ping
   ```
   You should receive a "PONG" response.

### Running Locally

#### Backend Setup

1. Reset and seed the database with initial data:
   ```bash
   python reset_and_seed_db.py
   ```
   This will populate the database with:
   - Form templates required by the frontend
   - Sample users with different roles
   - A sample lease exit record

2. Start Redis (if not already running):
   ```bash
   redis-server
   ```

3. Start Celery worker using the simplified script:
   ```bash
   python start_worker.py
   ```

4. Start Celery Flower (optional, for monitoring):
   ```bash
   celery -A celery_app flower --port=5555
   ```

5. Run the FastAPI application:
   ```bash
   uvicorn main:app --reload
   ```

   The API will be available at: http://localhost:8000  
   API Documentation: http://localhost:8000/docs  
   Celery Flower Dashboard: http://localhost:5555

#### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node.js dependencies:
   ```bash
   npm install
   ```

3. Start the React development server:
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

### Running with Docker

For a simplified setup using Docker:

1. Make sure Docker and Docker Compose are installed
2. Configure your `.env` file
3. Start all services:
   ```bash
   docker-compose up -d
   ```
4. Access the application at http://localhost:3000

## API Documentation

The system provides a comprehensive API for interacting with the backend services. The API is documented using OpenAPI (Swagger) and can be accessed at http://localhost:8000/docs when the server is running.

Key API endpoints include:

### Workflow Endpoints

- `POST /api/workflows/lease-exit`: Create a new lease exit workflow
- `GET /api/workflows/lease-exits`: List all lease exit workflows
- `GET /api/workflows/lease-exit/{lease_exit_id}`: Get details of a specific lease exit
- `POST /api/workflows/lease-exit/{lease_exit_id}/form`: Submit a form for a specific lease exit
- `POST /api/workflows/lease-exit/{lease_exit_id}/approve`: Submit an approval decision

### Form Endpoints

- `POST /api/forms/templates`: Create a new form template
- `GET /api/forms/templates`: List all form templates
- `GET /api/forms/templates/{template_id}`: Get a specific form template
- `POST /api/forms/{lease_exit_id}/documents`: Upload a document for a form
- `GET /api/forms/{lease_exit_id}/documents`: List all documents for a lease exit
- `GET /api/forms/{lease_exit_id}`: List all forms for a lease exit
- `GET /api/forms/{lease_exit_id}/{form_type}`: Get a specific form for a lease exit

### Notification Endpoints

- `POST /api/notifications`: Send notifications to multiple stakeholders
- `GET /api/notifications/{lease_exit_id}`: Get all notifications for a specific lease exit
- `GET /api/notifications/role/{role}`: Get all notifications for a specific role
- `POST /api/notifications/{notification_id}/resend`: Resend a specific notification

## AI Agent System

The Lease Exit System leverages specialized AI agents powered by the Crew AI framework to handle different aspects of the lease exit process.

### Workflow Designer Agent

**File**: `agents/workflow_designer.py`

The Workflow Designer Agent is responsible for creating and optimizing workflows for lease exits. It analyzes lease properties to determine the appropriate workflow steps and transitions.

**Key Methods**:
- `create_standard_workflow`: Creates a standard workflow based on lease type and property details
- `customize_workflow`: Customizes an existing workflow based on specific requirements
- `analyze_workflow_performance`: Analyzes workflow performance and identifies bottlenecks
- `generate_workflow_for_lease_exit`: Generates a customized workflow for a specific lease exit

**Example**:
```python
workflow_agent = WorkflowDesignerAgent()
workflow = await workflow_agent.create_standard_workflow(
    lease_type="commercial",
    property_details={"property_type": "office", "value": 2000000}
)
```

### Form Creator Agent

**File**: `agents/form_creator.py`

The Form Creator Agent generates dynamic forms based on lease context and stakeholder roles. It determines the appropriate fields, validation rules, and form structure.

**Key Methods**:
- `create_lease_exit_form`: Creates a dynamic form for lease exit initiation
- `customize_form_for_stakeholder`: Customizes a form for a specific stakeholder role
- `validate_form_submission`: Validates form submission data against rules
- `analyze_lease_exit_for_form_requirements`: Determines what forms are required for a lease exit

**Example**:
```python
form_agent = FormCreatorAgent()
form = await form_agent.create_lease_exit_form(
    lease_type="commercial",
    property_details={"property_type": "office"}
)
```

### Approval Architect Agent

**File**: `agents/approval_architect.py`

The Approval Architect Agent manages the approval process for lease exits. It creates approval chains, processes approval decisions, and updates workflow status.

**Key Methods**:
- `create_approval_chain`: Creates an approval chain for a lease exit
- `process_approval`: Processes an approval decision
- `notify_approvers`: Notifies approvers about pending approvals
- `notify_rejection`: Sends notifications about rejections
- `notify_approval_complete`: Notifies stakeholders when all approvals are complete

**Example**:
```python
approval_agent = ApprovalArchitectAgent()
approval_chain = await approval_agent.create_approval_chain(
    lease_exit_id="123456",
    required_approvers=[
        StakeholderRole.ADVISORY,
        StakeholderRole.LEGAL,
        StakeholderRole.LEASE_EXIT_MANAGEMENT
    ]
)
```

### Notification Specialist Agent

**File**: `agents/notification_specialist.py`

The Notification Specialist Agent handles all communications with stakeholders. It creates and sends notifications, tracks delivery status, and resends failed notifications.

**Key Methods**:
- `create_notification`: Creates and sends a notification
- `notify_workflow_update`: Sends notifications about workflow updates
- `resend_failed_notifications`: Resends notifications that failed to deliver

**Example**:
```python
notification_agent = NotificationSpecialistAgent()
await notification_agent.create_notification(
    lease_exit_id="123456",
    recipient_role=StakeholderRole.ADVISORY,
    subject="New Lease Exit Submission",
    message="A new lease exit has been submitted for your review."
)
```

## Task Management

The system uses a task-based architecture to manage discrete operations. Tasks are defined in the `tasks/` directory and are executed by the appropriate agent or service.

### Workflow Tasks

**File**: `tasks/workflow_tasks.py`

Handles tasks related to workflow management, such as creating workflows, updating workflow status, and initiating lease exits.

### Form Tasks

**File**: `tasks/form_tasks.py`

Manages form-related tasks, including creating form templates, validating form submissions, and uploading documents.

### Approval Tasks

**File**: `tasks/approval_tasks.py`

Handles approval-related tasks, such as creating approval chains, processing approval decisions, and sending notifications.

### Notification Tasks

**File**: `tasks/notification_tasks.py`

Manages notification-related tasks, including creating notifications, sending emails, and resending failed notifications.

## Troubleshooting

### Database Connection Issues

If you encounter database connection issues:

1. Check that MongoDB is running:
   ```bash
   docker ps | grep mongo
   ```

2. Verify the MongoDB URI in your `.env` file:
   ```
   MONGODB_URI=mongodb+srv://construction_admin:24April@1988@construction-projects.8ekec.mongodb.net/?retryWrites=true&w=majority&appName=construction-projects
   ```

3. If using Docker Compose, check the `mongo` service:
   ```bash
   docker-compose logs mongo
   ```

### API Errors

If you encounter API errors:

1. Check the API logs:
   ```bash
   docker-compose logs api
   ```

2. Verify that the required environment variables are set:
   ```bash
   docker-compose exec api env
   ```

3. Check the API documentation for the correct request format:
   http://localhost:8000/docs

### AI Agent Issues

If the AI agents are not functioning correctly:

1. Verify your OpenAI API key:
   ```
   OPENAI_API_KEY=your-openai-api-key
   ```

2. Check the agent configuration in `config/agents.yaml`

3. Check the agent logs:
   ```bash
   docker-compose logs api | grep "agent"
   ```

## Extending the System

The Lease Exit System is designed to be easily extensible. Here are some ways to extend the system:

### Adding a New Agent

1. Create a new agent class in the `agents/` directory:
   ```python
   from crew.agent import Agent

   class MyNewAgent(Agent):
       def __init__(self, config: Dict[str, Any] = None):
           super().__init__(config)
           self.name = "My New Agent"
           self.description = "Description of my new agent"
           
       async def my_new_method(self, param1, param2):
           # Implementation
           return result
   ```

2. Register the agent in `config/agents.yaml`:
   ```yaml
   my_new_agent:
     name: "My New Agent"
     description: "Description of my new agent"
     class: "agents.my_new_agent.MyNewAgent"
     model: ${ai_models.default}
     tools:
       - "tools.my_tool.MyTool"
   ```

### Adding a New Task

1. Create a new task class in the `tasks/` directory:
   ```python
   class MyNewTasks:
       def __init__(self):
           self.my_agent = MyNewAgent()
       
       async def my_new_task(self, param1, param2):
           # Implementation
           return result
   ```

2. Register the task in `config/tasks.yaml`:
   ```yaml
   my_new_tasks:
     - id: "my_new_task"
       name: "My New Task"
       description: "Description of my new task"
       agent: "my_new_agent"
       expected_output:
         type: "result_type"
         schema:
           field1: "string"
           field2: "number"
   ```

### Adding a New API Endpoint

1. Create a new route in the appropriate file in `api/routes/`:
   ```python
   @router.post("/my-new-endpoint")
   async def my_new_endpoint(request: MyNewRequestModel):
       # Implementation
       return {"status": "success", "data": result}
   ```

2. Register the route in `main.py`:
   ```python
   from api.routes import my_new_route
   app.include_router(my_new_route.router, prefix="/api/my-new", tags=["My New"])
   ```
