from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from main_business.models import get_db, Chat, Message

router = APIRouter()

# 定义请求和响应模型
class MessageSchema(BaseModel):
    role: str
    content: str

    class Config:
        orm_mode = True

class ChatCreate(BaseModel):
    title: str = "新对话"

class ChatUpdate(BaseModel):
    title: str

class MessageCreate(BaseModel):
    role: str
    content: str

class ChatResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ChatDetailResponse(ChatResponse):
    messages: List[MessageSchema]

    class Config:
        orm_mode = True

# 获取所有对话
@router.get("/chats", response_model=List[ChatResponse])
def get_chats(db: Session = Depends(get_db)):
    return db.query(Chat).order_by(Chat.updated_at.desc()).all()

# 获取单个对话详情
@router.get("/chats/{chat_id}", response_model=ChatDetailResponse)
def get_chat(chat_id: int, db: Session = Depends(get_db)):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="对话不存在")
    return chat

# 创建新对话
@router.post("/chats", response_model=ChatResponse)
def create_chat(chat: ChatCreate, db: Session = Depends(get_db)):
    db_chat = Chat(title=chat.title)
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    return db_chat

# 更新对话
@router.put("/chats/{chat_id}", response_model=ChatResponse)
def update_chat(chat_id: int, chat: ChatUpdate, db: Session = Depends(get_db)):
    db_chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not db_chat:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    db_chat.title = chat.title
    db_chat.updated_at = datetime.now()
    db.commit()
    db.refresh(db_chat)
    return db_chat

# 删除对话
@router.delete("/chats/{chat_id}")
def delete_chat(chat_id: int, db: Session = Depends(get_db)):
    db_chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not db_chat:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    db.delete(db_chat)
    db.commit()
    return {"status": "success"}

# 添加消息到对话
@router.post("/chats/{chat_id}/messages", response_model=ChatDetailResponse)
def add_message(chat_id: int, message: MessageCreate, db: Session = Depends(get_db)):
    db_chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not db_chat:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    db_message = Message(chat_id=chat_id, role=message.role, content=message.content)
    db.add(db_message)
    
    # 更新对话的更新时间
    db_chat.updated_at = datetime.now()
    
    db.commit()
    db.refresh(db_chat)
    return db_chat