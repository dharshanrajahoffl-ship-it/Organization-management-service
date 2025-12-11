# app/schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Any

class OrgCreateIn(BaseModel):
    organization_name: str = Field(..., min_length=3)
    email: EmailStr
    password: str = Field(..., min_length=6)

class OrgGetIn(BaseModel):
    organization_name: str

class OrgUpdateIn(BaseModel):
    organization_name: str  # current name
    new_organization_name: str
    email: Optional[EmailStr]
    password: Optional[str]

class OrgDeleteIn(BaseModel):
    organization_name: str

class AdminLoginIn(BaseModel):
    email: EmailStr
    password: str

class OrgOut(BaseModel):
    organization_name: str
    collection_name: str
    admin_email: EmailStr
    id: Optional[str] = None
    extra: Optional[Any] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
