"""SQLAlchemy models for the application."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from datetime import datetime


class UserProfile(Base):
    """User profile with learned context from documents."""
    
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True)
    
    # Learned context from documents
    profile_summary = Column(Text, nullable=True)
    expertise_areas = Column(JSON, default=list)  # List of expertise domains
    risk_tolerance = Column(String(50), default="moderate")  # low, moderate, high
    decision_style = Column(String(100), nullable=True)  # analytical, intuitive, collaborative, etc.
    
    # Portfolio and context
    portfolio_links = Column(JSON, default=list)  # List of URLs
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    documents = relationship("Document", back_populates="user_profile", cascade="all, delete-orphan")
    agents = relationship("Agent", back_populates="user_profile", cascade="all, delete-orphan")
    debate_sessions = relationship("DebateSession", back_populates="user_profile", cascade="all, delete-orphan")


class Document(Base):
    """Documents uploaded for profile learning."""
    
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_profile_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, txt, url
    file_size = Column(Integer, nullable=True)  # bytes
    
    # Processing status
    processed = Column(Boolean, default=False)
    embedding_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    
    # Metadata
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user_profile = relationship("UserProfile", back_populates="documents")


class Agent(Base):
    """AI agent configuration with system prompt."""
    
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_profile_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    
    # Agent identity
    name = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)  # e.g., "devil's advocate", "optimist", "analyst"
    description = Column(Text, nullable=True)
    
    # AI model configuration
    model_provider = Column(String(50), nullable=False)  # "gemini" or "ollama"
    model_name = Column(String(100), nullable=False)  # e.g., "gemini-pro", "llama2"
    
    # System prompt (YAML/XML format)
    system_prompt_raw = Column(Text, nullable=False)  # Raw YAML/XML
    system_prompt_parsed = Column(JSON, nullable=True)  # Parsed structure
    
    # Model parameters
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=500)
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user_profile = relationship("UserProfile", back_populates="agents")
    debate_messages = relationship("DebateMessage", back_populates="agent", cascade="all, delete-orphan")


class DebateSession(Base):
    """A debate/conversation session between multiple agents."""
    
    __tablename__ = "debate_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_profile_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    
    # Session details
    title = Column(String(255), nullable=False)
    topic = Column(Text, nullable=False)  # The decision or topic to discuss
    
    # Session configuration
    debate_format = Column(String(50), default="turn_based")  # turn_based, moderated, free_form
    agent_ids = Column(JSON, nullable=False)  # List of participating agent IDs
    max_turns = Column(Integer, default=10)
    
    # Session status
    status = Column(String(50), default="pending")  # pending, active, completed, cancelled
    
    # Results
    decision_summary = Column(Text, nullable=True)
    key_insights = Column(JSON, default=list)
    
    # Metadata
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user_profile = relationship("UserProfile", back_populates="debate_sessions")
    messages = relationship("DebateMessage", back_populates="debate_session", cascade="all, delete-orphan")


class DebateMessage(Base):
    """Individual message in a debate session."""
    
    __tablename__ = "debate_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    debate_session_id = Column(Integer, ForeignKey("debate_sessions.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    
    # Message content
    content = Column(Text, nullable=False)
    turn_number = Column(Integer, nullable=False)
    
    # Metadata
    tokens_used = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    debate_session = relationship("DebateSession", back_populates="messages")
    agent = relationship("Agent", back_populates="debate_messages")
