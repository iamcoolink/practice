from core.mail import create_mail_instance
from core.auth import AuthHandler
from fastapi import Depends, FastAPI,Security
from sqlalchemy.ext.asyncio import AsyncSession
from models import AsyncSessionFactory
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()
auth_handler = AuthHandler()

async def get_session() -> AsyncSession:
    session = AsyncSessionFactory()
    try:
        yield session
    finally:
        await session.close()


async def get_mail() -> FastAPI:
    return create_mail_instance()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> int:
    token = credentials.credentials
    return auth_handler.verify_access_token(token)