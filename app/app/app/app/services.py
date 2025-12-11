# app/services.py
from app.db import orgs_col, master_db, client
from app.utils import hash_password, verify_password, create_access_token
from typing import Optional, Dict, Any
import re
from bson import ObjectId
import asyncio

def _normalize_name(name: str) -> str:
    # remove spaces, lowercase, keep alphanum and underscore
    name = name.strip().lower()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^a-z0-9_]", "", name)
    return name

def _org_collection_name(normalized_name: str) -> str:
    return f"org_{normalized_name}"

async def organization_exists(org_name: str) -> bool:
    doc = await orgs_col.find_one({"organization_name": org_name})
    return doc is not None

async def create_organization(organization_name: str, email: str, password: str) -> Dict[str, Any]:
    normalized = _normalize_name(organization_name)
    coll_name = _org_collection_name(normalized)
    # check exists
    existing = await orgs_col.find_one({"organization_name": organization_name})
    if existing:
        raise ValueError("organization already exists")
    # create collection (Motor creates on first insert). Optionally ensure indexes.
    db = client[master_db.name]  # same client
    # create a collection by inserting a marker doc then removing it, or create_collection
    try:
        await db.create_collection(coll_name)
    except Exception:
        # collection may already exist or server doesn't allow create_collection explicitly
        pass
    # init admin
    hashed = hash_password(password)
    admin = {"email": email, "password": hashed}
    org_doc = {
        "organization_name": organization_name,
        "normalized_name": normalized,
        "collection_name": coll_name,
        "admin": admin,
        "created_at":  __import__("datetime").datetime.utcnow(),
    }
    res = await orgs_col.insert_one(org_doc)
    org_doc["_id"] = res.inserted_id
    return {
        "id": str(res.inserted_id),
        "organization_name": organization_name,
        "collection_name": coll_name,
        "admin_email": email,
    }

async def get_organization(organization_name: str) -> Optional[Dict[str, Any]]:
    doc = await orgs_col.find_one({"organization_name": organization_name})
    if not doc:
        return None
    doc["id"] = str(doc["_id"])
    doc.pop("_id", None)
    return doc

async def admin_login(email: str, password: str) -> Dict[str, Any]:
    # find the organization containing this admin
    doc = await orgs_col.find_one({"admin.email": email})
    if not doc:
        raise ValueError("invalid credentials")
    hashed = doc["admin"]["password"]
    if not verify_password(password, hashed):
        raise ValueError("invalid credentials")
    # create token with admin id (we will use org doc id and admin email)
    token_data = {"admin_email": email, "org_id": str(doc["_id"]), "organization_name": doc["organization_name"]}
    token = create_access_token(token_data)
    return {"access_token": token, "token_type": "bearer"}

async def delete_organization(organization_name: str, requesting_admin_email: str) -> bool:
    # verify admin belongs to org
    doc = await orgs_col.find_one({"organization_name": organization_name})
    if not doc:
        raise ValueError("organization not found")
    if doc["admin"]["email"] != requesting_admin_email:
        raise PermissionError("only the org admin can delete the organization")
    coll_name = doc["collection_name"]
    # drop collection
    db = client[master_db.name]
    if coll_name in await db.list_collection_names():
        await db.drop_collection(coll_name)
    # remove master doc
    await orgs_col.delete_one({"_id": doc["_id"]})
    return True

async def update_organization(current_name: str, new_name: str, email: Optional[str] = None, password: Optional[str] = None) -> Dict[str, Any]:
    # ensure current exists
    doc = await orgs_col.find_one({"organization_name": current_name})
    if not doc:
        raise ValueError("organization not found")
    # validate new_name not used (other than current)
    if current_name != new_name:
        existing = await orgs_col.find_one({"organization_name": new_name})
        if existing:
            raise ValueError("target organization name already exists")

    old_coll = doc["collection_name"]
    normalized = _normalize_name(new_name)
    new_coll = _org_collection_name(normalized)
    db = client[master_db.name]

    # create new collection and copy documents from old to new
    # If old and new collection names are identical (no change), skip copy
    if old_coll != new_coll:
        # ensure new collection exists
        try:
            await db.create_collection(new_coll)
        except Exception:
            pass
        # copy documents if old exists
        if old_coll in await db.list_collection_names():
            old_c = db[old_coll]
            new_c = db[new_coll]
            cursor = old_c.find({})
            batch = []
            async for doc_item in cursor:
                # remove _id to let Mongo assign new one (or keep if you want)
                doc_item.pop("_id", None)
                batch.append(doc_item)
                if len(batch) >= 500:
                    await new_c.insert_many(batch)
                    batch = []
            if batch:
                await new_c.insert_many(batch)
        # optional: drop old collection
        # await db.drop_collection(old_coll)

    # update admin fields if provided
    updated_admin = doc["admin"]
    if email:
        updated_admin["email"] = email
    if password:
        updated_admin["password"] = hash_password(password)

    # update master doc
    await orgs_col.update_one(
        {"_id": doc["_id"]},
        {"$set": {"organization_name": new_name, "normalized_name": normalized, "collection_name": new_coll, "admin": updated_admin}}
    )
    updated = await orgs_col.find_one({"_id": doc["_id"]})
    updated["id"] = str(updated["_id"])
    updated.pop("_id", None)
    return updated
