"""FastAPI application - main entry point."""
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import shutil
from pathlib import Path
import json
from datetime import datetime

from config import settings
from database import get_db, init_db, engine
from models import UserProfile, Agent, DebateSession, DebateMessage, Document, Base
from schemas import (
    UserProfileCreate, UserProfileResponse,
    AgentCreate, AgentUpdate, AgentResponse,
    DebateSessionCreate, DebateSessionResponse, DebateSessionDetail,
    DocumentResponse, MessageResponse,
    PromptValidationRequest, PromptValidationResponse
)
from services.profile_engine import ProfileEngine
from services.agent_orchestrator import AgentOrchestrator
from services.prompt_parser import PromptParser, DEFAULT_AGENT_TEMPLATE

# Create FastAPI app
app = FastAPI(
    title="Multi-Agent Decision Support API",
    description="AI-powered multi-agent system for collaborative decision making",
    version="1.0.0",
    debug=settings.debug
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload directory
UPLOAD_DIR = Path("./data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()
    print("✅ Database initialized")


# ==================== User Profile Endpoints ====================

@app.post("/api/profiles", response_model=UserProfileResponse, status_code=201)
async def create_profile(
    profile: UserProfileCreate,
    db: Session = Depends(get_db)
):
    """Create a new user profile."""
    # Check if email exists
    existing = db.query(UserProfile).filter(UserProfile.email == profile.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_profile = UserProfile(
        name=profile.name,
        email=profile.email,
        portfolio_links=profile.portfolio_links
    )
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    
    return new_profile


@app.get("/api/profiles/{profile_id}", response_model=UserProfileResponse)
async def get_profile(profile_id: int, db: Session = Depends(get_db)):
    """Get a user profile by ID."""
    profile = db.query(UserProfile).filter(UserProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@app.get("/api/profiles", response_model=List[UserProfileResponse])
async def list_profiles(db: Session = Depends(get_db)):
    """List all user profiles."""
    profiles = db.query(UserProfile).all()
    return profiles


@app.get("/api/profiles/by-email/{email}", response_model=UserProfileResponse)
async def get_profile_by_email(email: str, db: Session = Depends(get_db)):
    """Get a user profile by email (for login)."""
    profile = db.query(UserProfile).filter(UserProfile.email == email).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


# ==================== Document Endpoints ====================

@app.post("/api/profiles/{profile_id}/documents", response_model=DocumentResponse)
async def upload_document(
    profile_id: int,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Upload a document for profile learning."""
    # Verify profile exists
    profile = db.query(UserProfile).filter(UserProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Determine file type
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in ['pdf', 'txt', 'docx']:
        raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF, TXT, or DOCX")
    
    # Save file
    user_upload_dir = UPLOAD_DIR / f"user_{profile_id}"
    user_upload_dir.mkdir(exist_ok=True)
    
    file_path = user_upload_dir / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create document record
    document = Document(
        user_profile_id=profile_id,
        filename=file.filename,
        file_path=str(file_path),
        file_type=file_extension,
        file_size=file_path.stat().st_size
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Process document in background
    if background_tasks:
        background_tasks.add_task(
            process_document_task,
            document.id,
            str(file_path),
            file_extension
        )
    
    return document


@app.get("/api/profiles/{profile_id}/documents", response_model=List[DocumentResponse])
async def list_documents(profile_id: int, db: Session = Depends(get_db)):
    """List all documents for a profile."""
    documents = db.query(Document).filter(
        Document.user_profile_id == profile_id
    ).all()
    return documents


@app.delete("/api/documents/{document_id}", status_code=204)
async def delete_document(document_id: int, db: Session = Depends(get_db)):
    """Delete a document."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete physical file
    file_path = Path(document.file_path)
    if file_path.exists():
        file_path.unlink()
    
    db.delete(document)
    db.commit()
    
    return None


@app.post("/api/profiles/{profile_id}/generate-summary", response_model=MessageResponse)
async def generate_profile_summary(profile_id: int, db: Session = Depends(get_db)):
    """Generate profile summary from uploaded documents."""
    profile = db.query(UserProfile).filter(UserProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    engine_instance = ProfileEngine(db)
    summary = await engine_instance.generate_profile_summary(profile_id)
    
    if not summary:
        raise HTTPException(status_code=500, detail="Failed to generate summary")
    
    # Also extract expertise areas
    expertise = await engine_instance.extract_expertise_areas(profile_id)
    
    return MessageResponse(
        message="Profile summary generated successfully",
        details={
            "summary": summary,
            "expertise_areas": expertise
        }
    )


# ==================== Agent Endpoints ====================

@app.post("/api/profiles/{profile_id}/agents", response_model=AgentResponse, status_code=201)
async def create_agent(
    profile_id: int,
    agent: AgentCreate,
    db: Session = Depends(get_db)
):
    """Create a new agent."""
    # Verify profile exists
    profile = db.query(UserProfile).filter(UserProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Validate prompt
    parser = PromptParser()
    is_valid, error = parser.validate_prompt(agent.system_prompt_raw)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid prompt: {error}")
    
    # Parse prompt
    parsed_prompt = parser.parse(agent.system_prompt_raw)
    
    new_agent = Agent(
        user_profile_id=profile_id,
        name=agent.name,
        role=agent.role,
        description=agent.description,
        model_provider=agent.model_provider,
        model_name=agent.model_name,
        system_prompt_raw=agent.system_prompt_raw,
        system_prompt_parsed=parsed_prompt,
        temperature=agent.temperature,
        max_tokens=agent.max_tokens
    )
    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)
    
    return new_agent


@app.get("/api/profiles/{profile_id}/agents", response_model=List[AgentResponse])
async def list_agents(
    profile_id: int,
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """List all agents for a profile."""
    query = db.query(Agent).filter(Agent.user_profile_id == profile_id)
    
    if active_only:
        query = query.filter(Agent.is_active == True)
    
    agents = query.all()
    return agents


@app.get("/api/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: int, db: Session = Depends(get_db)):
    """Get an agent by ID."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@app.patch("/api/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    agent_update: AgentUpdate,
    db: Session = Depends(get_db)
):
    """Update an agent."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Update fields
    update_data = agent_update.model_dump(exclude_unset=True)
    
    # Validate prompt if provided
    if "system_prompt_raw" in update_data:
        parser = PromptParser()
        is_valid, error = parser.validate_prompt(update_data["system_prompt_raw"])
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid prompt: {error}")
        
        parsed_prompt = parser.parse(update_data["system_prompt_raw"])
        update_data["system_prompt_parsed"] = parsed_prompt
    
    for key, value in update_data.items():
        setattr(agent, key, value)
    
    db.commit()
    db.refresh(agent)
    
    return agent


@app.delete("/api/agents/{agent_id}", status_code=204)
async def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    """Delete an agent."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    db.delete(agent)
    db.commit()
    
    return None


# ==================== Debate Session Endpoints ====================

@app.post("/api/profiles/{profile_id}/debates", response_model=DebateSessionResponse, status_code=201)
async def create_debate_session(
    profile_id: int,
    debate: DebateSessionCreate,
    db: Session = Depends(get_db)
):
    """Create a new debate session."""
    # Verify profile exists
    profile = db.query(UserProfile).filter(UserProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Verify all agents exist and belong to this profile
    agents = db.query(Agent).filter(Agent.id.in_(debate.agent_ids)).all()
    if len(agents) != len(debate.agent_ids):
        raise HTTPException(status_code=400, detail="Some agents not found")
    
    for agent in agents:
        if agent.user_profile_id != profile_id:
            raise HTTPException(status_code=403, detail="Agent does not belong to this profile")
    
    new_session = DebateSession(
        user_profile_id=profile_id,
        title=debate.title,
        topic=debate.topic,
        debate_format=debate.debate_format,
        agent_ids=debate.agent_ids,
        max_turns=debate.max_turns
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return new_session


@app.get("/api/debates/{session_id}", response_model=DebateSessionDetail)
async def get_debate_session(session_id: int, db: Session = Depends(get_db)):
    """Get a debate session with all messages."""
    session = db.query(DebateSession).filter(DebateSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Fetch messages with agent information
    messages = db.query(DebateMessage, Agent).join(
        Agent, DebateMessage.agent_id == Agent.id
    ).filter(
        DebateMessage.debate_session_id == session_id
    ).order_by(DebateMessage.turn_number).all()
    
    # Build response with agent details
    response_data = {
        **session.__dict__,
        "messages": [
            {
                "id": msg.id,
                "agent_id": msg.agent_id,
                "agent_name": agent.name,
                "agent_role": agent.role,
                "content": msg.content,
                "turn": msg.turn_number,  # Map turn_number to turn for frontend
                "created_at": msg.created_at
            }
            for msg, agent in messages
        ]
    }
    
    return response_data


@app.get("/api/profiles/{profile_id}/debates", response_model=List[DebateSessionResponse])
async def list_debate_sessions(profile_id: int, db: Session = Depends(get_db)):
    """List all debate sessions for a profile."""
    sessions = db.query(DebateSession).filter(
        DebateSession.user_profile_id == profile_id
    ).order_by(DebateSession.created_at.desc()).all()
    return sessions


@app.delete("/api/debates/{session_id}", status_code=204)
async def delete_debate_session(session_id: int, db: Session = Depends(get_db)):
    """Delete a debate session and all its messages."""
    session = db.query(DebateSession).filter(DebateSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Delete all messages first (due to foreign key constraint)
    db.query(DebateMessage).filter(DebateMessage.debate_session_id == session_id).delete()
    
    # Delete the session
    db.delete(session)
    db.commit()
    
    return None


@app.get("/api/debates/{session_id}/start")
async def start_debate(session_id: int, db: Session = Depends(get_db)):
    """Start a debate session and stream the responses."""
    session = db.query(DebateSession).filter(DebateSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status != "pending":
        raise HTTPException(status_code=400, detail="Session already started or completed")
    
    orchestrator = AgentOrchestrator(db)
    
    async def event_generator():
        """Generate server-sent events for debate messages."""
        try:
            async for message in orchestrator.start_debate(
                session_id=session_id,
                agent_ids=session.agent_ids,
                topic=session.topic,
                max_turns=session.max_turns,
                debate_format=session.debate_format
            ):
                # Send as JSON event
                yield f"data: {json.dumps(message)}\n\n"
            
            # Generate summary at the end
            summary = await orchestrator.generate_debate_summary(session_id)
            if summary:
                yield f"data: {json.dumps({'type': 'summary', 'data': summary})}\n\n"
            
            yield "data: {\"type\": \"complete\"}\n\n"
            
        except Exception as e:
            error_msg = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_msg)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


# ==================== Utility Endpoints ====================

@app.post("/api/validate-prompt", response_model=PromptValidationResponse)
async def validate_prompt(request: PromptValidationRequest):
    """Validate a system prompt."""
    parser = PromptParser()
    is_valid, error = parser.validate_prompt(request.raw_prompt)
    variables = parser.extract_variables(request.raw_prompt)
    
    return PromptValidationResponse(
        is_valid=is_valid,
        variables=variables,
        error_message=error
    )


@app.get("/api/prompt-template")
async def get_prompt_template():
    """Get the default agent prompt template."""
    return {"template": DEFAULT_AGENT_TEMPLATE}


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.app_env
    }


# ==================== Background Tasks ====================

async def process_document_task(document_id: int, file_path: str, file_type: str):
    """Background task to process uploaded documents."""
    from database import SessionLocal
    db = SessionLocal()
    
    try:
        engine_instance = ProfileEngine(db)
        await engine_instance.process_document(document_id, file_path, file_type)
    finally:
        db.close()


# ==================== Run Application ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development
    )
