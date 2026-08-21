from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.db import execute, execute_returning, fetch_all, fetch_one
from app.schemas.models import CredentialCreate, CredentialOut
from app.services.crypto import encrypt_payload

router = APIRouter(prefix="/api/credentials", tags=["credentials"])


@router.get("", response_model=list[CredentialOut])
async def list_credentials() -> list[CredentialOut]:
    rows = await fetch_all(
        "SELECT id, name, cred_type, meta, created_at FROM credentials ORDER BY id DESC"
    )
    return [CredentialOut(**r) for r in rows]


@router.post("", response_model=CredentialOut, status_code=201)
async def create_credential(body: CredentialCreate) -> CredentialOut:
    if body.cred_type == "password":
        if not body.username or not body.password:
            raise HTTPException(400, "username and password required for password type")
        payload = {"username": body.username, "password": body.password}
    else:
        if not body.access_token:
            raise HTTPException(400, "access_token required for jwt type")
        payload = {
            "access_token": body.access_token,
            "refresh_token": body.refresh_token or "",
        }

    try:
        ciphertext = encrypt_payload(payload)
    except RuntimeError as exc:
        raise HTTPException(500, str(exc)) from exc

    try:
        row = await execute_returning(
            """
            INSERT INTO credentials (name, cred_type, payload_encrypted, meta)
            VALUES (%s, %s, %s, %s)
            RETURNING id, name, cred_type, meta, created_at
            """,
            (body.name, body.cred_type, ciphertext, body.meta),
        )
    except Exception as exc:
        if "unique" in str(exc).lower() or "duplicate" in str(exc).lower():
            raise HTTPException(409, f"credential name already exists: {body.name}") from exc
        raise
    return CredentialOut(**row)


@router.delete("/{credential_id}", status_code=204)
async def delete_credential(credential_id: int) -> None:
    existing = await fetch_one("SELECT id FROM credentials WHERE id = %s", (credential_id,))
    if existing is None:
        raise HTTPException(404, "credential not found")
    await execute("DELETE FROM credentials WHERE id = %s", (credential_id,))
