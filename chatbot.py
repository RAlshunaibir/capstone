"""
Professional Qwen Chatbot Backend
A robust Flask-based chatbot using Groq API with advanced features
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from functools import wraps
import hashlib
import secrets
import re
from dotenv import load_dotenv

from flask import Flask, request, jsonify, render_template, session
from groq import Groq

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chatbot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, template_folder="templates")
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))

# In-memory storage for conversations (simple but effective)
conversation_store = {}

# Rate limiting (simple implementation)
request_counts = {}
RATE_LIMIT_PER_MINUTE = 10

# Configuration
@dataclass
class ChatConfig:
    """Configuration for the chatbot"""
    model: str = "qwen-qwq-32b"
    temperature: float = 0.7
    max_tokens: int = 512
    max_history: int = 10
    system_prompt: str = """You are a helpful, professional, and friendly AI assistant. 
    You provide accurate, helpful responses while maintaining a conversational tone. 
    Always be respectful and considerate in your interactions."""
    max_input_length: int = 1000
    request_timeout: int = 30

config = ChatConfig()

# Initialize Groq client
try:
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set")
    groq_client = Groq(api_key=groq_api_key)
    logger.info("Groq client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Groq client: {e}")
    groq_client = None

@dataclass
class Conversation:
    """Represents a conversation session"""
    session_id: str
    messages: List[Dict]
    created_at: datetime
    last_activity: datetime
    user_agent: str
    ip_address: str

    def to_dict(self) -> Dict:
        return {
            'session_id': self.session_id,
            'messages': self.messages,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'user_agent': self.user_agent,
            'ip_address': self.ip_address
        }

class ConversationManager:
    """Manages conversation sessions and history"""
    
    def __init__(self):
        self.store = conversation_store
    
    def get_conversation(self, session_id: str) -> Optional[Conversation]:
        """Retrieve conversation from storage"""
        try:
            return self.store.get(session_id)
        except Exception as e:
            logger.error(f"Error retrieving conversation: {e}")
        return None
    
    def save_conversation(self, conversation: Conversation):
        """Save conversation to storage"""
        try:
            self.store[conversation.session_id] = conversation
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
    
    def create_conversation(self, session_id: str, user_agent: str, ip_address: str) -> Conversation:
        """Create a new conversation"""
        now = datetime.now()
        conversation = Conversation(
            session_id=session_id,
            messages=[],
            created_at=now,
            last_activity=now,
            user_agent=user_agent,
            ip_address=ip_address
        )
        self.save_conversation(conversation)
        return conversation

conversation_manager = ConversationManager()

def get_client_ip():
    """Get client IP address"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    return request.remote_addr

def check_rate_limit(ip_address):
    """Simple rate limiting implementation"""
    current_time = time.time()
    minute_ago = current_time - 60
    
    # Clean old entries
    request_counts[ip_address] = [req_time for req_time in request_counts.get(ip_address, []) 
                                 if req_time > minute_ago]
    
    # Check if limit exceeded
    if len(request_counts[ip_address]) >= RATE_LIMIT_PER_MINUTE:
        return False
    
    # Add current request
    request_counts[ip_address].append(current_time)
    return True

def validate_input(text: str) -> Tuple[bool, str]:
    """Validate user input"""
    if not text or not text.strip():
        return False, "Message cannot be empty"
    
    if len(text.strip()) > config.max_input_length:
        return False, f"Message too long (max {config.max_input_length} characters)"
    
    # Basic content filtering
    inappropriate_words = ['spam', 'advertisement']  # Add more as needed
    if any(word in text.lower() for word in inappropriate_words):
        return False, "Message contains inappropriate content"
    
    return True, ""

def generate_session_id() -> str:
    """Generate a unique session ID"""
    return hashlib.sha256(f"{time.time()}{secrets.token_hex(8)}".encode()).hexdigest()[:16]

def log_request(func):
    """Decorator to log API requests"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        client_ip = get_client_ip()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"Request from {client_ip} to {func.__name__} completed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Request from {client_ip} to {func.__name__} failed after {duration:.2f}s: {e}")
            raise
    return wrapper

def clean_ai_response(response_text: str) -> str:
    """Clean AI response by removing thinking process and internal markers"""
    # Remove thinking process markers
    response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL)
    
    # Remove other common internal processing markers
    response_text = re.sub(r'<|>.*?</|>', '', response_text, flags=re.DOTALL)
    
    # Remove any leading/trailing whitespace
    response_text = response_text.strip()
    
    # If response is empty after cleaning, return a default message
    if not response_text:
        return "I apologize, but I couldn't generate a proper response. Please try asking your question again."
    
    return response_text

def generate_chat_response(user_msg: str, conversation: Conversation) -> Tuple[str, int]:
    """Generate response using Groq API with conversation history"""
    if not groq_client:
        return "Sorry, the AI service is currently unavailable.", 503
    
    try:
        # Prepare messages with history
        messages = [{"role": "system", "content": config.system_prompt}]
        
        # Add conversation history (limited to prevent token overflow)
        history_messages = conversation.messages[-config.max_history*2:]  # *2 because each exchange has 2 messages
        messages.extend(history_messages)
        
        # Add current user message
        messages.append({"role": "user", "content": user_msg})
        
        # Make API call
        response = groq_client.chat.completions.create(
            model=config.model,
            messages=messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )
        
        ai_response = response.choices[0].message.content
        
        # Clean the response to remove thinking process
        ai_response = clean_ai_response(ai_response)
        
        # Update conversation history
        conversation.messages.append({"role": "user", "content": user_msg})
        conversation.messages.append({"role": "assistant", "content": ai_response})
        conversation.last_activity = datetime.now()
        
        # Keep conversation history manageable
        if len(conversation.messages) > config.max_history * 2:
            conversation.messages = conversation.messages[-config.max_history * 2:]
        
        conversation_manager.save_conversation(conversation)
        
        return ai_response, 200
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return "I apologize, but I encountered an error processing your request. Please try again.", 500

@app.route("/")
def index():
    """Serve the main chat interface"""
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
@log_request
def chat():
    """Handle chat requests"""
    try:
        # Rate limiting
        client_ip = get_client_ip()
        if not check_rate_limit(client_ip):
            return jsonify({
                "error": "Rate limit exceeded. Please wait before sending more messages.",
                "retry_after": 60
            }), 429
        
        # Validate request
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "Message field is required"}), 400
        
        user_message = data["message"]
        
        # Input validation
        is_valid, error_msg = validate_input(user_message)
        if not is_valid:
            return jsonify({"error": error_msg}), 400
        
        # Get or create session
        if 'session_id' not in session:
            session['session_id'] = generate_session_id()
        
        conversation = conversation_manager.get_conversation(session['session_id'])
        if not conversation:
            conversation = conversation_manager.create_conversation(
                session['session_id'],
                request.headers.get('User-Agent', 'Unknown'),
                request.remote_addr
            )
        
        # Generate response
        response_text, status_code = generate_chat_response(user_message, conversation)
        
        if status_code == 200:
            return jsonify({
                "response": response_text,
                "session_id": session['session_id'],
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({"error": response_text}), status_code
            
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/health")
def health_check():
    """Health check endpoint"""
    try:
        # Test Groq connection
        if groq_client:
            # Simple test call
            test_response = groq_client.chat.completions.create(
                model=config.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            groq_status = "healthy"
        else:
            groq_status = "unavailable"
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "groq_api": groq_status,
            "active_conversations": len(conversation_store)
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 503

@app.route("/stats")
def get_stats():
    """Get basic statistics (admin endpoint)"""
    try:
        stats = {
            "active_conversations": len(conversation_store),
            "total_requests": sum(len(requests) for requests in request_counts.values()),
            "storage_type": "memory"
        }
        
        return jsonify({
            "stats": stats,
            "config": {
                "model": config.model,
                "max_tokens": config.max_tokens,
                "max_history": config.max_history,
                "rate_limit": RATE_LIMIT_PER_MINUTE
            },
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({"error": "Failed to retrieve statistics"}), 500

@app.route("/clear-session", methods=["POST"])
def clear_session():
    """Clear current session and conversation history"""
    try:
        if 'session_id' in session:
            session_id = session['session_id']
            if session_id in conversation_store:
                del conversation_store[session_id]
            session.pop('session_id', None)
            return jsonify({"message": "Session cleared successfully"})
        return jsonify({"message": "No active session to clear"})
    except Exception as e:
        logger.error(f"Error clearing session: {e}")
        return jsonify({"error": "Failed to clear session"}), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded"""
    return jsonify({
        "error": "Rate limit exceeded. Please wait before sending more messages.",
        "retry_after": 60
    }), 429

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {e}")
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404

if __name__ == "__main__":
    # Start the application
    port = int(os.getenv('PORT', 80))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting chatbot server on port {port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Model: {config.model}")
    logger.info(f"Rate limit: {RATE_LIMIT_PER_MINUTE} requests per minute")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
