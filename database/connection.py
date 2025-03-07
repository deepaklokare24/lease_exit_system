from motor.motor_asyncio import AsyncIOMotorClient
import os
from typing import Optional
from dotenv import load_dotenv
import logging
from contextlib import asynccontextmanager
from config.config import config
from functools import lru_cache

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class Database:
    """MongoDB database connection handler"""
    
    client: Optional[AsyncIOMotorClient] = None
    db_name: str = "lease_exit_system"
    
    @classmethod
    async def connect(cls):
        """Connect to the MongoDB database"""
        if not cls.client:
            mongo_uri = config.get_mongodb_uri()
            
            logger.info(f"Connecting to MongoDB")
            cls.client = AsyncIOMotorClient(mongo_uri)
            
            # Set up indexes (could be moved to a separate method if there are many)
            db = cls.client[cls.db_name]
            
            # Create indexes on commonly queried fields
            await db.lease_exits.create_index("lease_id")
            await db.users.create_index("email", unique=True)
            await db.users.create_index("role")
            await db.notifications.create_index("recipient_role")
            await db.notifications.create_index("lease_exit_id")
            await db.form_templates.create_index("form_type", unique=True)
            
            logger.info("Connected to MongoDB")
    
    @classmethod
    async def disconnect(cls):
        """Disconnect from the MongoDB database"""
        if cls.client:
            cls.client.close()
            cls.client = None
            logger.info("Disconnected from MongoDB")
    
    @classmethod
    def get_db(cls):
        """Get the database instance
        
        Returns:
            The database instance
        """
        if not cls.client:
            raise RuntimeError("Database not connected. Call connect() first.")
        
        return cls.client[cls.db_name]
    
    @classmethod
    @asynccontextmanager
    async def get_collection(cls, collection_name):
        """Get a collection from the database
        
        Args:
            collection_name: The name of the collection
            
        Yields:
            The collection
        """
        if cls.client is None:
            await cls.connect()
        
        db = cls.get_db()
        yield db[collection_name]

# Helper functions for common database operations

async def get_lease_exits_collection():
    """Get the lease_exits collection
    
    Returns:
        The lease_exits collection
    """
    async with Database.get_collection("lease_exits") as collection:
        return collection

async def get_users_collection():
    """Get the users collection
    
    Returns:
        The users collection
    """
    async with Database.get_collection("users") as collection:
        return collection

async def get_notifications_collection():
    """Get the notifications collection
    
    Returns:
        The notifications collection
    """
    async with Database.get_collection("notifications") as collection:
        return collection

async def get_form_templates_collection():
    """Get the form_templates collection
    
    Returns:
        The form_templates collection
    """
    async with Database.get_collection("form_templates") as collection:
        return collection

@lru_cache()
def get_database():
    """FastAPI dependency for getting database instance"""
    return Database.get_db()
