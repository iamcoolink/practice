from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from models.entity import Entity
from typing import List, Optional

class EntityRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, paper_id: int, name: str, type: str, mentions: int = 1) -> Entity:
        entity = Entity(paper_id=paper_id, name=name, type=type, mentions=mentions)
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def get_by_paper(self, paper_id: int) -> List[Entity]:
        result = await self.session.execute(
            select(Entity).where(Entity.paper_id == paper_id).order_by(Entity.type, Entity.name)
        )
        return result.scalars().all()

    async def delete_by_paper(self, paper_id: int) -> None:
        await self.session.execute(
            delete(Entity).where(Entity.paper_id == paper_id)
        )