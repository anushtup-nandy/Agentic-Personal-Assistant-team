# Multi-Agent Decision Support System - Backend

Production-grade backend for an AI-powered multi-agent decision support system.

## Features

- 🤖 **Multi-Agent Orchestration**: LangGraph-powered agent debates
- 🧠 **Profile Learning**: Extract and learn from user documents
- 🔌 **Dual AI Integration**: Gemini AI Studio + Ollama support
- 📝 **Custom System Prompts**: YAML/XML format with variable substitution
- 💾 **Vector Storage**: Semantic search with ChromaDB
- 🚀 **FastAPI**: Modern async API with streaming support

## Setup

### Prerequisites

- Python 3.10+
- Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- Ollama installed locally (optional)

### Installation

1. **Install dependencies**:
```bash
cd backend
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
cp ../.env.example ../.env
# Edit .env and add your API keys
```

3. **Initialize database**:
```bash
python -c "from database import init_db; init_db()"
```

4. **Run the server**:
```bash
python app.py
# Or with uvicorn:
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Architecture

```
backend/
├── app.py                 # FastAPI application
├── config.py              # Configuration management
├── database.py            # Database setup
├── models.py              # SQLAlchemy models
├── schemas.py             # Pydantic schemas
└── services/
    ├── llm_clients.py     # Gemini & Ollama clients
    ├── prompt_parser.py   # YAML/XML parser
    ├── profile_engine.py  # Document processing
    └── agent_orchestrator.py  # Multi-agent debates
```

## Key Endpoints

### User Profiles
- `POST /api/profiles` - Create user profile
- `GET /api/profiles/{id}` - Get profile
- `POST /api/profiles/{id}/documents` - Upload document
- `POST /api/profiles/{id}/generate-summary` - Generate profile summary

### Agents
- `POST /api/profiles/{id}/agents` - Create agent
- `GET /api/profiles/{id}/agents` - List agents
- `PATCH /api/agents/{id}` - Update agent
- `DELETE /api/agents/{id}` - Delete agent

### Debates
- `POST /api/profiles/{id}/debates` - Create debate session
- `POST /api/debates/{id}/start` - Start debate (SSE streaming)
- `GET /api/debates/{id}` - Get debate with messages

### Utilities
- `POST /api/validate-prompt` - Validate system prompt
- `GET /api/prompt-template` - Get default template
- `GET /api/health` - Health check

## Agent System Prompt Format

```yaml
agent:
  name: "Critical Thinker"
  role: "devil's advocate"
  model_preference: "gemini"
  
  system_prompt: |
    <persona>
      You are a critical thinker who challenges assumptions.
    </persona>
    
    <context>
      User Profile: {{user_profile_summary}}
      Decision: {{decision_topic}}
    </context>
    
    <behavior>
      - Question assumptions
      - Provide counterarguments
      - Be respectful but direct
    </behavior>

  temperature: 0.8
  max_tokens: 500
```

## Development

### Running Tests
```bash
pytest tests/ -v
```

### Database Migrations
```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google AI Studio API key | Required |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |
| `DATABASE_URL` | Database connection string | `sqlite:///./agent_assistant.db` |
| `CHROMA_PERSIST_DIRECTORY` | Vector store path | `./data/chroma` |

## License

MIT
