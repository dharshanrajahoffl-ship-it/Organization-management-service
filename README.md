# Organization Management Service (FastAPI + MongoDB)

## Overview
Backend-only project to create and manage organizations in a multi-tenant style. Uses a Master DB to store metadata and programmatically creates per-organization collections.

## Tech Stack
- Python 3.10+
- FastAPI
- Motor (async MongoDB)
- JWT (python-jose)
- Passlib (bcrypt)

## Setup
1. Copy `.env.example` to `.env` and edit values (MONGO_URI, SECRET_KEY, etc).
2. Create virtualenv and install:

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

3. Run:


## Endpoints
- `POST /org/create` — create organization
- `GET /org/get?org_name=<name>` — get organization
- `PUT /org/update` (Bearer token required) — update organization (rename + admin update)
- `DELETE /org/delete?org_name=<name>` (Bearer token required) — delete organization
- `POST /admin/login` — login admin, returns JWT

## Notes
- Master DB stores organization metadata in `organizations` collection.
- Each organization gets a collection named `org_<normalized_name>`.
- Passwords are hashed with bcrypt.
- JWT contains `admin_email` and `org_id`.

