from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.conversation import Conversation, Role
from typing import List

class ConversationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_message(self, paper_id: int, role: Role, content: str) -> Conversation:
        msg = Conversation(paper_id=paper_id, role=role, content=content)
        self.session.add(msg)
        await self.session.flush()
        return msg

    async def get_history(self, paper_id: int, limit: int = 50) -> List[Conversation]:
        result = await self.session.execute(
            select(Conversation).where(Conversation.paper_id == paper_id).order_by(Conversation.created_at.asc()).limit(limit)
        )
        return result.scalars().all()