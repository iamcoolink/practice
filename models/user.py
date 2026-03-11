from sqlalchemy.orm import Mapped, mapped_column
from . import Base
from sqlalchemy import Integer, String, DateTime
from pwdlib import PasswordHash
from datetime import datetime
from sqlalchemy.orm import relationship

password_hash = PasswordHash.recommended()

class User(Base):
    __tablename__ = 'user'

    id: Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    email: Mapped[str] = mapped_column(String(100),unique=True,index=True)
    username: Mapped[str] = mapped_column(String(100))
    _password: Mapped[str] = mapped_column(String(200))

    papers = relationship("Paper", back_populates="user", cascade="all, delete-orphan")

#重新构造加密

    def __init__(self, *args, **kwargs):
        password =kwargs.pop('password')
        super().__init__(*args, **kwargs)
        if password:
            self.password = password

    @property    ##返回加密密码
    def password(self):
        return self._password

    @password.setter     ##原始密码
    def password(self, raw_password):
        self._password = password_hash.hash(raw_password)   ##把原始密码进行哈希处理变成加密密码返回

    def check_password(self, raw_password):
        return password_hash.verify(raw_password, self._password)


class EmailCode(Base):
    __tablename__ = 'email_code'
    id: Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    email: Mapped[str] = mapped_column(String(100))
    code: Mapped[str] = mapped_column(String(10))
    created_time: Mapped[datetime] = mapped_column(DateTime,default=datetime.now)