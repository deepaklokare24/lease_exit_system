import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from bson import ObjectId
from dotenv import load_dotenv
from database.models import StakeholderRole, WorkflowStatus, FormStatus
from config.config import config

# Load environment variables
load_dotenv()

async def reset_and_seed_database():
    print("Starting database reset and seeding...")
    
    # Connect to MongoDB
    mongo_uri = config.get_mongodb_uri()
    client = AsyncIOMotorClient(mongo_uri)
    db = client.lease_exit_system
    
    # Clear existing data
    await db.users.delete_many({})
    await db.lease_exits.delete_many({})
    await db.notifications.delete_many({})
    await db.form_templates.delete_many({})
    
    print("Cleared existing data from database")
    
    # Seed form templates
    current_time = datetime.utcnow().isoformat()
    form_templates = [
        {
            "form_type": "lease_exit_initiation",
            "name": "Lease Exit Initiation",
            "description": "Form to initiate a new lease exit process",
            "required_role": StakeholderRole.LEASE_EXIT_MANAGEMENT,
            "created_at": current_time,
            "updated_at": current_time,
            "fields": [
                {
                    "id": "lease_id",
                    "label": "Lease ID",
                    "type": "text",
                    "required": True,
                    "description": "Unique identifier for the lease"
                },
                {
                    "id": "property_address",
                    "label": "Property Address",
                    "type": "text",
                    "required": True,
                    "description": "Address of the property"
                },
                {
                    "id": "exit_date",
                    "label": "Expected Exit Date",
                    "type": "date",
                    "required": True,
                    "description": "The date when the lease exit should be completed"
                },
                {
                    "id": "reason_for_exit",
                    "label": "Exit Reason",
                    "type": "select",
                    "options": ["End of Term", "Early Termination", "Breach of Contract", "Other"],
                    "required": True
                },
                {
                    "id": "additional_notes",
                    "label": "Additional Notes",
                    "type": "textarea",
                    "required": False,
                    "description": "Any additional information about the lease exit"
                }
            ]
        },
        {
            "form_type": "advisory_form",
            "name": "Advisory Review Form",
            "description": "Form for Advisory team to review lease exit",
            "required_role": StakeholderRole.ADVISORY,
            "created_at": current_time,
            "updated_at": current_time,
            "fields": [
                {
                    "id": "lease_requirements",
                    "label": "Lease Requirements",
                    "type": "textarea",
                    "required": True,
                    "description": "Requirements specified in the lease agreement"
                },
                {
                    "id": "cost_information",
                    "label": "Cost Information",
                    "type": "textarea",
                    "required": True,
                    "description": "Financial implications of the lease exit"
                },
                {
                    "id": "documents",
                    "label": "Required Documents",
                    "type": "file",
                    "required": True,
                    "multiple": True,
                    "description": "Supporting documents for the lease exit"
                }
            ]
        },
        {
            "form_type": "ifm_form",
            "name": "IFM Review Form",
            "description": "Form for IFM team to review lease exit",
            "required_role": StakeholderRole.IFM,
            "created_at": current_time,
            "updated_at": current_time,
            "fields": [
                {
                    "id": "exit_requirements",
                    "label": "Exit Requirements",
                    "type": "textarea",
                    "required": True,
                    "description": "Requirements for completing the exit"
                },
                {
                    "id": "scope_details",
                    "label": "Scope Details",
                    "type": "textarea",
                    "required": True,
                    "description": "Scope of work for the exit"
                },
                {
                    "id": "timeline",
                    "label": "Timeline",
                    "type": "date",
                    "required": True,
                    "description": "Expected timeline for completion"
                }
            ]
        }
    ]
    
    # Insert form templates
    result = await db.form_templates.insert_many(form_templates)
    print(f"Inserted {len(result.inserted_ids)} form templates")
    
    # Create users for each role in StakeholderRole enum
    users = []
    
    # Get all roles from the StakeholderRole enum
    for role in StakeholderRole:
        # Convert enum value to string and create email
        role_value = role.value
        email = f"{role_value.lower()}@yopmail.com"
        
        # Create user
        user = {
            "email": email,
            "full_name": f"{role_value.capitalize()} User",
            "role": role_value,
            "hashed_password": "hashed_password_here",  # In production, use proper password hashing
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
        
        users.append(user)
    
    # Insert users
    result = await db.users.insert_many(users)
    print(f"Inserted {len(result.inserted_ids)} users")
    
    # Create a sample lease exit
    sample_lease_exit = {
        "lease_exit_id": "LE-SAMPLE123",
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "property_details": {
            "property_address": "123 Main St, Anytown, USA",
            "lease_id": "LEASE123"
        },
        "exit_details": {
            "exit_date": "2025-06-30T00:00:00.000Z",
            "reason_for_exit": "End of Term",
            "additional_notes": "Sample lease exit for testing"
        },
        "workflow_state": {
            "current_step": "initial_submission",
            "approvals": {},
            "history": [
                {
                    "step": "initial_submission",
                    "timestamp": datetime.now().isoformat(),
                    "action": "created"
                }
            ]
        }
    }
    
    # Insert sample lease exit
    result = await db.lease_exits.insert_one(sample_lease_exit)
    print(f"Inserted sample lease exit with ID: {result.inserted_id}")
    
    print("Database reset and seeding completed successfully!")
    client.close()

if __name__ == "__main__":
    asyncio.run(reset_and_seed_database()) 