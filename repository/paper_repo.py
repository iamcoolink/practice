from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from models.paper import Paper, PaperStatus
from typing import Optional, List

class PaperRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, original_text: str, title: Optional[str] = None, file_path: Optional[str] = None) -> Paper:
        paper = Paper(
            user_id=user_id,
            original_text=original_text,
            title=title,
            file_path=file_path,
            status=PaperStatus.UPLOADED
        )
        self.session.add(paper)
        await self.session.flush()
        return paper

    async def get_by_id(self, paper_id: int) -> Optional[Paper]:
        result = await self.session.execute(select(Paper).where(Paper.id == paper_id))
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: int, skip: int = 0, limit: int = 10) -> List[Paper]:
        result = await self.session.execute(
            select(Paper).where(Paper.user_id == user_id).order_by(Paper.created_at.desc()).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def update_summary(self, paper_id: int, summary: str) -> None:
        await self.session.execute(
            update(Paper).where(Paper.id == paper_id).values(summary=summary, status=PaperStatus.SUMMARIZED)
        )

    async def update_status(self, paper_id: int, status: PaperStatus) -> None:
        await self.session.execute(
            update(Paper).where(Paper.id == paper_id).values(status=status)
        )