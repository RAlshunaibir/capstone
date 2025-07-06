# 🐳 Docker Setup Guide

## Overview

This application is fully containerized using Docker and Docker Compose. The setup includes:

- **Frontend**: React app served by Nginx
- **Backend**: FastAPI application
- **Database**: PostgreSQL with persistent storage

## 🏗 Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Frontend  │    │   Backend   │    │  Database   │
│   (Nginx)   │◄──►│  (FastAPI)  │◄──►│ (PostgreSQL)│
│   Port 80   │    │  Port 8000  │    │  Port 5432  │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker
- Docker Compose
- `.env` file with required environment variables

### Environment Variables
Create a `.env` file in the root directory:

```env
GROQ_API_KEY=your_groq_api_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here
```

### Start the Application
```bash
# Build and start all services
docker compose up --build -d

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

## 📁 File Structure

```
app/
├── docker-compose.yml          # Main orchestration file
├── .env                        # Environment variables
├── backend/
│   ├── Dockerfile             # Backend container definition
│   ├── app.py                 # FastAPI application
│   ├── database.py            # Database models
│   └── requirements.txt       # Python dependencies
└── frontend/
    ├── Dockerfile             # Frontend container definition
    ├── nginx.conf             # Nginx configuration
    ├── src/                   # React source code
    └── package.json           # Node.js dependencies
```

## 🔧 Service Details

### Frontend (React + Nginx)
- **Port**: 80
- **URL**: http://localhost
- **Features**:
  - Multi-stage build for optimization
  - Nginx for static file serving
  - API proxy to backend
  - Gzip compression
  - React Router support

### Backend (FastAPI)
- **Port**: 8000
- **URL**: http://localhost:8000
- **Features**:
  - Python 3.11 with FastAPI
  - JWT authentication
  - Database integration
  - Rate limiting

### Database (PostgreSQL)
- **Port**: 5432
- **Database**: chatbot_db
- **User**: chatbot_user
- **Features**:
  - Persistent data storage
  - Automatic backups via volumes
  - Optimized for production

## 🔄 Container Communication

### Internal Network
- Frontend → Backend: `http://app:8000`
- Backend → Database: `postgresql://chatbot_user:chatbot_password@postgres:5432/chatbot_db`

### External Access
- Frontend: `http://localhost`
- Backend API: `http://localhost:8000`
- Database: `localhost:5432`

## 🛠 Development Commands

```bash
# Start development environment
docker compose up -d

# View specific service logs
docker compose logs frontend
docker compose logs app
docker compose logs postgres

# Rebuild specific service
docker compose build frontend
docker compose build app

# Access container shell
docker compose exec app bash
docker compose exec postgres psql -U chatbot_user -d chatbot_db

# Stop and remove everything
docker compose down -v
```

## 📊 Monitoring

### Check Service Status
```bash
docker compose ps
```

### View Resource Usage
```bash
docker stats
```

### Database Connection
```bash
# Connect with DBeaver or any PostgreSQL client
Host: localhost
Port: 5432
Database: chatbot_db
Username: chatbot_user
Password: chatbot_password
```

## 🔒 Security Considerations

1. **Environment Variables**: Never commit `.env` files
2. **Database Passwords**: Use strong passwords in production
3. **API Keys**: Store sensitive keys in environment variables
4. **Network**: Services communicate via internal Docker network
5. **Volumes**: Data persists across container restarts

## 🚀 Production Deployment

### Environment Variables
```env
GROQ_API_KEY=your_production_groq_key
JWT_SECRET_KEY=your_secure_jwt_secret
DATABASE_URL=postgresql://user:pass@host:5432/db
```

### Security Checklist
- [ ] Change default passwords
- [ ] Use HTTPS in production
- [ ] Set up proper SSL certificates
- [ ] Configure firewall rules
- [ ] Set up database backups
- [ ] Use production-grade PostgreSQL

## 🐛 Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check what's using the ports
   lsof -i :80
   lsof -i :8000
   lsof -i :5432
   ```

2. **Database Connection Issues**
   ```bash
   # Check database logs
   docker compose logs postgres
   
   # Test database connection
   docker compose exec postgres psql -U chatbot_user -d chatbot_db
   ```

3. **Frontend Not Loading**
   ```bash
   # Check frontend logs
   docker compose logs frontend
   
   # Rebuild frontend
   docker compose build frontend
   ```

4. **Backend API Errors**
   ```bash
   # Check backend logs
   docker compose logs app
   
   # Test API directly
   curl http://localhost:8000/
   ```

## 📈 Scaling

### Horizontal Scaling
```bash
# Scale backend services
docker compose up -d --scale app=3
```

### Load Balancing
- Use Nginx or Traefik for load balancing
- Configure sticky sessions for chat functionality
- Set up health checks

## 🔄 Updates

### Update Application
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker compose down
docker compose up --build -d
```

### Database Migrations
```bash
# Run database migrations
docker compose exec app python init_db.py
```

---

## 🎯 Key Benefits

✅ **Isolation**: Each service runs in its own container  
✅ **Consistency**: Same environment across development and production  
✅ **Scalability**: Easy to scale individual services  
✅ **Persistence**: Data survives container restarts  
✅ **Security**: Isolated network and file systems  
✅ **Portability**: Runs anywhere Docker is available  

Your application is now fully containerized and ready for deployment! 🚀 