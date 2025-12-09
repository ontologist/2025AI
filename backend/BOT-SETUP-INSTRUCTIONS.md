# AI-300 Bot Setup Instructions

This guide will help you set up the AI-300 Course Bot, a RAG-powered chatbot that uses Ollama, ChromaDB, and optional web search for AI topics.

## Prerequisites

- **Python 3.10+**
- **Ollama** with `llama3.2` model installed
- **Node.js 18+** (optional, for frontend development)

## Quick Start

### 1. Navigate to Backend Directory

```powershell
cd backend
```

### 2. Create Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 4. Ensure Ollama is Running

Make sure Ollama is running and has the required models:

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Pull required models if not already installed
ollama pull llama3.2
ollama pull nomic-embed-text
```

### 5. Copy Course Materials to Knowledge Base

```powershell
.\scripts\copy_knowledge_base.ps1
```

### 6. Load Knowledge Base into Vector Database

```powershell
python scripts/load_knowledge_base.py
```

### 7. Start the Backend Server

```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```

The API will be available at: `http://localhost:8003`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/health` | GET | Health check |
| `/api/chat` | POST | Chat with the bot |
| `/api/health` | GET | Bot service health |
| `/api/test` | GET | Test the bot |

### Chat Request Example

```json
POST /api/chat
{
    "user_id": "student123",
    "message": "What is artificial intelligence?",
    "language": "en",
    "conversation_history": [],
    "use_rag": true,
    "use_web_search": true
}
```

### Chat Response Example

```json
{
    "response": "Artificial intelligence (AI) is...",
    "user_id": "student123",
    "language": "en",
    "context_used": true,
    "web_search_used": false,
    "model": "llama3.2:latest"
}
```

## Configuration

Edit `backend/app/core/config.py` or create a `.env` file:

```env
# Course Configuration
COURSE_ID=ai300
COURSE_NAME=AI-300 Basic Artificial Intelligence

# Server Configuration
BACKEND_PORT=8003

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# RAG Configuration
CHROMA_DB_PATH=./chroma_db
KNOWLEDGE_BASE_PATH=./knowledge_base

# Web Search
WEB_SEARCH_ENABLED=true
WEB_SEARCH_MAX_RESULTS=3
```

## Features

### 1. RAG (Retrieval-Augmented Generation)
- Indexes all course materials (HTML, MD, YAML, etc.)
- Uses ChromaDB for vector storage
- Retrieves relevant context for each query

### 2. Web Search (AI Topics Only)
- Automatically searches the web when:
  - RAG context is insufficient
  - Query is related to AI/ML topics
- Uses DuckDuckGo for privacy-friendly search
- Only searches for AI-related keywords

### 3. Bilingual Support
- Responds in English or Japanese
- Controlled via `language` parameter

## Updating the Knowledge Base

When course materials change:

1. Run the copy script:
   ```powershell
   .\scripts\copy_knowledge_base.ps1
   ```

2. Re-index the documents:
   ```powershell
   python scripts/load_knowledge_base.py
   ```

## Troubleshooting

### Ollama Connection Error

```
Error: Ollama error: Connection refused
```

**Solution:** Start Ollama service:
```bash
ollama serve
```

### ChromaDB Permission Error

**Solution:** Delete the `chroma_db` folder and re-run ingestion:
```powershell
Remove-Item -Recurse -Force .\chroma_db
python scripts/load_knowledge_base.py
```

### No Documents Found

**Solution:** Ensure knowledge base has files:
```powershell
Get-ChildItem -Recurse .\knowledge_base | Measure-Object
```

If empty, run the copy script first.

## Production Deployment

For production with HTTPS (GitHub Pages):

1. Set up a Cloudflare Tunnel:
   ```bash
   cloudflared tunnel create ai300bot
   ```

2. Configure tunnel to point to `http://localhost:8003`

3. Update frontend `bot-chat.js`:
   - Set `bot_cloudflare_url` in localStorage, or
   - Update the default URL in `getApiUrl()`

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── chat.py          # Chat API endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py        # Configuration settings
│   ├── services/
│   │   ├── __init__.py
│   │   ├── bot_service.py   # Bot orchestration
│   │   ├── ollama_service.py # Ollama LLM client
│   │   ├── rag_service.py   # RAG with ChromaDB
│   │   └── web_search_service.py # DuckDuckGo search
│   ├── __init__.py
│   └── main.py              # FastAPI application
├── scripts/
│   ├── copy_knowledge_base.ps1  # Copy course files
│   └── load_knowledge_base.py   # Index to ChromaDB
├── knowledge_base/          # Indexed course materials
├── chroma_db/               # Vector database
├── logs/                    # Application logs
└── requirements.txt         # Python dependencies
```

## Port Assignment

| Course | Backend Port | Purpose |
|--------|--------------|---------|
| ML-101 | 8001 | Machine Learning course |
| HCI | 8002 | Human-Computer Interaction |
| AI-300 | 8003 | Basic AI course (this bot) |

---

For questions or issues, check the logs at `./logs/app.log`.

