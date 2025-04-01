import json
import os
import contextlib
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse
import httpx
from pydantic import BaseModel
from sqlalchemy.orm import Session

from main_business.models import get_db, Chat, Message
from main_business.routes import router as chat_history_router

app = FastAPI(title="LM Chat")

# 添加CORS中间件，允许前端跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头部
)

# 注册历史对话路由
app.include_router(chat_history_router, prefix="/api")

# 挂载Vue前端静态文件目录
app.mount("/assets", StaticFiles(directory="vue-frontend/dist/assets"), name="assets")
app.mount(
    "/vite.svg", StaticFiles(directory="vue-frontend/dist", html=False), name="vite_svg"
)

# 默认LM Studio API地址
DEFAULT_API_BASE = "http://127.0.0.1:1234/v1"
api_base = os.environ.get("LM_STUDIO_API_BASE", DEFAULT_API_BASE)

# 模型列表, 这里根据.lmstudio_modles里的实际模型修改
models = ["QwQ", "qwen2.5", "deepseek-r1"]

# 获取数据库会话上下文管理器
db_context = contextlib.contextmanager(get_db)

# 定义消息模型
class MessageSchema(BaseModel):
    role: str
    content: str


# 构建聊天请求
class ChatRequest(BaseModel):
    messages: List[MessageSchema]
    model: str = models[1]
    temperature: float = 0.8
    max_tokens: int = 4096
    stream: bool = False
    chat_id: Optional[int] = None


# 构建聊天响应
class ChatResponse(BaseModel):
    choices: List[dict]

async def save_messages_to_db(messages, chat_id=None):
    """
    将消息保存到数据库。如果 chat_id 为 None 或不存在，则创建一个新的聊天。
    如果没有有效的消息可保存，则返回 chat_id 或 None。
    """
    with db_context() as db:
        # 如果提供了chat_id，检查对话是否存在
        if chat_id is not None:
            db_chat = db.query(Chat).filter(Chat.id == chat_id).first()
            if db_chat:
                # 只保存最新的用户消息（假设是消息列表中的最后一条用户消息）
                user_messages = [m for m in messages if m.role == "user"]
                if user_messages:
                    latest_user_message = user_messages[-1]
                    db_message = Message(
                        chat_id=chat_id,
                        role=latest_user_message.role,
                        content=latest_user_message.content
                    )
                    db.add(db_message)

                db_chat.updated_at = datetime.now()
                db.commit()
                return chat_id

        # 创建新对话
        user_messages = [m for m in messages if m.role == "user"]
        
        # 检查是否有非空的用户消息
        if not user_messages or not user_messages[0].content.strip():
            return None

        # 使用第一条用户消息作为对话标题（截取前20个字符）
        title = user_messages[0].content[:20] + "..." if len(user_messages[0].content) > 20 else user_messages[0].content
        db_chat = Chat(title=title)
        db.add(db_chat)
        db.commit()
        db.refresh(db_chat)
        
        # 保存所有消息（新对话的情况）
        for message in messages:
            db_message = Message(
                chat_id=db_chat.id,
                role=message.role,
                content=message.content
            )
            db.add(db_message)

        db_chat.updated_at = datetime.now()
        db.commit()
        return db_chat.id

async def save_assistant_response(chat_id, role, content):
    """保存AI回复到数据库"""
    if not content or chat_id is None:
        return
        
    with db_context() as db:
        db_message = Message(
            chat_id=chat_id,
            role=role,
            content=content
        )
        db.add(db_message)
        db.commit()

@app.post("/api/chat")
async def chat(chat_request: ChatRequest):
    # 获取chat_id
    chat_id = await save_messages_to_db(chat_request.messages, chat_request.chat_id)
    
    # 如果没有创建对话，返回错误信息
    if chat_id is None:
        error_response = {"choices": [{"message": {"role": "assistant", "content": "请输入有效的问题"}, "index": 0, "finish_reason": "stop"}]}
        if chat_request.stream:
            async def error_stream():
                yield f'data: {json.dumps({"error": "请输入有效的问题"})}\n\n'
                yield "data: [DONE]\n\n"
            return StreamingResponse(error_stream(), media_type="text/event-stream")
        return error_response

    if chat_request.stream:
        return StreamingResponse(generate_stream(chat_request, chat_id), media_type="text/event-stream")
    else:
        return await get_complete_response(chat_request, chat_id)

async def generate_stream(chat_request, chat_id):
    """流失输出"""
    ai_response_content = ""

    async with httpx.AsyncClient() as client:
        try:
            async with client.stream(
                "POST",
                f"{api_base}/chat/completions",
                json=chat_request.dict(),
                timeout=None,
            ) as response:
                response.raise_for_status()

                async for chunk in response.aiter_lines():
                    chunk = chunk.strip()
                    if chunk.startswith("data: "):
                        chunk = chunk[len("data: "):]
                        try:
                            data = json.loads(chunk)
                            
                            # 检查delta是否为空对象
                            if data.get("choices", [{}])[0].get("delta", None) == {}:
                                break

                            # 收集AI回复内容
                            content = data.get("choices", [{}])[0].get("delta", {}).get("content")
                            if content:
                                ai_response_content += content
                                
                            yield f"data: {json.dumps(data)}\n\n"
                        except json.JSONDecodeError as e:
                            yield f'data: {{"error": "JSON解析失败: {str(e)}"}}\n\n'
        except httpx.RequestError as e:
            yield f'data: {{"error": "请求异常: {str(e)}"}}\n\n'
        except Exception as e:
            yield f'data: {{"error": "未知错误: {str(e)}"}}\n\n'
        finally:
            # 保存AI回复到数据库
            await save_assistant_response(chat_id, "assistant", ai_response_content)
            yield "data: [DONE]\n\n"

async def get_complete_response(chat_request, chat_id):
    """非流失输出处理"""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{api_base}/chat/completions",
                json=chat_request.dict(),
                timeout=120,
            )
            resp.raise_for_status()
            response_data = resp.json()
            
            if not response_data.get("choices"):
                return {"choices": []}

            processed_choices = []
            for choice in response_data["choices"]:
                if "message" in choice and "content" in choice["message"]:
                    await save_assistant_response(
                        chat_id,
                        choice["message"].get("role", "assistant"),
                        choice["message"]["content"]
                    )

                    processed_choices.append({
                        "message": {
                            "role": choice["message"].get("role", "assistant"),
                            "content": choice["message"]["content"],
                        },
                        "index": choice.get("index", 0),
                        "finish_reason": choice.get("finish_reason", None),
                    })

            return {"choices": processed_choices}

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"上游API错误: {e.response.text}",
            )

app.mount(
    "/", StaticFiles(directory="vue-frontend/dist", html=True), name="vue_frontend"
)
