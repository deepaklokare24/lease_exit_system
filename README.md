# Lease Exit System

A sophisticated workflow management system for handling lease exit processes, built with Crew AI, FastAPI, and React.

## Features

- Dynamic workflow orchestration using Crew AI agents
- Customizable form creation and management
- Document upload and management
- Real-time notifications via email and in-app alerts
- Role-based access control
- Approval chain management
- Comprehensive API documentation
- Modern React-based frontend

## System Requirements

- Python 3.9+
- Node.js 16+
- MongoDB 5.0+
- Redis 6.0+

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/lease-exit-system.git
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

5. Install frontend dependencies:
```bash
cd frontend
npm install
```

## Configuration

1. Configure MongoDB:
- Install MongoDB if not already installed
- Create a new database named `lease_exit_system`
- Update the `MONGODB_URI` in your `.env` file

2. Configure Email:
- Set up an email account for notifications
- Update the SMTP settings in your `.env` file

3. Configure OpenAI:
- Get an API key from OpenAI
- Add it to your `.env` file

## Running the Application

1. Start the backend server:
```bash
# From the root directory
python -m uvicorn api.server:app --reload
```

2. Start the frontend development server:
```bash
# From the frontend directory
npm start
```

3. Start the Redis server:
```bash
redis-server
```

4. Start the Celery worker (for background tasks):
```bash
celery -A tasks worker --loglevel=info
```

The application will be available at:
- Backend API: http://localhost:8000
- Frontend: http://localhost:3000
- API Documentation: http://localhost:8000/docs

## Project Structure

```
lease_exit_system/
├── api/                    # FastAPI application
│   ├── routes/            # API endpoints
│   └── server.py          # Main server file
├── database/              # Database models and connections
├── frontend/              # React frontend application
├── utils/                 # Utility functions and tools
├── workflows/             # Crew AI workflow definitions
├── tasks/                 # Background tasks
├── tests/                 # Test files
├── config/               # Configuration files
└── uploads/              # File upload directory
```

## API Documentation

The API documentation is automatically generated and can be accessed at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

Run the test suite:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=.
```

## Workflow Steps

1. **Initiation**
   - Lease Exit Management Team submits initial form
   - System notifies Advisory, IFM, and Legal

2. **Advisory Review**
   - Advisory completes Lease Requirements & Cost Information form
   - System notifies Legal, IFM, and Accounting

3. **IFM Review**
   - IFM completes Exit Requirements Scope form
   - System notifies MAC

4. **MAC Review**
   - MAC completes Exit Requirements Scope form
   - System notifies PJM

5. **PJM Review**
   - PJM completes Exit Requirements Scope form
   - System notifies Lease Exit Management Team

6. **Final Review**
   - Lease Exit Management Team reviews all details
   - Marks lease exit as Ready for Approval

7. **Approval Process**
   - Stakeholders provide Approve/Reject decisions
   - System updates status based on decisions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please contact the development team or create an issue in the repository. 