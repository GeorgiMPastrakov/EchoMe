from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from db import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(100), nullable=False)
    voices = relationship("Voice", back_populates="user")

class Voice(Base):
    __tablename__ = "voices"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    voice_name = Column(String(100))
    audio_file = Column(String(255))
    embedding_file = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="voices")