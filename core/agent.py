import PyPDF2
import tempfile
import os
from fastapi_cloud_cli.config import Settings
from langchain_deepseek import ChatDeepSeek
from pydantic import StrictStr
import settings
import json
from typing import List, Dict

# 初始化 LLM
llm = ChatDeepSeek(
    model="deepseek-chat",
    api_key=StrictStr(settings.DEEPSEEK_API_KEY),##这个在setting中定义了
    temperature=0.5
)

# 摘要提示模板prompt
SUMMARY_TEMPLATE = """
你是一位专业的学术助手。请根据以下论文内容，生成一份简洁、准确的摘要，概括论文的主要研究问题、方法、结果和结论。摘要应控制在300字以内。

论文内容：
{text}

请生成摘要：
"""

# 对话提示模板prompt
CHAT_TEMPLATE = """
你是一位基于论文内容的智能助手。请根据以下论文内容和对话历史，回答用户的问题。如果问题与论文无关，请礼貌地说明只能回答与论文相关的问题。

论文内容：
{paper_text}

对话历史：
{chat_history}

用户：{user_input}
助手："""

# 实体提取 prompt
ENTITY_EXTRACTION_TEMPLATE = """
你是一个专业的学术信息提取助手。请从以下论文内容中提取所有关键实体，包括人物、概念、术语、组织机构等。
请以 JSON 格式返回，格式如下：
[
  {{"name": "实体名称", "type": "person/concept/term/organization", "mentions": 出现次数}}
]
仅返回 JSON，不要任何额外文字。

论文内容：
{text}
"""

# 思维导图生成 prompt
MINDMAP_TEMPLATE = """
你是一个论文结构分析专家。请根据以下论文内容，提取其主要章节、子章节、关键论点，并生成一个层级化的 JSON 结构，用于绘制思维导图。
要求：
- 根节点为论文标题（如果没有标题，则用“论文”）
- 一级节点为引言、方法、实验、结论等主要部分
- 二级节点为各部分下的子主题
- 如果原文有明确的标题（如“## 引言”），请直接使用；否则根据内容概括。
- 如果论文内容太短，至少提取出核心主题。
- 仅返回 JSON，不要任何额外文字。

输出格式示例：
{{
  "root": "论文标题",
  "children": [
    {{"name": "引言", "children": [{{"name": "研究背景"}}, {{"name": "问题定义"}}]}},
    {{"name": "方法", "children": [{{"name": "模型架构"}}, {{"name": "训练策略"}}]}},
    {{"name": "实验", "children": [{{"name": "数据集"}}, {{"name": "结果分析"}}]}},
    {{"name": "结论", "children": []}}
  ]
}}

论文内容：
{text}
"""

# 笔记生成 prompt
NOTE_TEMPLATE = """
你是一个智能笔记助手。请根据以下论文内容、摘要和关键实体，生成一份结构清晰、易于理解的笔记。
笔记应包括：
- 研究背景
- 主要方法
- 关键结果
- 结论与展望
使用 Markdown 格式，适当使用标题、列表、引用。

论文内容：
{paper_text}

摘要：
{summary}

关键实体：
{entities}

请生成笔记：
"""

async def extract_text_from_pdf(file_path: str) -> str:
    """从PDF文件提取文本"""
    text = ""
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

async def generate_summary(text: str) -> str:
    """生成摘要"""
    prompt = SUMMARY_TEMPLATE.format(text=text)
    response = await llm.ainvoke(prompt)
    return response.content.strip()

async def generate_chat_response(paper_text: str, chat_history: str, user_input: str) -> str:
    """生成对话回复"""
    prompt = CHAT_TEMPLATE.format(
        paper_text=paper_text,
        chat_history=chat_history,
        user_input=user_input
    )
    response = await llm.ainvoke(prompt)
    return response.content.strip()

async def extract_entities(text: str) -> List[Dict]:
    """从论文文本中提取实体"""
    prompt = ENTITY_EXTRACTION_TEMPLATE.format(text=text[:10000])  # 截断防止超长
    try:
        response = await llm.ainvoke(prompt)
        content = response.content.strip()
        # 解析 JSON
        entities = json.loads(content)
        # 确保格式正确
        if not isinstance(entities, list):
            raise ValueError("返回的不是列表")
        return entities
    except Exception as e:
        # 出错时返回空列表
        print(f"实体提取失败: {e}")
        return []

async def generate_mindmap(text: str) -> Dict:
    """生成思维导图"""
    prompt = MINDMAP_TEMPLATE.format(text=text[:10000])
    try:
        response = await llm.ainvoke(prompt)
        content = response.content.strip()
        print("===== LLM Raw Output =====")#思维导图的正式获取
        print(content)
        print("===========================")

        # 用正则提取 JSON 对象（第一个 { 到最后一个 }）
        import re
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            json_str = match.group()
        else:
            json_str = content  # 如果没找到，回退到原内容

        mindmap = json.loads(json_str)
        return mindmap
    except Exception as e:
        print(f"思维导图生成失败: {e}")
        # 可选：打印 json_str 帮助调试
        return {"root": "论文", "children": []}

async def generate_note(paper_text: str, summary: str, entities: List[str]) -> str:
    """生成笔记"""
    entities_str = ", ".join(entities) if entities else "无"
    prompt = NOTE_TEMPLATE.format(
        paper_text=paper_text[:8000],  # 进一步截断，因为摘要和实体也会占 token
        summary=summary,
        entities=entities_str
    )
    try:
        response = await llm.ainvoke(prompt)
        return response.content.strip()
    except Exception as e:
        print(f"笔记生成失败: {e}")
        return "笔记生成失败，请稍后重试。"