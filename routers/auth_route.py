from fastapi import APIRouter, Depends, HTTPException
from fastapi_mail import FastMail, MessageSchema, MessageType
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies import get_session, get_mail
from repository.user_repo import EmailCodeRepository, UserRepository
import random
from schemas import ResponseOut
from schemas.user import RegisterIn, UserCreateSchema, LoginIn, LoginOut
from models.user import User
from core.auth import AuthHandler

router = APIRouter(prefix="/auth", tags=['user'])
auth_handler = AuthHandler()

def generate_code():
    return str(random.randint(100000, 999999))

@router.get("/code")
async def get_email_code(
    email: str,
    session: AsyncSession = Depends(get_session),
    mail: FastMail = Depends(get_mail)
):
    async with session.begin():  # 开启事务
        code = generate_code()
        repo = EmailCodeRepository(session)
        await repo.create(email, code)

        message = MessageSchema(
            subject="验证码",
            recipients=[email],
            body=f"您的验证码是：{code}",
            subtype=MessageType.plain
        )
        await mail.send_message(message)

    return {"message": "验证码已发送"}

@router.post("/register", response_model=ResponseOut)
async def register(
    data: RegisterIn,
    session: AsyncSession = Depends(get_session),
):
    async with session.begin():  # 开启顶层事务
        # 1. 判断邮箱是否存在
        user_repo = UserRepository(session)
        email_exist = await user_repo.email_is_exist(str(data.email))
        if email_exist:
            raise HTTPException(status_code=400, detail="邮箱或验证码错误！")

        # 2. 判断验证码是否正确
        email_code_repo = EmailCodeRepository(session)
        email_code_match = await email_code_repo.check_email_code(email=str(data.email), code=str(data.code))
        if not email_code_match:
            raise HTTPException(status_code=400, detail="邮箱或验证码错误！")

        # 3. 创建用户
        await user_repo.create(UserCreateSchema(
            email=str(data.email),
            password=data.password,
            username=str(data.username)
        ))

    return ResponseOut()

@router.post("/login", response_model=LoginOut)
async def login(
    data: LoginIn,
    session: AsyncSession = Depends(get_session),
):
    # 登录不需要事务，只读操作
    user_repo = UserRepository(session)
    user = await user_repo.get_by_email(str(data.email))
    if not user:
        raise HTTPException(status_code=400, detail="该用户不存在！")
    if not user.check_password(data.password):
        raise HTTPException(status_code=400, detail="邮箱或密码错误！")

    tokens = auth_handler.encode_login_token(user.id)
    return {
        "user": user,
        "token": tokens["access_token"]
    }