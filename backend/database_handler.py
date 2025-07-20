from database import User, Conversation, Message, get_db
from sqlalchemy.orm import Session
from datetime import datetime

class DatabaseHandler:
    def __init__(self, db: Session):
        self.db = db

    def get_user(self, username):
        return self.db.query(User).filter(User.username == username).first()

    def get_conversation(self, session_id, user_id=None):
        q = self.db.query(Conversation).filter(Conversation.session_id == session_id)
        if user_id is not None:
            q = q.filter(Conversation.user_id == user_id)
        return q.first()

    def get_user_conversations(self, user_id):
        return self.db.query(Conversation).filter(Conversation.user_id == user_id).all()

    def create_conversation(self, session_id, user_id):
        conversation = Conversation(
            session_id=session_id,
            user_id=user_id,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def save_message(self, conversation_id, role, content):
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            timestamp=datetime.utcnow()
        )
        self.db.add(message)
        self.db.commit()
        return message

    def get_conversation_messages(self, conversation_id):
        return self.db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.timestamp).all()

    def update_conversation_activity(self, conversation):
        conversation.last_activity = datetime.utcnow()
        self.db.commit()

    def delete_conversation(self, conversation):
        self.db.delete(conversation)
        self.db.commit() 