# RAG Chatbot - Quick Start Guide

## 📦 What You Have

A complete RAG chatbot application with:
- **Backend**: Flask API with 10 endpoints
- **Frontend**: React app with 5 components
- **Features**: Website crawling, vector search, streaming chat, multi-bot support

## 🚀 Quick Start (3 Steps)

### Step 1: Get API Keys

1. **Google Gemini**: https://makersuite.google.com/app/apikey
2. **Pinecone**: https://www.pinecone.io/
   - Create index: dimension=768, metric=cosine

### Step 2: Configure

Edit `backend/.env`:
```env
GOOGLE_API_KEY=your_key_here
PINECONE_API_KEY=your_key_here
PINECONE_INDEX=your_index_name
```

### Step 3: Run

**Terminal 1 - Backend**:
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm install
npm run dev
```

**Open**: http://localhost:5173

## 📁 File Structure

```
RAG/
├── backend/          # Python Flask API
│   ├── app.py       # Main server
│   ├── rag.py       # RAG pipeline
│   ├── ingest.py    # Crawling
│   └── ...
├── frontend/         # React UI
│   └── src/
│       ├── App.jsx
│       └── components/
└── README.md         # Full docs
```

## 🎯 Usage

1. Click "Add New Bot"
2. Enter website URL
3. Wait for crawl to complete
4. Start chatting!

## 📚 Full Documentation

See [README.md](file:///c:/Users/hosan/Desktop/RAG/README.md) for complete documentation.
