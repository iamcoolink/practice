#核心功能

from sqlalchemy import String, Integer, ForeignKey, Text, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import Base
from datetime import datetime
import enum

class PaperStatus(enum.Enum):
    UPLOADED = "uploaded"
    SUMMARIZED = "summarized"
    ERROR = "error"

class Paper(Base):
    __tablename__ = 'paper'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=True)
    original_text: Mapped[str] = mapped_column(Text, nullable=False)#源文件
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[PaperStatus] = mapped_column(Enum(PaperStatus), default=PaperStatus.UPLOADED)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="papers")
    conversations = relationship("Conversation", back_populates="paper", cascade="all, delete-orphan")
    entities = relationship("Entity", back_populates="paper", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="paper", cascade="all, delete-orphan")
