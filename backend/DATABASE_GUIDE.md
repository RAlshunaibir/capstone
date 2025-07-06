# 🗄️ Database Guide for Beginners

## 📚 **What is PostgreSQL?**

**PostgreSQL** is like a super-powered Excel spreadsheet that can handle millions of rows of data.

### **Simple Analogy:**
- **Excel Spreadsheet** = One table with data
- **PostgreSQL** = Multiple spreadsheets (tables) that can talk to each other

### **Our Database Structure:**
```
📁 Chatbot Database
├── 📋 Users Table (like a contact list)
│   ├── ID (unique number)
│   ├── Username
│   ├── Email
│   └── Password (hashed)
│
├── 📋 Conversations Table (like chat sessions)
│   ├── ID (unique number)
│   ├── Session ID
│   ├── User ID (links to Users table)
│   └── Timestamps
│
└── 📋 Messages Table (like individual texts)
    ├── ID (unique number)
    ├── Conversation ID (links to Conversations table)
    ├── Role (user or assistant)
    ├── Content (the actual message)
    └── Timestamp
```

## 🐳 **What is Docker Compose?**

**Docker Compose** is like a recipe that tells your computer how to start multiple applications together.

### **What our recipe does:**
1. **Start PostgreSQL** (the database)
2. **Start FastAPI** (your chatbot app)
3. **Connect them together**

## 🚀 **How to Use**

### **Step 1: Start Everything**
```bash
# Start PostgreSQL and your app
docker-compose up -d
```

### **Step 2: Initialize Database**
```bash
# Create the tables
python init_db.py
```

### **Step 3: Check Everything Works**
```bash
# Visit your app
http://localhost:8000
```

## 🔍 **Understanding the Files**

### **`docker-compose.yml`**
- **Recipe file** that tells Docker what to run
- **postgres service**: Starts PostgreSQL database
- **app service**: Starts your FastAPI application
- **volumes**: Keeps your data safe (like a backup)

### **`database.py`**
- **Table definitions** (like creating spreadsheets)
- **User table**: Stores user accounts
- **Conversation table**: Stores chat sessions
- **Message table**: Stores individual messages

### **`init_db.py`**
- **Setup script** that creates all the tables
- Run this once to prepare your database

## 📊 **Database Tables Explained**

### **Users Table**
```sql
-- Like a contact list
CREATE TABLE users (
    id SERIAL PRIMARY KEY,           -- Unique number for each user
    username VARCHAR(50) UNIQUE,     -- Username (must be unique)
    email VARCHAR(100) UNIQUE,       -- Email (must be unique)
    hashed_password VARCHAR(255),    -- Encrypted password
    created_at TIMESTAMP,            -- When account was created
    is_active BOOLEAN                -- Is account active?
);
```

### **Conversations Table**
```sql
-- Like chat sessions
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,           -- Unique number for each conversation
    session_id VARCHAR(50) UNIQUE,   -- Session identifier
    user_id INTEGER,                 -- Links to Users table
    created_at TIMESTAMP,            -- When conversation started
    last_activity TIMESTAMP          -- Last message time
);
```

### **Messages Table**
```sql
-- Like individual text messages
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,           -- Unique number for each message
    conversation_id INTEGER,         -- Links to Conversations table
    role VARCHAR(20),                -- 'user' or 'assistant'
    content TEXT,                    -- The actual message
    timestamp TIMESTAMP              -- When message was sent
);
```

## 🔗 **Relationships (How Tables Connect)**

```
User (1) ←→ (Many) Conversations
Conversation (1) ←→ (Many) Messages
```

**Example:**
- **User "Alice"** has **3 conversations**
- **Conversation #1** has **10 messages**
- **Conversation #2** has **5 messages**
- **Conversation #3** has **15 messages**

## 🛠 **Common Commands**

### **Start Services**
```bash
# Start everything
docker-compose up -d

# Start only database
docker-compose up postgres -d

# Start only app
docker-compose up app -d
```

### **Stop Services**
```bash
# Stop everything
docker-compose down

# Stop and remove data (WARNING: deletes all data!)
docker-compose down -v
```

### **View Logs**
```bash
# See all logs
docker-compose logs

# See database logs
docker-compose logs postgres

# See app logs
docker-compose logs app
```

### **Database Operations**
```bash
# Connect to database
docker-compose exec postgres psql -U chatbot_user -d chatbot_db

# Initialize database tables
python init_db.py
```

## 🔧 **Troubleshooting**

### **Database Connection Error**
```bash
# Check if PostgreSQL is running
docker-compose ps

# Restart PostgreSQL
docker-compose restart postgres
```

### **Port Already in Use**
```bash
# Check what's using port 5432
lsof -i :5432

# Change port in docker-compose.yml
ports:
  - "5433:5432"  # Use port 5433 instead
```

### **Data Persistence**
- **Data is saved** in Docker volumes
- **Data survives** container restarts
- **Data is lost** only if you run `docker-compose down -v`

## 📈 **Next Steps**

1. **Learn SQL**: Basic SELECT, INSERT, UPDATE, DELETE
2. **Database Tools**: Install DBeaver or pgAdmin
3. **Backup**: Learn how to backup your data
4. **Performance**: Learn about indexes and optimization

## 🎯 **Key Concepts Summary**

- **PostgreSQL** = Database (stores data)
- **Docker Compose** = Recipe (runs multiple apps)
- **Tables** = Spreadsheets (organize data)
- **Relationships** = Links between tables
- **Volumes** = Persistent storage (keeps data safe) 