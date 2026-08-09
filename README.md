# AI ChatGPT Clone

A production-oriented ChatGPT clone built with a React + Vite frontend and a FastAPI backend. The application supports authenticated chat, persistent user memory, conversation threads, streaming assistant responses, internal tool routing, feedback collection, and background answer evaluation.

## Features

- User registration and login with JWT authentication
- Protected frontend chat route
- ChatGPT-style chat interface with sidebar conversation history
- New chat creation and isolated conversation threads
- Streaming assistant responses
- Persistent user memory for personal information such as name, role, company, skills, and preferences
- Calculator tool for math requests
- Tavily-powered live search tool for current information
- Feedback buttons for assistant responses
- Background evaluation saved internally in the database
- SQLite persistence for users, memory, conversations, messages, feedback, and evaluations

## Architecture Diagram

```text
React Frontend
  |
  v
FastAPI Backend
  |
  v
JWT Auth + Protected APIs
  |
  v
Chat Pipeline
  |
  +--> Personal Information Analyzer
  |      |
  |      v
  |   User Memory System
  |
  +--> Current Conversation History
  |
  +--> Tool Router
  |      |
  |      +--> Calculator Tool
  |      |
  |      +--> Tavily Search Tool
  |
  v
LLM Response Generation
  |
  v
Streaming Response to Frontend
  |
  v
SQLite Database
  |
  +--> users
  +--> user_memory
  +--> conversations
  +--> messages
  +--> feedback
  +--> evaluations
```

## Technology Stack

- Frontend: React 18, Vite 5, Tailwind CSS, React Router DOM, Axios
- Backend: FastAPI, SQLAlchemy async ORM, SQLite, Pydantic, Uvicorn
- Authentication: JWT bearer tokens, hashed passwords
- AI: OpenRouter-compatible LLM API
- Tools: Calculator, Tavily live search
- Storage: SQLite

## Installation

### Backend

```bash
cd ChatGPT-Clone/backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000`.

### Frontend

```bash
cd ChatGPT-Clone/frontend
npm install
npm run dev
```

Frontend runs at the Vite dev server URL shown in the terminal.

## Environment Variables

### Backend

Create `backend/.env` from `backend/.env.example`.

```env
APP_NAME=ChatGPT Clone Backend
APP_DESCRIPTION=Production-ready FastAPI foundation for the ChatGPT Clone backend.
APP_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=false
API_PREFIX=/api
ALLOWED_ORIGINS=https://your-frontend-domain.com
SQLITE_DATABASE_URL=sqlite:///./chatgpt_clone.db
SECRET_KEY=replace-with-a-strong-secret
JWT_ALGORITHM=HS256
OPENROUTER_API_KEY=your-openrouter-api-key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-oss-20b
TAVILY_API_KEY=your-tavily-api-key
```

### Frontend

Create `frontend/.env` from `frontend/.env.example`.

```env
VITE_API_URL=https://your-backend-domain.com/api/v1
```

## API Endpoints

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for request and response details.

Main endpoint groups:

- Authentication: `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/me`
- Chat: `/api/v1/chat`, `/api/v1/new-chat`
- Conversations: `/api/conversations/`
- Feedback: `/api/v1/feedback/`
- Health: `/health`, `/api/v1/health`

## Deployment Steps

### Backend

1. Set production environment variables.
2. Install dependencies from `backend/requirements.txt`.
3. Start the FastAPI app with Uvicorn or the platform's ASGI runner.
4. Confirm `/health` returns `status: healthy`.
5. Confirm `ALLOWED_ORIGINS` includes the deployed frontend URL.

### Frontend

1. Set `VITE_API_URL` to the deployed backend API base URL.
2. Run `npm install`.
3. Run `npm run build`.
4. Deploy `frontend/dist`.
5. Verify register, login, chat streaming, tools, and feedback from the deployed URL.

## Production Verification

The final verification notes and demo plan are documented in:

- [FINAL_TESTING_REPORT.md](FINAL_TESTING_REPORT.md)
- [DEMO_SCRIPT.md](DEMO_SCRIPT.md)
