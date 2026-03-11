##返回一个固定值，不会返回前端

from pydantic import BaseModel, Field
from typing import Annotated, Literal

class ResponseOut(BaseModel):
    result: Annotated[Literal["success", "failure"], Field("success", description="操作结果")]