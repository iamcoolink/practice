from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from models.note import Note
from typing import Optional
from datetime import datetime

class NoteRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, paper_id: int, content: str) -> Note:
        note = Note(paper_id=paper_id, content=content)
        self.session.add(note)
        await self.session.flush()
        return note

    async def get_by_paper(self, paper_id: int) -> Optional[Note]:
        result = await self.session.execute(
            select(Note).where(Note.paper_id == paper_id).order_by(Note.created_at.desc())
        )
        return result.scalar_one_or_none()

    async def update(self, paper_id: int, content: str) -> Optional[Note]:
        note = await self.get_by_paper(paper_id)
        if note:
            note.content = content
            note.updated_at = datetime.now()
            await self.session.flush()
        return note

    async def delete(self, paper_id: int) -> None:
        await self.session.execute(
            delete(Note).where(Note.paper_id == paper_id)
        )