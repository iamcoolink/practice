from sqlalchemy import String, Integer, ForeignKey, Text, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import Base
from datetime import datetime
import enum

class Role(enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"

class Conversation(Base):
    __tablename__ = 'conversation'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey('paper.id', ondelete='CASCADE'), nullable=False, index=True)
    role: Mapped[Role] = mapped_column(Enum(Role), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    paper = relationship("Paper", back_populates="conversations")