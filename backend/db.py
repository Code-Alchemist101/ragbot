"""
MongoDB operations for RAG Chatbot Application
Handles chat history, bot profiles, and session management
"""
from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime, timedelta
import uuid
from logger import setup_logger
from config import MONGO_URI, DB_NAME, COLLECTION_CHAT_HISTORY, COLLECTION_BOTS, COLLECTION_SESSIONS

logger = setup_logger('db')

class DatabaseManager:
    """MongoDB database manager with connection pooling"""
    
    def __init__(self, uri=MONGO_URI, db_name=DB_NAME):
        """
        Initialize database connection
        
        Args:
            uri: MongoDB connection URI
            db_name: Database name
        """
        self.client = None
        self.db = None
        self.uri = uri
        self.db_name = db_name
        self._connect()
    
    def _connect(self, max_retries=3):
        """
        Establish database connection with retry logic
        
        Args:
            max_retries: Maximum number of connection attempts
        """
        for attempt in range(max_retries):
            try:
                self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
                self.db = self.client[self.db_name]
                
                # Test connection
                self.client.server_info()
                
                # Create indexes
                self._create_indexes()
                
                logger.info(f"Connected to MongoDB: {self.db_name}")
                return
            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
    
    def _create_indexes(self):
        """Create database indexes for performance"""
        try:
            # Chat history indexes
            self.db[COLLECTION_CHAT_HISTORY].create_index([('session_id', ASCENDING)])
            self.db[COLLECTION_CHAT_HISTORY].create_index([('bot_id', ASCENDING)])
            self.db[COLLECTION_CHAT_HISTORY].create_index([('timestamp', DESCENDING)])
            
            # Bot indexes
            self.db[COLLECTION_BOTS].create_index([('bot_id', ASCENDING)], unique=True)
            self.db[COLLECTION_BOTS].create_index([('namespace', ASCENDING)])
            
            # Session indexes
            self.db[COLLECTION_SESSIONS].create_index([('session_id', ASCENDING)], unique=True)
            self.db[COLLECTION_SESSIONS].create_index([('bot_id', ASCENDING)])
            
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
    
    def save_message(self, session_id, role, content, bot_id=None):
        """
        Save a chat message
        
        Args:
            session_id: Session identifier
            role: Message role ('user' or 'assistant')
            content: Message content
            bot_id: Optional bot identifier
        
        Returns:
            Inserted document ID
        """
        try:
            message = {
                'session_id': session_id,
                'role': role,
                'content': content,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if bot_id:
                message['bot_id'] = bot_id
            
            result = self.db[COLLECTION_CHAT_HISTORY].insert_one(message)
            logger.debug(f"Saved message for session {session_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            raise
    
    def get_history(self, session_id, limit=50):
        """
        Retrieve conversation history
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to retrieve
        
        Returns:
            List of message dictionaries
        """
        try:
            messages = list(
                self.db[COLLECTION_CHAT_HISTORY]
                .find({'session_id': session_id})
                .sort('timestamp', ASCENDING)
                .limit(limit)
            )
            
            # Remove MongoDB _id field
            for msg in messages:
                msg.pop('_id', None)
            
            logger.debug(f"Retrieved {len(messages)} messages for session {session_id}")
            return messages
        except Exception as e:
            logger.error(f"Error retrieving history: {e}")
            return []
    
    def create_bot(self, name, namespace, base_url):
        """
        Create a new bot profile
        
        Args:
            name: Bot name
            namespace: Pinecone namespace
            base_url: Website base URL
        
        Returns:
            Bot document
        """
        try:
            bot_id = str(uuid.uuid4())
            bot = {
                'bot_id': bot_id,
                'name': name,
                'namespace': namespace,
                'base_url': base_url,
                'created_at': datetime.utcnow().isoformat()
            }
            
            self.db[COLLECTION_BOTS].insert_one(bot)
            logger.info(f"Created bot: {name} ({bot_id})")
            
            bot.pop('_id', None)
            return bot
        except Exception as e:
            logger.error(f"Error creating bot: {e}")
            raise
    
    def get_bots(self):
        """
        Get all bot profiles
        
        Returns:
            List of bot documents
        """
        try:
            bots = list(self.db[COLLECTION_BOTS].find().sort('created_at', DESCENDING))
            
            # Remove MongoDB _id field
            for bot in bots:
                bot.pop('_id', None)
            
            logger.debug(f"Retrieved {len(bots)} bots")
            return bots
        except Exception as e:
            logger.error(f"Error retrieving bots: {e}")
            return []
    
    def get_bot(self, bot_id):
        """
        Get specific bot details
        
        Args:
            bot_id: Bot identifier
        
        Returns:
            Bot document or None
        """
        try:
            bot = self.db[COLLECTION_BOTS].find_one({'bot_id': bot_id})
            if bot:
                bot.pop('_id', None)
            return bot
        except Exception as e:
            logger.error(f"Error retrieving bot {bot_id}: {e}")
            return None
    
    def get_sessions_by_bot(self, bot_id):
        """
        Get all sessions for a specific bot
        
        Args:
            bot_id: Bot identifier
        
        Returns:
            List of unique session IDs
        """
        try:
            sessions = self.db[COLLECTION_CHAT_HISTORY].distinct('session_id', {'bot_id': bot_id})
            logger.debug(f"Retrieved {len(sessions)} sessions for bot {bot_id}")
            return sessions
        except Exception as e:
            logger.error(f"Error retrieving sessions: {e}")
            return []
    
    def update_session_activity(self, session_id, bot_id=None):
        """
        Update session last activity or create if not exists
        
        Args:
            session_id: Session identifier
            bot_id: Bot identifier (optional, but recommended for creation)
        """
        try:
            # Try to update existing session
            result = self.db[COLLECTION_SESSIONS].update_one(
                {'session_id': session_id},
                {'$set': {'last_activity': datetime.utcnow().isoformat()}}
            )
            
            # If not found (and bot_id provided), create new session
            if result.matched_count == 0 and bot_id:
                self.create_session(bot_id, session_id)
                
        except Exception as e:
            logger.error(f"Error updating session activity: {e}")
            # Don't raise, just log - session tracking shouldn't break chat

    def create_session(self, bot_id, session_id=None):
        """
        Create a new chat session
        
        Args:
            bot_id: Bot identifier
            session_id: Optional session ID (generates UUID if not provided)
        
        Returns:
            Session document
        """
        try:
            if not session_id:
                session_id = str(uuid.uuid4())
            
            session = {
                'session_id': session_id,
                'bot_id': bot_id,
                'created_at': datetime.utcnow().isoformat(),
                'last_activity': datetime.utcnow().isoformat()
            }
            
            self.db[COLLECTION_SESSIONS].insert_one(session)
            logger.info(f"Created session {session_id} for bot {bot_id}")
            
            session.pop('_id', None)
            return session
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise
    
    def delete_old_messages(self, days=30):
        """
        Delete messages older than specified days
        
        Args:
            days: Number of days to retain messages
        
        Returns:
            Number of deleted messages
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            result = self.db[COLLECTION_CHAT_HISTORY].delete_many({
                'timestamp': {'$lt': cutoff_date.isoformat()}
            })
            
            logger.info(f"Deleted {result.deleted_count} old messages")
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error deleting old messages: {e}")
            return 0
    
    def delete_bot(self, bot_id):
        """
        Delete a bot and all associated data
        
        Args:
            bot_id: Bot identifier
            
        Returns:
            Boolean indicating success
        """
        try:
            # Delete chat history
            self.db[COLLECTION_CHAT_HISTORY].delete_many({'bot_id': bot_id})
            
            # Delete sessions
            self.db[COLLECTION_SESSIONS].delete_many({'bot_id': bot_id})
            
            # Delete bot
            result = self.db[COLLECTION_BOTS].delete_one({'bot_id': bot_id})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted bot {bot_id} and associated data")
                return True
            else:
                logger.warning(f"Bot {bot_id} not found for deletion")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting bot: {e}")
            raise

    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")

# Global database instance
db = DatabaseManager()
