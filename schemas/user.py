from pydantic import BaseModel, EmailStr,Field ,model_validator
from typing import Annotated
from models.user import User

UsernameStr = Annotated[str, Field(min_length=6, max_length=20, description="用户名")]
PasswordStr = Annotated[str, Field(min_length=6, max_length=20, description="密码")]


class RegisterIn(BaseModel):
    email: EmailStr
    username: UsernameStr
    password: PasswordStr
    confirm_password:PasswordStr
    code:Annotated[str,Field(min_length=6,max_length=6,description="邮箱验证码")]

    @model_validator(mode="after")
    def passwords_is_match(self):
        if self.password != self.confirm_password:
            raise ValueError("两个密码不一致")
        return self



class UserCreateSchema(BaseModel):  ##接送数据在数据库之中
    email: EmailStr
    username: UsernameStr
    password: PasswordStr



## 下面是登录功能
class LoginIn(BaseModel):
    email: EmailStr
    password: PasswordStr


class UserSchema(BaseModel):
    id:Annotated[int,Field(...)]
    email: EmailStr
    username: UsernameStr


class LoginOut(BaseModel):
    user:UserSchema
    token:str
