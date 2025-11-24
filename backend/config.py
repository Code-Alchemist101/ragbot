"""
Configuration management for RAG Chatbot Application
Loads environment variables and defines application constants
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_INDEX = os.getenv('PINECONE_INDEX')
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')

# Validate required environment variables
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is required")
if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY environment variable is required")
if not PINECONE_INDEX:
    raise ValueError("PINECONE_INDEX environment variable is required")

# Crawling Configuration
MAX_CONCURRENCY = int(os.getenv('MAX_CONCURRENCY', '30'))
MAX_URLS = int(os.getenv('MAX_URLS', '100000'))
CRAWL_TIMEOUT = int(os.getenv('CRAWL_TIMEOUT', '15'))

# Chunking Configuration
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '500'))
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '100'))

# Embedding Configuration
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-mpnet-base-v2')
EMBEDDING_DIMENSION = 768  # Fixed for all-mpnet-base-v2

# LLM Configuration
LLM_MODEL = os.getenv('LLM_MODEL', 'gemini-1.5-flash-latest')
LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.3'))

# RAG Configuration
RETRIEVAL_TOP_K = int(os.getenv('RETRIEVAL_TOP_K', '10'))

# Batch Processing
INGESTION_BATCH_SIZE = int(os.getenv('INGESTION_BATCH_SIZE', '50'))

# MongoDB Configuration
DB_NAME = os.getenv('DB_NAME', 'klbot_chat')
COLLECTION_CHAT_HISTORY = os.getenv('COLLECTION_CHAT_HISTORY', 'chat_history')
COLLECTION_BOTS = os.getenv('COLLECTION_BOTS', 'bots')
COLLECTION_SESSIONS = os.getenv('COLLECTION_SESSIONS', 'sessions')

# Flask Configuration
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
