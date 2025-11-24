# RAG Chatbot Application

A production-ready, full-stack RAG (Retrieval-Augmented Generation) chatbot application that crawls entire websites, processes content into semantic chunks, stores embeddings in a vector database, and provides an intelligent chat interface with conversation history and multi-bot management.

## 🌟 Features

- **Website Crawling**: Async crawling with 20+ concurrent requests
- **Smart Indexing**: Automatic deduplication, chunking, and vector storage
- **RAG Pipeline**: History-aware retrieval using LangChain LCEL
- **Multi-Bot Support**: Manage multiple chatbots for different websites
- **Streaming Responses**: Real-time SSE streaming for chat responses
- **Conversation History**: Persistent chat history with MongoDB
- **Modern UI**: Glassmorphism design with smooth animations
- **Real-Time Progress**: Live crawl progress updates

## 🏗️ Architecture

### Backend (Python)
- **Framework**: Flask with CORS
- **LLM**: Google Gemini (gemini-1.5-flash-latest)
- **Embeddings**: HuggingFace sentence-transformers/all-mpnet-base-v2
- **Vector DB**: Pinecone with namespace isolation
- **Database**: MongoDB for chat history and bot profiles
- **Crawling**: Custom async crawler with aiohttp

### Frontend (React)
- **Framework**: React 18 with Vite
- **Styling**: Modern CSS with glassmorphism
- **State**: React hooks
- **HTTP**: Fetch API with SSE streaming

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB (local or Atlas)
- Google Gemini API key
- Pinecone account with index (dimension: 768, metric: cosine)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
cd RAG
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### 3. Configure Environment Variables

Edit `backend/.env`:

```env
# Required
GOOGLE_API_KEY=your_google_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX=your_pinecone_index_name

# Optional (defaults provided)
MONGO_URI=mongodb://localhost:27017/
FLASK_PORT=5000
```

### 4. Get API Keys

**Google Gemini API**:
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create API key
3. Add to `.env` as `GOOGLE_API_KEY`

**Pinecone**:
1. Create account at [Pinecone](https://www.pinecone.io/)
2. Create index with:
   - Dimension: **768** (critical - must match embedding model)
   - Metric: **cosine**
3. Get API key and index name
4. Add to `.env`

**MongoDB**:
- Local: Install MongoDB Community Edition
- Cloud: Use [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)

### 5. Start Backend

```bash
cd backend
python app.py
```

Backend will run on `http://localhost:5000`

### 6. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will run on `http://localhost:5173`

## 📖 Usage

### Creating a Bot

1. Open `http://localhost:5173`
2. Click "Add New Bot"
3. Enter website URL (e.g., `https://example.com`)
4. Select crawl depth (2 recommended)
5. Click "Start Crawling"
6. Wait for crawl to complete (progress shown in real-time)
7. Bot will be created automatically

### Chatting with a Bot

1. Click on a bot card in the dashboard
2. Start a new conversation or select existing session
3. Type your question
4. Receive streaming AI responses based on website content

## 🔧 API Endpoints

### Chat
- `POST /api/chat` - Non-streaming chat
- `POST /api/chat/stream` - SSE streaming chat
- `GET /api/history/:session_id` - Get conversation history

### Crawling
- `POST /api/crawl` - Start website crawl
- `GET /api/crawl/stream/:crawl_id` - SSE crawl progress
- `GET /api/crawl/status/:crawl_id` - Get crawl status

### Bot Management
- `POST /api/bots` - Create bot
- `GET /api/bots` - List all bots
- `GET /api/bots/:bot_id` - Get bot details
- `GET /api/bots/:bot_id/sessions` - List bot sessions

## 📁 Project Structure

```
RAG/
├── backend/
│   ├── app.py              # Flask API server
│   ├── rag.py              # RAG pipeline with LCEL
│   ├── ingest.py           # Website indexing pipeline
│   ├── async_crawler.py    # Async content extraction
│   ├── url_discovery.py    # Fast URL discovery
│   ├── db.py               # MongoDB operations
│   ├── config.py           # Configuration management
│   ├── logger.py           # Logging setup
│   ├── requirements.txt    # Python dependencies
│   └── .env.example        # Environment template
├── frontend/
│   ├── src/
│   │   ├── App.jsx         # Main application
│   │   ├── App.css         # Global styles
│   │   ├── main.jsx        # React entry point
│   │   └── components/
│   │       ├── BotDashboard.jsx
│   │       ├── Onboarding.jsx
│   │       ├── ChatInterface.jsx
│   │       └── ChatWidget.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
└── README.md
```

## ⚙️ Configuration

### Crawling Settings

```env
MAX_CONCURRENCY=30        # Concurrent requests
MAX_URLS=100000          # Maximum URLs to crawl
CRAWL_TIMEOUT=15         # Request timeout (seconds)
```

### Chunking Settings

```env
CHUNK_SIZE=500           # Characters per chunk
CHUNK_OVERLAP=100        # Overlap between chunks
```

### RAG Settings

```env
LLM_MODEL=models/gemini-2.0-flash
LLM_TEMPERATURE=0.3
RETRIEVAL_TOP_K=10       # Number of chunks to retrieve
```

## 🧪 Testing

### Test Backend API

```bash
# Test crawl
curl -X POST http://localhost:5000/api/crawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "depth": 2}'

# Test chat
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this about?", "session_id": "test-123"}'

# List bots
curl http://localhost:5000/api/bots
```

### Test Frontend

1. Navigate to `http://localhost:5173`
2. Create a test bot
3. Verify crawl progress updates
4. Test chat functionality
5. Check conversation history persistence

## 🔒 Security Notes

- Never commit `.env` file
- Use environment variables for all secrets
- Enable CORS only for trusted origins in production
- Implement rate limiting for production deployment
- Validate all user inputs

## 🚀 Production Deployment

### Backend

1. Use production WSGI server (Gunicorn/uWSGI)
2. Set `FLASK_DEBUG=False`
3. Configure MongoDB replica set
4. Use Pinecone production tier
5. Implement request queuing for crawls
6. Add monitoring and logging

### Frontend

```bash
cd frontend
npm run build
# Deploy dist/ folder to hosting service
```

## 📊 Performance

- **Crawl Speed**: 20+ concurrent requests
- **Chat Response**: < 1s to first token
- **Embedding Model**: 768-dimensional vectors
- **Batch Processing**: 50 documents per batch

## 🐛 Troubleshooting

### Pinecone Dimension Error
- Ensure Pinecone index dimension is **768**
- Verify `EMBEDDING_MODEL` is `sentence-transformers/all-mpnet-base-v2`

### MongoDB Connection Failed
- Check MongoDB is running: `mongod --version`
- Verify `MONGO_URI` in `.env`

### Crawl Fails
- Check URL is accessible
- Verify internet connection
- Check crawl timeout settings

### Chat Not Streaming
- Ensure backend is running
- Check browser console for errors
- Verify SSE connection in Network tab

## 📝 License

MIT License - feel free to use for personal or commercial projects

## 🤝 Contributing

Contributions welcome! Please open issues or submit PRs.

## 📧 Support

For issues or questions, please open a GitHub issue.

---

Built with ❤️ using LangChain, Google Gemini, Pinecone, and React
