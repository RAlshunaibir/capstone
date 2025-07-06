#!/usr/bin/env python3
"""
Database initialization script
Run this to create all database tables
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text

# Load environment variables
load_dotenv()

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import create_tables, engine

def init_database():
    """Initialize the database by creating all tables"""
    try:
        print("🔄 Creating database tables...")
        create_tables()
        print("✅ Database tables created successfully!")
        
        # Test database connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"📊 Connected to PostgreSQL: {version}")
            
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        print("\n💡 Make sure PostgreSQL is running and accessible.")
        print("   If using Docker: docker-compose up postgres")
        sys.exit(1)

if __name__ == "__main__":
    init_database() 