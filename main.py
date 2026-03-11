from fastapi import FastAPI
from fastapi_mail import FastMail,MessageSchema,MessageType
from fastapi import Depends
from dependencies import get_mail
from aiosmtplib import SMTPResponseException
from routers.auth_route import router as auth_route
from routers.paper_router import router as paper_route
from fastapi.middleware.cors import CORSMiddleware

##显示错误
import logging
logging.basicConfig(level=logging.DEBUG)

app = FastAPI()

app.add_middleware(##目的是前端用于上传
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # 你的前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_route)
app.include_router(paper_route)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.get("/mail/test")
async def mail_test(
        email: str,
        mail:FastMail=Depends(get_mail),

):
    message = MessageSchema(
        subject="hello",  #邮件标题
        recipients=[email],  #要给哪些邮箱发送邮件
        body=f"hello{email}",  #邮箱内容
        subtype=MessageType.plain,
    )
    await mail.send_message(message)
    return {"message": "发送成功"}

