from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# 创建基础类
Base = declarative_base()

# 定义对话模型
class Chat(Base):
    __tablename__ = 'chats'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), default='新对话')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 建立与消息的关系
    messages = relationship('Message', back_populates='chat', cascade='all, delete-orphan')

# 定义消息模型
class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey('chats.id'))
    role = Column(String(50))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    
    # 建立与对话的关系
    chat = relationship('Chat', back_populates='messages')

# 数据库连接
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chat_history.db')
DATABASE_URL = f"sqlite:///{DB_PATH}"

# 创建引擎
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# 创建会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 初始化数据库
def init_db():
    Base.metadata.create_all(bind=engine)

# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()