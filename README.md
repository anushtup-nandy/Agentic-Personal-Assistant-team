# Multi-Agent Decision Support System

A beautiful, minimalistic web application that learns about you through documents and creates customizable AI agents for collaborative decision-making.

## Features

✨ **Profile Learning** - Upload documents to build a comprehensive user profile  
🤖 **Custom AI Agents** - Create agents with unique personas using YAML/XML prompts  
💬 **Multi-Agent Debates** - Watch agents discuss and help you make decisions  
🎨 **Beautiful UI** - Dark mode, glassmorphism, smooth animations  
🔌 **Dual AI Support** - Gemini AI Studio + Ollama integration  

## Quick Start

### Prerequisites

- Node.js 18+ / Python 3.10+
- Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
- Ollama (optional, for local models)

### Backend Setup

```bash
# Navigate to backend
cd backend

# Install dependencies (using conda env 'cofounder')
conda activate cofounder
pip install -r requirements.txt

# Configure environment
cp ../.env.example ../.env
# Edit .env and add your GEMINI_API_KEY

# Run the server
python app.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The app will be available at `http://localhost:5173`

## Usage

### 1. Create Your Profile
- Enter your name and email
- Upload documents (resume, portfolio, etc.)
- Let the AI generate your profile summary

### 2. Create AI Agents
- Design custom agent personas
- Define behavior using YAML/XML prompts
- Choose between Gemini or Ollama models
- Set temperature and other parameters

### 3. Start a Debate
- Select 2+ agents to participate
- Enter your decision topic
- Watch agents discuss in real-time
- Export the conversation

## Project Structure

```
AgenticAssisstants/
├── backend/                 # FastAPI backend
│   ├── app.py              # Main application
│   ├── models.py           # Database models
│   ├── schemas.py          # Pydantic schemas
│   ├── database.py         # DB configuration
│   ├── config.py           # Settings
│   └── services/           # Business logic
│       ├── llm_clients.py       # Gemini & Ollama
│       ├── prompt_parser.py     # YAML/XML parser
│       ├── profile_engine.py    # Document processing
│       └── agent_orchestrator.py # Multi-agent debates
│
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # UI components
│   │   ├── api.js         # API client
│   │   ├── App.jsx        # Main app
│   │   └── index.css      # Design system
│   ├── package.json
│   └── vite.config.js
│
└── .env.example           # Environment template
```

## Technologies

**Backend:**
- FastAPI - Modern async Python framework
- LangGraph + LangChain - Multi-agent orchestration
- ChromaDB - Vector embeddings
- SQLAlchemy - Database ORM
- Google Gemini API
- Ollama API

**Frontend:**
- React 18 - UI library
- Vite - Build tool
- React Router - Navigation
- Monaco Editor - Code editing
- Axios - HTTP client

## API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google AI Studio API key | Yes |
| `OLLAMA_BASE_URL` | Ollama server URL | No |
| `DATABASE_URL` | Database connection string | No |
| `CHROMA_PERSIST_DIRECTORY` | Vector store path | No |

## Example Agent Prompt

```yaml
agent:
  name: "Strategic Advisor"
  role: "long-term thinker"
  model_preference: "gemini"
  
  system_prompt: |
    <persona>
      You are a strategic advisor who thinks long-term.
      You consider second-order effects and future implications.
    </persona>
    
    <context>
      User Profile: {{user_profile_summary}}
      Decision: {{decision_topic}}
    </context>
    
    <behavior>
      - Think 5-10 years ahead
      - Consider ripple effects
      - Ask about sustainability
      - Challenge short-term thinking
    </behavior>
    
    <constraints>
      - Keep responses under 200 words
      - Focus on {{user_expertise_areas}}
      - Match {{user_risk_tolerance}} risk tolerance
    </constraints>

  temperature: 0.7
  max_tokens: 500
```

## Contributing

This is a personal project, but suggestions and feedback are welcome!

## License

MIT

## Acknowledgments

Built with ❤️ using Google's Gemini API, LangChain, and modern web technologies.
