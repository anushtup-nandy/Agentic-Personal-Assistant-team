"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# User Profile Schemas
class UserProfileCreate(BaseModel):
    """Schema for creating a user profile."""
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    portfolio_links: Optional[List[str]] = []


class UserProfileResponse(BaseModel):
    """Schema for user profile response."""
    id: int
    name: str
    email: str
    profile_summary: Optional[str]
    expertise_areas: List[str]
    risk_tolerance: str
    decision_style: Optional[str]
    portfolio_links: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Document Schemas
class DocumentResponse(BaseModel):
    """Schema for document response."""
    id: int
    filename: str
    file_type: str
    file_size: Optional[int]
    processed: bool
    embedding_status: str
    uploaded_at: datetime
    
    class Config:
        from_attributes = True


# Agent Schemas
class AgentCreate(BaseModel):
    """Schema for creating an agent."""
    name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    model_provider: str = Field(..., pattern="^(gemini|ollama)$")
    model_name: str
    system_prompt_raw: str
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=500, ge=1, le=4000)


class AgentUpdate(BaseModel):
    """Schema for updating an agent."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    model_provider: Optional[str] = Field(None, pattern="^(gemini|ollama)$")
    model_name: Optional[str] = None
    system_prompt_raw: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=4000)
    is_active: Optional[bool] = None


class AgentResponse(BaseModel):
    """Schema for agent response."""
    id: int
    name: str
    role: str
    description: Optional[str]
    model_provider: str
    model_name: str
    system_prompt_raw: str
    temperature: float
    max_tokens: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Debate Session Schemas
class DebateSessionCreate(BaseModel):
    """Schema for creating a debate session."""
    title: str = Field(..., min_length=1, max_length=255)
    topic: str = Field(..., min_length=1)
    agent_ids: List[int] = Field(..., min_items=2)
    debate_format: str = Field(default="turn_based", pattern="^(turn_based|moderated|free_form)$")
    max_turns: int = Field(default=10, ge=1, le=50)


class DebateMessageResponse(BaseModel):
    """Schema for debate message."""
    id: int
    agent_id: int
    content: str
    turn_number: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class DebateSessionResponse(BaseModel):
    """Schema for debate session response."""
    id: int
    title: str
    topic: str
    debate_format: str
    agent_ids: List[int]
    status: str
    decision_summary: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class DebateSessionDetail(DebateSessionResponse):
    """Schema for detailed debate session with messages."""
    messages: List[DebateMessageResponse]


# Validation Schemas
class PromptValidationRequest(BaseModel):
    """Schema for prompt validation request."""
    raw_prompt: str


class PromptValidationResponse(BaseModel):
    """Schema for prompt validation response."""
    is_valid: bool
    variables: List[str]
    error_message: Optional[str] = None


# Generic Responses
class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    details: Optional[Dict[str, Any]] = None
