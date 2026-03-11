from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from repository.conversation_repo import ConversationRepository, Role
from schemas.paper import (
    PaperOut, PaperSummaryOut, ChatIn,
    ChatHistoryOut, ChatMessageOut
)
from core.agent import extract_text_from_pdf, generate_summary, generate_chat_response
import tempfile
import os
import shutil
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies import get_session, get_current_user
from repository.paper_repo import PaperRepository
from repository.entity_repo import EntityRepository
from repository.note_repo import NoteRepository
from schemas.paper import EntityOut, MindmapOut, NoteIn, NoteOut
from core.agent import extract_entities, generate_mindmap, generate_note
from typing import List

router = APIRouter(prefix="/paper", tags=["paper"])

@router.post("/upload", response_model=PaperOut)#上传pdf文件或粘贴文件
async def upload_paper(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user)
):
    if not file and not text:
        raise HTTPException(status_code=400, detail="必须提供PDF文件或粘贴文本")

    original_text = ""
    file_path = None
    if file:
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        try:
            original_text = await extract_text_from_pdf(tmp_path)
            file_path = tmp_path
        except Exception as e:
            os.unlink(tmp_path)
            raise HTTPException(status_code=500, detail=f"PDF提取失败: {str(e)}")
    else:
        original_text = text

    if not original_text.strip():
        raise HTTPException(status_code=400, detail="提取的文本为空")

    paper_repo = PaperRepository(session)
    paper = await paper_repo.create(
        user_id=user_id,
        original_text=original_text[:10000],  # 截断避免过大
        title=title,
        file_path=file_path
    )
    await session.commit()

    return PaperOut(
        id=paper.id,
        user_id=paper.user_id,
        title=paper.title,
        original_text=paper.original_text[:500] + "..." if len(paper.original_text) > 500 else paper.original_text,
        summary=paper.summary,
        status=paper.status.value,
        created_at=paper.created_at,
        updated_at=paper.updated_at
    )

@router.post("/{paper_id}/summarize", response_model=PaperSummaryOut)#生成摘要
async def summarize_paper(
    paper_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user)
):
    paper_repo = PaperRepository(session)
    paper = await paper_repo.get_by_id(paper_id)
    if not paper or paper.user_id != user_id:
        raise HTTPException(status_code=404, detail="论文不存在或无权限")

    if paper.status == "summarized" and paper.summary:
        return PaperSummaryOut(paper_id=paper_id, summary=paper.summary)

    try:
        summary = await generate_summary(paper.original_text)
    except Exception as e:
        await paper_repo.update_status(paper_id, "error")
        await session.commit()
        raise HTTPException(status_code=500, detail=f"摘要生成失败: {str(e)}")

    await paper_repo.update_summary(paper_id, summary)
    await session.commit()

    return PaperSummaryOut(paper_id=paper_id, summary=summary)

@router.post("/{paper_id}/chat", response_model=ChatMessageOut)#实现多轮对话操作
async def chat_with_paper(
    paper_id: int,
    chat_in: ChatIn,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user)
):
    paper_repo = PaperRepository(session)
    paper = await paper_repo.get_by_id(paper_id)
    if not paper or paper.user_id != user_id:
        raise HTTPException(status_code=404, detail="论文不存在或无权限")

    conv_repo = ConversationRepository(session)
    history = await conv_repo.get_history(paper_id)
    chat_history = ""
    for msg in history:
        role = "用户" if msg.role == Role.USER else "助手"
        chat_history += f"{role}: {msg.content}\n"

    await conv_repo.add_message(paper_id, Role.USER, chat_in.message)

    try:
        answer = await generate_chat_response(paper.original_text, chat_history, chat_in.message)
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"对话生成失败: {str(e)}")

    assistant_msg = await conv_repo.add_message(paper_id, Role.ASSISTANT, answer)
    await session.commit()

    return ChatMessageOut(
        role=assistant_msg.role.value,
        content=assistant_msg.content,
        created_at=assistant_msg.created_at
    )

@router.get("/{paper_id}/history", response_model=ChatHistoryOut)#获取对话的历史
async def get_chat_history(
    paper_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user)
):
    paper_repo = PaperRepository(session)
    paper = await paper_repo.get_by_id(paper_id)
    if not paper or paper.user_id != user_id:
        raise HTTPException(status_code=404, detail="论文不存在或无权限")

    conv_repo = ConversationRepository(session)
    history = await conv_repo.get_history(paper_id)
    messages = [
        ChatMessageOut(role=msg.role.value, content=msg.content, created_at=msg.created_at)
        for msg in history
    ]
    return ChatHistoryOut(paper_id=paper_id, messages=messages)

@router.get("/list", response_model=List[PaperOut])#列出用户论文
async def list_papers(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user)
):
    paper_repo = PaperRepository(session)
    papers = await paper_repo.get_by_user(user_id, skip, limit)
    return [
        PaperOut(
            id=p.id,
            user_id=p.user_id,
            title=p.title,
            original_text=p.original_text[:200] + "..." if len(p.original_text) > 200 else p.original_text,
            summary=p.summary,
            status=p.status.value,
            created_at=p.created_at,
            updated_at=p.updated_at
        )
        for p in papers
    ]


@router.get("/{paper_id}/entities", response_model=List[EntityOut])
async def get_entities(
    paper_id: int,
    refresh: bool = False,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user)
):
    """获取论文的实体列表，可选择刷新（重新提取）"""
    paper_repo = PaperRepository(session)
    paper = await paper_repo.get_by_id(paper_id)
    if not paper or paper.user_id != user_id:
        raise HTTPException(status_code=404, detail="论文不存在或无权限")

    entity_repo = EntityRepository(session)
    if refresh:
        # 删除旧实体，重新提取
        await entity_repo.delete_by_paper(paper_id)
        entities_data = await extract_entities(paper.original_text)
        for ent in entities_data:
            await entity_repo.create(
                paper_id=paper_id,
                name=ent["name"],
                type=ent["type"],
                mentions=ent.get("mentions", 1)
            )
        await session.commit()

    entities = await entity_repo.get_by_paper(paper_id)
    return entities

@router.get("/{paper_id}/mindmap", response_model=MindmapOut)
async def get_mindmap(
    paper_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user)
):
    """生成论文的思维导图（实时生成，不存储）"""
    paper_repo = PaperRepository(session)
    paper = await paper_repo.get_by_id(paper_id)
    if not paper or paper.user_id != user_id:
        raise HTTPException(status_code=404, detail="论文不存在或无权限")

    mindmap_data = await generate_mindmap(paper.original_text)
    return MindmapOut(data=mindmap_data)

@router.get("/{paper_id}/note", response_model=NoteOut)
async def get_note(
    paper_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user)
):
    """获取论文的笔记（如果不存在则自动生成）"""
    paper_repo = PaperRepository(session)
    paper = await paper_repo.get_by_id(paper_id)
    if not paper or paper.user_id != user_id:
        raise HTTPException(status_code=404, detail="论文不存在或无权限")

    note_repo = NoteRepository(session)
    note = await note_repo.get_by_paper(paper_id)
    if not note:
        # 需要生成笔记
        # 先获取实体（如果已存在则用，否则提取）
        entity_repo = EntityRepository(session)
        entities = await entity_repo.get_by_paper(paper_id)
        if not entities:
            # 如果还没有实体，自动提取
            entities_data = await extract_entities(paper.original_text)
            for ent in entities_data:
                await entity_repo.create(
                    paper_id=paper_id,
                    name=ent["name"],
                    type=ent["type"],
                    mentions=ent.get("mentions", 1)
                )
            await session.flush()
            entities = await entity_repo.get_by_paper(paper_id)

        entity_names = [e.name for e in entities]
        note_content = await generate_note(
            paper_text=paper.original_text,
            summary=paper.summary or "",
            entities=entity_names
        )
        note = await note_repo.create(paper_id, note_content)
        await session.commit()

    return note

@router.put("/{paper_id}/note", response_model=NoteOut)
async def update_note(
    paper_id: int,
    note_in: NoteIn,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user)
):
    """更新笔记（用户手动编辑）"""
    paper_repo = PaperRepository(session)
    paper = await paper_repo.get_by_id(paper_id)
    if not paper or paper.user_id != user_id:
        raise HTTPException(status_code=404, detail="论文不存在或无权限")

    note_repo = NoteRepository(session)
    note = await note_repo.update(paper_id, note_in.content)
    if not note:
        # 如果笔记不存在，创建新笔记
        note = await note_repo.create(paper_id, note_in.content)
    await session.commit()
    return note

@router.delete("/{paper_id}/note")
async def delete_note(
    paper_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user)
):
    """删除笔记"""
    paper_repo = PaperRepository(session)
    paper = await paper_repo.get_by_id(paper_id)
    if not paper or paper.user_id != user_id:
        raise HTTPException(status_code=404, detail="论文不存在或无权限")

    note_repo = NoteRepository(session)
    await note_repo.delete(paper_id)
    await session.commit()
    return {"message": "笔记已删除"}

@router.get("/{paper_id}", response_model=PaperOut)##与前端相联合，获取单篇论文
async def get_paper(
    paper_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user)
):
    paper_repo = PaperRepository(session)
    paper = await paper_repo.get_by_id(paper_id)
    if not paper or paper.user_id != user_id:
        raise HTTPException(status_code=404, detail="论文不存在或无权限")
    return paper