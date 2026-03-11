from models import AsyncSession
from models.user import User, EmailCode
from sqlalchemy import select, update, delete, exists
from datetime import datetime, timedelta
from schemas.user import UserCreateSchema
from sqlalchemy import select, update, delete, exists
from datetime import datetime, timedelta
from schemas.user import UserCreateSchema

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        # 直接使用 session，不另开事务
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def email_is_exist(self, email: str) -> bool:
        stmt = select(exists().where(User.email == email))
        result = await self.session.execute(stmt)
        return result.scalar()

    async def create(self, user_schema: UserCreateSchema) -> User:
        user = User(**user_schema.model_dump())
        self.session.add(user)
        # 不在这里提交，等待外层事务提交
        await self.session.flush()  # 可选，如果需要立即获得id
        return user

class EmailCodeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, email: str, code: str) -> EmailCode:
        email_code = EmailCode(email=email, code=code)
        self.session.add(email_code)
        await self.session.flush()
        return email_code

    async def check_email_code(self, email: str, code: str) -> bool:
        stmt = select(EmailCode).where(
            EmailCode.email == email,
            EmailCode.code == code
        ).order_by(EmailCode.created_time.desc())
        result = await self.session.execute(stmt)
        email_code = result.scalar_one_or_none()
        if not email_code:
            return False
        if (datetime.now() - email_code.created_time) > timedelta(minutes=10):
            return False
        return True