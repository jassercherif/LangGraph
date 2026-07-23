import psycopg
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.database import get_db_connection
from core.security import hash_password, verify_password, decode_access_token

bearer_scheme = HTTPBearer()


# ── User CRUD ─────────────────────────────────────────────────────────────────

def create_user(username: str, email: str, password: str) -> dict:
    hashed = hash_password(password)
    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (username, email, hashed_password)
                    VALUES (%s, %s, %s)
                    RETURNING id, username, email, created_at
                    """,
                    (username, email, hashed),
                )
                user = cur.fetchone()
            conn.commit()
            return user
        except psycopg.errors.UniqueViolation:
            conn.rollback()
            raise HTTPException(status_code=400, detail="Username or email already exists.")


def authenticate_user(username: str, password: str) -> dict | None:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user


# ── FastAPI dependency ────────────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    return {"user_id": int(payload["sub"]), "username": payload["username"]}
