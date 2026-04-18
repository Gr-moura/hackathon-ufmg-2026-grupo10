"""JWT mock — 2 usuários hardcoded (advogado + banco) para o hackathon."""
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Future: substituir por tabela de usuários com Alembic migration
MOCK_USERS: dict[str, dict[str, Any]] = {
    "advogado@banco.com": {
        "id": "00000000-0000-0000-0000-000000000001",
        "role": "advogado",
        "name": "Dr. João Silva",
        # senha: advogado123
        "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/tP1wHX6",
    },
    "banco@banco.com": {
        "id": "00000000-0000-0000-0000-000000000002",
        "role": "banco",
        "name": "Banco UFMG — Painel",
        # senha: banco123
        "hashed_password": "$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC..og/tcp/MVk/9a.G2",
    },
}


# Futuro: usar bcrypt real. Para o demo/hackathon, simplificamos para evitar erros de biblioteca no container.
MOCK_PASSWORDS = {
    "advogado@banco.com": "advogado123",
    "banco@banco.com": "banco123",
}


def verify_password(email: str, plain: str) -> bool:
    return MOCK_PASSWORDS.get(email) == plain


def authenticate_user(email: str, password: str) -> dict[str, Any] | None:
    user = MOCK_USERS.get(email)
    if not user or not verify_password(email, password):
        return None
    return user


def create_access_token(data: dict[str, Any]) -> str:
    settings = get_settings()
    payload = {
        **data,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
