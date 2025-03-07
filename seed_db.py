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

async def seed_database():
    print("Starting database seeding...")
    
    # Connect to MongoDB
    mongo_uri = config.get_mongodb_uri()
    client = AsyncIOMotorClient(mongo_uri)
    db = client.lease_exit_system
    
    # Clear existing data (optional, comment out if you want to keep existing data)
    await db.form_templates.delete_many({})
    print("Cleared existing form templates")
    
    # Seed form templates
    form_templates = [
        {
            "form_type": "initial_form",
            "fields": [
                {
                    "name": "lease_id",
                    "label": "Lease ID",
                    "type": "text",
                    "required": True
                },
                {
                    "name": "property_address",
                    "label": "Property Address",
                    "type": "text",
                    "required": True
                },
                {
                    "name": "exit_date",
                    "label": "Exit Date",
                    "type": "date",
                    "required": True
                },
                {
                    "name": "reason_for_exit",
                    "label": "Reason for Exit",
                    "type": "textarea",
                    "required": True
                },
                {
                    "name": "additional_details",
                    "label": "Additional Details",
                    "type": "textarea",
                    "required": False
                }
            ],
            "required_role": StakeholderRole.LEASE_EXIT_MANAGEMENT,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        {
            "form_type": "advisory_form",
            "fields": [
                {
                    "name": "lease_requirements",
                    "label": "Lease Requirements",
                    "type": "textarea",
                    "required": True
                },
                {
                    "name": "cost_information",
                    "label": "Cost Information",
                    "type": "textarea",
                    "required": True
                },
                {
                    "name": "documents",
                    "label": "Required Documents",
                    "type": "file",
                    "required": True,
                    "multiple": True
                }
            ],
            "required_role": StakeholderRole.ADVISORY,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        {
            "form_type": "ifm_form",
            "fields": [
                {
                    "name": "exit_requirements",
                    "label": "Exit Requirements",
                    "type": "textarea",
                    "required": True
                },
                {
                    "name": "scope_details",
                    "label": "Scope Details",
                    "type": "textarea",
                    "required": True
                },
                {
                    "name": "timeline",
                    "label": "Timeline",
                    "type": "date",
                    "required": True
                }
            ],
            "required_role": StakeholderRole.IFM,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    ]
    
    # Insert form templates
    result = await db.form_templates.insert_many(form_templates)
    print(f"Inserted {len(result.inserted_ids)} form templates")
    
    # Seed users (if needed)
    users = [
        {
            "email": "admincrew@example.com",
            "full_name": "Admin User",
            "role": StakeholderRole.LEASE_EXIT_MANAGEMENT,
            "hashed_password": "hashed_password_here",  # In production, use proper password hashing
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "email": "advisorycrew@example.com",
            "full_name": "Advisory User",
            "role": StakeholderRole.ADVISORY,
            "hashed_password": "hashed_password_here",
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "email": "ifmcrew@example.com",
            "full_name": "IFM User",
            "role": StakeholderRole.IFM,
            "hashed_password": "hashed_password_here",
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        }
    ]
    
    # Check if users collection is empty before inserting
    if await db.users.count_documents({}) == 0:
        result = await db.users.insert_many(users)
        print(f"Inserted {len(result.inserted_ids)} users")
    else:
        print("Users already exist, skipping user creation")
    
    # Create a sample lease exit (optional)
    sample_lease_exit = {
        "lease_id": "LEASE123",
        "property_details": {
            "property_address": "123 Main St, Anytown, USA",
            "property_type": "Office",
            "square_footage": 5000
        },
        "status": WorkflowStatus.DRAFT,
        "current_step": "initial_form",
        "forms": {},
        "approval_chain": [
            {
                "role": StakeholderRole.ADVISORY,
                "status": "pending",
                "approved_by": None,
                "approved_at": None,
                "comments": None
            },
            {
                "role": StakeholderRole.IFM,
                "status": "pending",
                "approved_by": None,
                "approved_at": None,
                "comments": None
            }
        ],
        "documents": [],
        "created_by": "admin@example.com",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "metadata": {}
    }
    
    # Check if lease_exits collection is empty before inserting
    if await db.lease_exits.count_documents({}) == 0:
        result = await db.lease_exits.insert_one(sample_lease_exit)
        print(f"Inserted sample lease exit with ID: {result.inserted_id}")
    else:
        print("Lease exits already exist, skipping sample creation")
    
    print("Database seeding completed successfully!")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_database()) 