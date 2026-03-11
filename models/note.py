##整理笔记功能
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from . import Base
from datetime import datetime

class Note(Base):
    __tablename__ = 'note'

    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(Integer, ForeignKey('paper.id', ondelete='CASCADE'), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    paper = relationship("Paper", back_populates="notes")