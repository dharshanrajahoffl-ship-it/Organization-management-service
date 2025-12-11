# app/db.py
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MASTER_DB = os.getenv("MASTER_DB", "org_master_db")

client = AsyncIOMotorClient(MONGO_URI)
master_db = client[MASTER_DB]

# collections in master_db:
# - organizations
# - admins (optional; we keep admin inside organization doc for simplicity)
orgs_col = master_db.get_collection("organizations")
