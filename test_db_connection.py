import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import urllib.parse
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

async def test_connection():
    # Get MongoDB URI from environment
    uri = os.getenv("MONGODB_URI")
    
    if not uri:
        # Construct URI with proper escaping if not in environment
        username = urllib.parse.quote_plus("construction_admin")
        password = urllib.parse.quote_plus("24April@1988")
        uri = f"mongodb+srv://{username}:{password}@construction-projects.8ekec.mongodb.net/?retryWrites=true&w=majority&appName=construction-projects"
    
    print(f"Connecting to MongoDB with URI: {uri}")
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(uri)
        
        # Test connection by listing databases
        db_list = await client.list_database_names()
        print(f"Connected successfully! Available databases: {db_list}")
        
        # Close connection
        client.close()
        print("Connection closed")
        
    except Exception as e:
        print(f"Connection failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_connection()) 