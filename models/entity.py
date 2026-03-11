##提取关键实体
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from . import Base

class Entity(Base):
    __tablename__ = 'entity'

    id = Column(Integer, primary_key=True, autoincrement=True)##主体的分配编号
    paper_id = Column(Integer, ForeignKey('paper.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # person（人物）, concept（概念）, term（术语）, organization（组织）
    mentions = Column(Integer, default=1)  # 出现次数，可选

    # 关系
    paper = relationship("Paper", back_populates="entities")