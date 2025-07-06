# app.py
# This is a FastAPI application for a chatbot using Groq API
# You can modify this file to change the chatbot behavior
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from groq import Groq
import os
import re
import bcrypt
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Dict, Optional, List
import time
import hashlib
import secrets
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Import database models and session
from database import get_db, User, Conversation, Message

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Set up templates
templates = Jinja2Templates(directory="templates")

# Set Groq API key from environment variable
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY environment variable is not set")

client = Groq(api_key=groq_api_key)

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Database storage is now used instead of in-memory storage

# Rate limiting
request_counts: Dict[str, List[float]] = {}
RATE_LIMIT_PER_MINUTE = 10

# Chat configuration
CHAT_CONFIG = {
    "model": "qwen-qwq-32b",
    "temperature": 0.7,
    "max_tokens": 512,
    "max_history": 10,
    "system_prompt": "You are a helpful, professional, and friendly AI assistant. You provide accurate, helpful responses while maintaining a conversational tone. Always be respectful and considerate in your interactions.",
    "max_input_length": 1000
}

# Security
security = HTTPBearer()

# Pydantic models
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: str

class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: List[Dict[str, str]]
    created_at: str
    last_activity: str
    message_count: int

class UserSignup(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    username: str

class TokenData(BaseModel):
    username: Optional[str] = None

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[str]:
    """Verify JWT token and return username"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except jwt.PyJWTError:
        return None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current user from JWT token"""
    token = credentials.credentials
    username = verify_token(token)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def generate_session_id() -> str:
    """Generate a unique session ID"""
    return hashlib.sha256(f"{time.time()}{secrets.token_hex(8)}".encode()).hexdigest()[:16]

def check_rate_limit(ip_address: str) -> bool:
    """Simple rate limiting implementation"""
    current_time = time.time()
    minute_ago = current_time - 60
    
    # Clean old entries
    if ip_address in request_counts:
        request_counts[ip_address] = [req_time for req_time in request_counts[ip_address] 
                                     if req_time > minute_ago]
    
    # Check if limit exceeded
    if len(request_counts.get(ip_address, [])) >= RATE_LIMIT_PER_MINUTE:
        return False
    
    # Add current request
    if ip_address not in request_counts:
        request_counts[ip_address] = []
    request_counts[ip_address].append(current_time)
    return True

def validate_input(text: str) -> tuple[bool, str]:
    """Validate user input"""
    if not text or not text.strip():
        return False, "Message cannot be empty"
    
    if len(text.strip()) > CHAT_CONFIG["max_input_length"]:
        return False, f"Message too long (max {CHAT_CONFIG['max_input_length']} characters)"
    
    # Basic content filtering
    inappropriate_words = ['spam', 'advertisement']  # Add more as needed
    if any(word in text.lower() for word in inappropriate_words):
        return False, "Message contains inappropriate content"
    
    return True, ""

def clean_response(text):
    """Remove thinking process from AI response"""
    # Remove <think>...</think> blocks
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    
    # Remove other thinking markers like <|>...</|>
    text = re.sub(r'<\|>.*?</\|>', '', text, flags=re.DOTALL)
    
    # Remove any text that starts with "Okay," and ends before the actual response
    text = re.sub(r'Okay,.*?(?=\n\n|\n[A-Z]|$)', '', text, flags=re.DOTALL)
    
    return text.strip()

def generate_chat_response(user_msg: str, session_id: str, username: str) -> str:
    """Generate a response using Groq API"""
    try:
        # Prepare the message for the API
        messages = [
            {"role": "system", "content": CHAT_CONFIG["system_prompt"]},
            {"role": "user", "content": user_msg}
        ]
        
        # Call Groq API
        response = client.chat.completions.create(
            model=CHAT_CONFIG["model"],
            messages=messages,
            temperature=CHAT_CONFIG["temperature"],
            max_tokens=CHAT_CONFIG["max_tokens"]
        )
        
        # Extract and clean the response
        response_text = response.choices[0].message.content
        cleaned_response = clean_response(response_text)
        
        return cleaned_response
        
    except Exception as e:
        print(f"Error generating response: {e}")
        return "I apologize, but I'm having trouble processing your request right now. Please try again later."

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Chatbot API is running"}

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup", response_model=Token)
async def signup(user_data: UserSignup, db: Session = Depends(get_db)):
    """Register a new user and return JWT token"""
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash the password
    hashed_password = hash_password(user_data.password)
    
    # Create new user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )
    
    # Save to database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_data.username}, expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        username=user_data.username
    )

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate a user and return JWT token"""
    # Get user from database
    user = db.query(User).filter(User.username == user_data.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Verify password
    if not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_data.username}, expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        username=user_data.username
    )

@app.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest, request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Chat endpoint that requires authentication"""
    # Rate limiting
    client_ip = request.client.host
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please wait before sending more messages."
        )
    
    # Input validation
    is_valid, error_msg = validate_input(chat_request.message)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Generate session ID for conversation tracking
    session_id = generate_session_id()
    
    # Generate response with username
    response_text = generate_chat_response(chat_request.message, session_id, username=current_user.username)
    
    # Create or get conversation in database
    conversation = db.query(Conversation).filter(Conversation.session_id == session_id).first()
    if not conversation:
        conversation = Conversation(
            session_id=session_id,
            user_id=current_user.id,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    
    # Add user message to database
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=chat_request.message,
        timestamp=datetime.utcnow()
    )
    db.add(user_message)
    
    # Add bot response to database
    bot_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=response_text,
        timestamp=datetime.utcnow()
    )
    db.add(bot_message)
    
    # Update conversation last activity
    conversation.last_activity = datetime.utcnow()
    
    db.commit()
    
    return ChatResponse(
        response=response_text,
        session_id=session_id,
        timestamp=datetime.now().isoformat()
    )

@app.get("/chat/history", response_model=List[ChatHistoryResponse])
async def get_chat_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get chat history for the current user"""
    # Get user's conversations from database
    conversations = db.query(Conversation).filter(Conversation.user_id == current_user.id).all()
    
    chat_history = []
    for conversation in conversations:
        # Get messages for this conversation
        messages = db.query(Message).filter(Message.conversation_id == conversation.id).order_by(Message.timestamp).all()
        
        # Convert messages to the expected format
        message_list = []
        for msg in messages:
            message_list.append({
                "role": msg.role,
                "content": msg.content
            })
        
        chat_history.append(ChatHistoryResponse(
            session_id=conversation.session_id,
            messages=message_list,
            created_at=conversation.created_at.isoformat(),
            last_activity=conversation.last_activity.isoformat(),
            message_count=len(message_list)
        ))
    
    # Sort by last activity (most recent first)
    chat_history.sort(key=lambda x: x.last_activity, reverse=True)
    
    return chat_history

@app.get("/chat/history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history_by_session(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get chat history for a specific session"""
    # Get conversation from database
    conversation = db.query(Conversation).filter(
        Conversation.session_id == session_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Get messages for this conversation
    messages = db.query(Message).filter(Message.conversation_id == conversation.id).order_by(Message.timestamp).all()
    
    # Convert messages to the expected format
    message_list = []
    for msg in messages:
        message_list.append({
            "role": msg.role,
            "content": msg.content
        })
    
    return ChatHistoryResponse(
        session_id=session_id,
        messages=message_list,
        created_at=conversation.created_at.isoformat(),
        last_activity=conversation.last_activity.isoformat(),
        message_count=len(message_list)
    )

@app.delete("/chat/history/{session_id}")
async def delete_chat_history(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete chat history for a specific session"""
    # Get conversation from database
    conversation = db.query(Conversation).filter(
        Conversation.session_id == session_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Delete conversation (messages will be deleted automatically due to cascade)
    db.delete(conversation)
    db.commit()
    
    return {"message": "Chat history deleted successfully"}

@app.get("/users")
async def list_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """List all users (for debugging, remove in production)"""
    users = db.query(User).all()
    return {"users": [user.username for user in users]}

@app.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "username": current_user.username,
        "email": current_user.email
    }

@app.post("/refresh")
async def refresh_token(current_user: User = Depends(get_current_user)):
    """Refresh JWT token"""
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user.username}, expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        username=current_user.username
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)
