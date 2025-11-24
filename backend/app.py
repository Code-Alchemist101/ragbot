"""
Flask API Server for RAG Chatbot Application
Provides REST endpoints for chat, crawling, and bot management
"""
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import uuid
import threading
import time
from datetime import datetime
from rag import get_answer, get_answer_stream
from ingest import ingest_website
from db import db
from logger import setup_logger
from config import FLASK_DEBUG, FLASK_PORT

logger = setup_logger('app')

app = Flask(__name__)
CORS(app)

# In-memory storage for crawl status
crawl_status = {}
crawl_status_lock = threading.Lock()

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Non-streaming chat endpoint
    
    Request body:
        {
            "question": "User question",
            "session_id": "Session UUID",
            "bot_id": "Bot UUID" (optional)
        }
    
    Returns:
        {
            "answer": "Generated response"
        }
    """
    try:
        data = request.json
        question = data.get('question')
        session_id = data.get('session_id')
        bot_id = data.get('bot_id')
        
        if not question or not session_id:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Get bot details for namespace
        namespace = None
        if bot_id:
            bot = db.get_bot(bot_id)
            if bot:
                namespace = bot.get('namespace')
        
        # Get chat history
        history = db.get_history(session_id)
        
        # Save user message
        db.save_message(session_id, 'user', question, bot_id)
        
        # Get answer
        answer = get_answer(question, namespace=namespace, chat_history=history)
        
        # Save assistant message
        db.save_message(session_id, 'assistant', answer, bot_id)
        
        return jsonify({'answer': answer})
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """
    Streaming chat endpoint using Server-Sent Events
    
    Request body: Same as /api/chat
    
    Returns:
        SSE stream with answer chunks
    """
    try:
        data = request.json
        question = data.get('question')
        session_id = data.get('session_id')
        bot_id = data.get('bot_id')
        
        if not question or not session_id:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Get bot details for namespace
        namespace = None
        if bot_id:
            bot = db.get_bot(bot_id)
            if bot:
                namespace = bot.get('namespace')
        
        # Get chat history
        history = db.get_history(session_id)
        
        # Save user message
        db.save_message(session_id, 'user', question, bot_id)
        
        def generate():
            """Generate SSE stream"""
            full_answer = ""
            try:
                for chunk in get_answer_stream(question, namespace=namespace, chat_history=history):
                    full_answer += chunk
                    yield f"data: {chunk}\n\n"
                
                # Send completion signal
                yield "data: [DONE]\n\n"
                
                # Save complete answer
                db.save_message(session_id, 'assistant', full_answer, bot_id)
            
            except Exception as e:
                logger.error(f"Error in streaming: {e}", exc_info=True)
                yield f"data: [ERROR] {str(e)}\n\n"
        
        return Response(generate(), mimetype='text/event-stream')
    
    except Exception as e:
        logger.error(f"Error in chat stream endpoint: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/<session_id>', methods=['GET'])
def get_history(session_id):
    """
    Get conversation history for a session
    
    Returns:
        {
            "history": [
                {"role": "user", "content": "...", "timestamp": "..."},
                ...
            ]
        }
    """
    try:
        history = db.get_history(session_id)
        return jsonify({'history': history})
    
    except Exception as e:
        logger.error(f"Error getting history: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/crawl', methods=['POST'])
def start_crawl():
    """
    Start website crawling
    
    Request body:
        {
            "url": "https://example.com",
            "depth": 2 (optional)
        }
    
    Returns:
        {
            "crawl_id": "UUID",
            "message": "Crawl started"
        }
    """
    try:
        data = request.json
        url = data.get('url')
        depth = data.get('depth', 2)
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Generate crawl ID
        crawl_id = str(uuid.uuid4())
        
        # Initialize status
        with crawl_status_lock:
            crawl_status[crawl_id] = {
                'status': 'running',
                'stage': 'initializing',
                'progress': {},
                'result': None,
                'error': None,
                'started_at': datetime.utcnow().isoformat()
            }
        
        # Start crawl in background thread
        def run_crawl():
            def status_callback(update):
                with crawl_status_lock:
                    if crawl_id in crawl_status:
                        crawl_status[crawl_id]['progress'].update(update)
                        if 'stage' in update:
                            crawl_status[crawl_id]['stage'] = update['stage']
            
            try:
                result = ingest_website(url, depth=depth, status_callback=status_callback)
                
                with crawl_status_lock:
                    if crawl_id in crawl_status:
                        crawl_status[crawl_id]['status'] = 'completed'
                        crawl_status[crawl_id]['result'] = result
                        crawl_status[crawl_id]['completed_at'] = datetime.utcnow().isoformat()
            
            except Exception as e:
                logger.error(f"Crawl {crawl_id} failed: {e}", exc_info=True)
                with crawl_status_lock:
                    if crawl_id in crawl_status:
                        crawl_status[crawl_id]['status'] = 'failed'
                        crawl_status[crawl_id]['error'] = str(e)
        
        thread = threading.Thread(target=run_crawl)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'crawl_id': crawl_id,
            'message': 'Crawl started'
        })
    
    except Exception as e:
        logger.error(f"Error starting crawl: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/crawl/stream/<crawl_id>', methods=['GET'])
def crawl_stream(crawl_id):
    """
    Stream crawl progress updates
    
    Returns:
        SSE stream with progress updates
    """
    def generate():
        """Generate SSE stream for crawl progress"""
        last_stage = None
        
        while True:
            with crawl_status_lock:
                if crawl_id not in crawl_status:
                    yield f"data: {{'error': 'Crawl not found'}}\n\n"
                    break
                
                status = crawl_status[crawl_id]
                current_stage = status.get('stage')
                
                # Send update if stage changed or status completed/failed
                if current_stage != last_stage or status['status'] in ['completed', 'failed']:
                    import json
                    update = {
                        'status': status['status'],
                        'stage': current_stage,
                        'progress': status.get('progress', {})
                    }
                    
                    if status['status'] == 'completed':
                        update['result'] = status.get('result')
                    elif status['status'] == 'failed':
                        update['error'] = status.get('error')
                    
                    yield f"data: {json.dumps(update)}\n\n"
                    last_stage = current_stage
                
                # Break if completed or failed
                if status['status'] in ['completed', 'failed']:
                    break
            
            time.sleep(1)
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/crawl/status/<crawl_id>', methods=['GET'])
def get_crawl_status(crawl_id):
    """
    Get current crawl status
    
    Returns:
        {
            "status": "running|completed|failed",
            "progress": {...},
            "result": {...}
        }
    """
    try:
        with crawl_status_lock:
            if crawl_id not in crawl_status:
                return jsonify({'error': 'Crawl not found'}), 404
            
            return jsonify(crawl_status[crawl_id])
    
    except Exception as e:
        logger.error(f"Error getting crawl status: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/bots', methods=['POST'])
def create_bot():
    """
    Create a new bot
    
    Request body:
        {
            "name": "Bot Name",
            "namespace": "domain_com",
            "base_url": "https://example.com"
        }
    
    Returns:
        Bot document
    """
    try:
        data = request.json
        name = data.get('name')
        namespace = data.get('namespace')
        base_url = data.get('base_url')
        
        if not all([name, namespace, base_url]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        bot = db.create_bot(name, namespace, base_url)
        return jsonify(bot)
    
    except Exception as e:
        logger.error(f"Error creating bot: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/bots', methods=['GET'])
def list_bots():
    """
    List all bots
    
    Returns:
        {
            "bots": [...]
        }
    """
    try:
        bots = db.get_bots()
        return jsonify({'bots': bots})
    
    except Exception as e:
        logger.error(f"Error listing bots: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/bots/<bot_id>', methods=['GET'])
def get_bot(bot_id):
    """
    Get bot details
    
    Returns:
        Bot document
    """
    try:
        bot = db.get_bot(bot_id)
        if not bot:
            return jsonify({'error': 'Bot not found'}), 404
        
        return jsonify(bot)
    
    except Exception as e:
        logger.error(f"Error getting bot: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/bots/<bot_id>/sessions', methods=['GET'])
def get_bot_sessions(bot_id):
    """
    Get all sessions for a bot
    
    Returns:
        {
            "sessions": ["session_id1", "session_id2", ...]
        }
    """
    try:
        sessions = db.get_sessions_by_bot(bot_id)
        return jsonify({'sessions': sessions})
    
    except Exception as e:
        logger.error(f"Error getting bot sessions: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    logger.info(f"Starting Flask server on port {FLASK_PORT}")
    app.run(debug=FLASK_DEBUG, port=FLASK_PORT, threaded=True)
