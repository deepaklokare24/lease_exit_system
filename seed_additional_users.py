import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from bson import ObjectId
from dotenv import load_dotenv
from database.models import StakeholderRole
from config.config import config

# Load environment variables
load_dotenv()

async def seed_additional_users():
    print("Starting additional users seeding...")
    
    # Connect to MongoDB
    mongo_uri = config.get_mongodb_uri()
    client = AsyncIOMotorClient(mongo_uri)
    db = client.lease_exit_system
    
    # Define new users with the missing roles
    new_users = [
        {
            "email": "property_manager@yopmail.com",
            "full_name": "Property Manager User",
            "role": "property_manager",
            "hashed_password": "hashed_password_here",  # In production, use proper password hashing
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "email": "tenant_role@yopmail.com",
            "full_name": "Tenant User",
            "role": "tenant",
            "hashed_password": "hashed_password_here",
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "email": "landlord_role@yopmail.com",
            "full_name": "Landlord User",
            "role": "landlord",
            "hashed_password": "hashed_password_here",
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "email": "maintenance_role@yopmail.com",
            "full_name": "Maintenance User",
            "role": "maintenance",
            "hashed_password": "hashed_password_here",
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        },
        # Add users with exact case matching roles used in notifications
        {
            "email": "advisorycrew@yopmail.com",
            "full_name": "Advisory User",
            "role": "Advisory",
            "hashed_password": "hashed_password_here",
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "email": "ifmcrew@yopmail.com",
            "full_name": "IFM User",
            "role": "IFM",
            "hashed_password": "hashed_password_here",
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "email": "legal_crew@yopmail.com",
            "full_name": "Legal User",
            "role": "Legal",
            "hashed_password": "hashed_password_here",
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        }
    ]
    
    # Check if users with these roles already exist
    for user in new_users:
        existing_user = await db.users.find_one({"role": user["role"]})
        if existing_user:
            print(f"User with role {user['role']} already exists, skipping")
        else:
            result = await db.users.insert_one(user)
            print(f"Inserted user with role {user['role']}, ID: {result.inserted_id}")
    
    print("Additional users seeding completed successfully!")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_additional_users()) 