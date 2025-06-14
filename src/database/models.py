# src/database/models.py - Fixed to work without pgvector
"""
SQLAlchemy models for Steve Connect database
Defines all tables and relationships
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from .connection import Base

class Session(Base):
    """
    User conversation sessions
    Tracks individual user interactions with Steve Connect
    """
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    context_memories = relationship("ContextMemory", back_populates="session", cascade="all, delete-orphan")
    app_states = relationship("AppState", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, active={self.is_active})>"

class ContextMemory(Base):
    """
    Stores conversation context across different apps
    """
    __tablename__ = "context_memory"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    app_name = Column(String(100), nullable=False)
    context_data = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relationships
    session = relationship("Session", back_populates="context_memories")
    
    def __repr__(self):
        return f"<ContextMemory(app={self.app_name}, session={self.session_id})>"

class KnowledgeBase(Base):
    """
    RAG knowledge base for app capabilities and documentation
    Using TEXT instead of Vector for compatibility
    """
    __tablename__ = "knowledge_base"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    meta_data = Column(JSONB)
    embedding = Column(Text)  # Using Text instead of Vector
    created_at = Column(DateTime, default=func.current_timestamp())
    
    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, content_length={len(self.content) if self.content else 0})>"

class AppState(Base):
    """
    Tracks current app state and navigation
    """
    __tablename__ = "app_states"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    current_app = Column(String(100))
    previous_app = Column(String(100))
    state_data = Column(JSONB)
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    session = relationship("Session", back_populates="app_states")
    
    def __repr__(self):
        return f"<AppState(current={self.current_app}, previous={self.previous_app})>"

# Create indexes for better performance
Index('idx_sessions_user_id', Session.user_id)
Index('idx_context_session_id', ContextMemory.session_id)
Index('idx_context_app_name', ContextMemory.app_name)
Index('idx_app_states_session_id', AppState.session_id)