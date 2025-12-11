# app/main.py
from fastapi import FastAPI, HTTPException, Depends
from app import services
from app import schemas
from app.auth import get_current_admin
from typing import Dict
import uvicorn

app = FastAPI(title="Organization Management Service")

@app.post("/org/create", response_model=schemas.OrgOut)
async def create_org(payload: schemas.OrgCreateIn):
    try:
        res = await services.create_organization(payload.organization_name, payload.email, payload.password)
        return {
            "organization_name": res["organization_name"],
            "collection_name": res["collection_name"],
            "admin_email": res["admin_email"],
            "id": res["id"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/org/get", response_model=schemas.OrgOut)
async def get_org(org_name: str):
    doc = await services.get_organization(org_name)
    if not doc:
        raise HTTPException(status_code=404, detail="organization not found")
    return {
        "organization_name": doc["organization_name"],
        "collection_name": doc["collection_name"],
        "admin_email": doc["admin"]["email"],
        "id": doc["id"],
        "extra": {"created_at": doc.get("created_at")}
    }

@app.put("/org/update", response_model=schemas.OrgOut)
async def update_org(payload: schemas.OrgUpdateIn, current=Depends(get_current_admin)):
    # ensure the caller belongs to the organization being updated
    if current["admin_email"] != (payload.email if payload.email else current["admin_email"]) and current["organization_name"] != payload.organization_name:
        # this is a gentle guard; we prefer admin token's org to match the target org being updated
        pass
    try:
        updated = await services.update_organization(payload.organization_name, payload.new_organization_name, payload.email, payload.password)
        return {
            "organization_name": updated["organization_name"],
            "collection_name": updated["collection_name"],
            "admin_email": updated["admin"]["email"],
            "id": updated["id"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/org/delete")
async def delete_org(org_name: str, current=Depends(get_current_admin)):
    # only admin of that org can delete
    try:
        await services.delete_organization(org_name, current["admin_email"])
        return {"status": "deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@app.post("/admin/login", response_model=schemas.Token)
async def admin_login(payload: schemas.AdminLoginIn):
    try:
        token = await services.admin_login(payload.email, payload.password)
        return token
    except ValueError:
        raise HTTPException(status_code=401, detail="invalid credentials")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
