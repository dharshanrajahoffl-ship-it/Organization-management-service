# app/auth.py
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.utils import decode_token
from typing import Dict, Any
from jose import JWTError

bearer_scheme = HTTPBearer()

async def get_current_admin(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)) -> Dict[str, Any]:
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    # token contains admin_email and org_id
    admin_email = payload.get("admin_email")
    org_id = payload.get("org_id")
    if not admin_email or not org_id:
        raise HTTPException(status_code=401, detail="Invalid token data")
    return {"admin_email": admin_email, "org_id": org_id, "organization_name": payload.get("organization_name")}
