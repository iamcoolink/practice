from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class PaperStatusEnum(str, Enum):
    UPLOADED = "uploaded"
    SUMMARIZED = "summarized"
    ERROR = "error"

class PaperUploadIn(BaseModel):
    text: Optional[str] = Field(None, description="直接粘贴的文本内容")
    title: Optional[str] = Field(None, description="论文标题")

class PaperOut(BaseModel):
    id: int
    user_id: int
    title: Optional[str]
    original_text: str
    summary: Optional[str]
    status: PaperStatusEnum
    created_at: datetime
    updated_at: datetime

class PaperSummaryOut(BaseModel):
    paper_id: int
    summary: str

class ChatIn(BaseModel):
    message: str

class ChatMessageOut(BaseModel):
    role: str
    content: str
    created_at: datetime

class ChatHistoryOut(BaseModel):
    paper_id: int
    messages: List[ChatMessageOut]

class EntityOut(BaseModel):
    id: int
    paper_id: int
    name: str
    type: str
    mentions: int

    model_config = ConfigDict(from_attributes=True)

class MindmapOut(BaseModel):
    data: Dict[str, Any]  # 思维导图的JSON结构

class NoteIn(BaseModel):
    content: str

class NoteOut(BaseModel):
    id: int
    paper_id: int
    content: str
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)