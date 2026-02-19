from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = "agile-tool"

client = None
database = None

async def connect_db():
    global client, database
    client = AsyncIOMotorClient(MONGODB_URI)
    database = client[DATABASE_NAME]
    
    # Create indexes
    await database.spaces.create_index([("created_at", DESCENDING)])
    await database.sprints.create_index([("space_id", ASCENDING)])
    await database.backlog_items.create_index([("space_id", ASCENDING)])
    await database.backlog_items.create_index([("sprint_id", ASCENDING)])
    
    print("Connected to MongoDB")

async def close_db():
    global client
    if client:
        client.close()
        print("Disconnected from MongoDB")

def get_database():
    return database
