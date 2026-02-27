# 🤖 Job Search AI Assistant

An AI-powered job search assistant built with FastAPI, React, and Claude AI. This application helps you find jobs, generate cover letters, tailor resumes, and track applications.

## 🚀 Features

### Phase 1 - Foundation ✅ COMPLETE
- ✅ Chat-based interface
- ✅ FastAPI backend
- ✅ React frontend
- ✅ Docker containerization

### Phase 2 - Job Search ✅ COMPLETE
- ✅ Adzuna API integration
- ✅ Real-time job search
- ✅ Job filtering by title and location
- ✅ Beautiful job cards with details

### Phase 3 - RAG + AI (Coming Soon)
- 🔄 Document storage (resume, portfolio)
- 🔄 Claude AI integration
- 🔄 Cover letter generation
- 🔄 Resume tailoring

### Phase 4 - Application Tracking (Coming Soon)
- 🔄 Track applications
- 🔄 Application status dashboard

## 📋 Prerequisites

- **Docker Desktop** - [Download for Mac](https://www.docker.com/products/docker-desktop/)
- **Git** (optional, for version control)
- **VS Code** (recommended) with Docker extension

## 🛠️ Quick Start

### 1. Set Up Adzuna API (Required for Job Search)

Before starting the app, you need Adzuna API credentials:

1. Sign up at https://developer.adzuna.com/signup (free, no credit card)
2. Get your `app_id` and `app_key` from the dashboard
3. Create `.env` file in the `backend/` folder:
   ```bash
   cd backend
   cp .env.example .env
   ```
4. Edit `.env` and add your credentials:
   ```
   ADZUNA_APP_ID=your_app_id_here
   ADZUNA_APP_KEY=your_app_key_here
   ```

**See [ADZUNA_SETUP.md](ADZUNA_SETUP.md) for detailed instructions.**

### 2. Start the Application

```bash
# Navigate to the project directory
cd job-search-ai

# Start all services (first time will take 5-10 minutes to build)
docker-compose up --build

# Or run in background (detached mode)
docker-compose up -d --build
```

### 3. Access the Application

- **Frontend (React)**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 4. Stop the Application

```bash
# Stop all containers
docker-compose down

# Stop and remove all data (including database)
docker-compose down -v
```

## 📁 Project Structure

```
job-search-ai/
├── docker-compose.yml          # Orchestrates all containers
├── backend/
│   ├── Dockerfile             # Python/FastAPI container
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example          # Environment variables template
│   └── app/
│       ├── __init__.py
│       └── main.py           # FastAPI application
├── frontend/
│   ├── Dockerfile            # React container
│   ├── package.json          # Node dependencies
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── App.js           # Main React component
│       ├── App.css
│       ├── index.js
│       └── index.css
├── database/                 # SQLite database (auto-created)
└── README.md
```

## 🔧 Development Workflow

### Making Changes

1. **Edit code** on your MacBook using any editor (VS Code recommended)
2. **Save the file** - Docker will auto-reload
3. **Refresh browser** to see changes

### Useful Docker Commands

```bash
# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart a service
docker-compose restart backend

# Rebuild after changing dependencies
docker-compose up --build

# Access backend container shell
docker-compose exec backend /bin/bash

# Access frontend container shell
docker-compose exec frontend /bin/sh
```

### Installing New Dependencies

**Backend (Python):**
```bash
# Add package to backend/requirements.txt
# Then rebuild
docker-compose up --build backend
```

**Frontend (Node):**
```bash
# Add package to frontend/package.json dependencies
# Then rebuild
docker-compose up --build frontend
```

## 🧪 Testing the API

### Using the Browser
Visit http://localhost:8000/docs for interactive API documentation (Swagger UI)

### Using curl
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test chat endpoint
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'

# Test job search
curl http://localhost:8000/api/jobs?query=python
```

## 📝 Adzuna API Setup

**Phase 2 is now complete!** The app searches real jobs using Adzuna.

See [ADZUNA_SETUP.md](ADZUNA_SETUP.md) for:
- How to add your API credentials
- Testing your integration
- Troubleshooting common issues

You get 1,000 free API calls per month - plenty for development!

## 🤖 Phase 3 Setup (Claude AI)

For Phase 3 RAG and AI features:

1. Get Anthropic API key from https://console.anthropic.com/
2. Add to `backend/.env`:
   ```
   ANTHROPIC_API_KEY=your_key_here
   ```
3. Restart backend: `docker-compose restart backend`

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Find and kill process using port 3000 or 8000
lsof -ti:3000 | xargs kill -9
lsof -ti:8000 | xargs kill -9
```

### Docker Build Fails
```bash
# Clean everything and rebuild
docker-compose down -v
docker system prune -a
docker-compose up --build
```

### Frontend Can't Connect to Backend
- Make sure both containers are running: `docker-compose ps`
- Check backend logs: `docker-compose logs backend`
- Verify CORS settings in `backend/app/main.py`

### Changes Not Appearing
- Check if file is mounted correctly (see volumes in docker-compose.yml)
- Try restarting: `docker-compose restart`
- Hard refresh browser: Cmd+Shift+R (Mac)

## 📚 Learning Resources

- **FastAPI**: https://fastapi.tiangolo.com/
- **React**: https://react.dev/
- **Docker**: https://docs.docker.com/
- **Anthropic Claude**: https://docs.anthropic.com/

## 🎯 Next Steps

1. ✅ Get the app running with `docker-compose up`
2. ✅ Add your Adzuna API credentials (see [ADZUNA_SETUP.md](ADZUNA_SETUP.md))
3. ✅ Try searching for jobs at http://localhost:3000
4. ✅ Explore the API docs at http://localhost:8000/docs
5. 📖 Start learning FastAPI and React basics
6. 🔨 Get ready for Phase 3 - RAG and AI integration!

## 📄 License

This is a personal portfolio project. Feel free to use as inspiration for your own projects!

## 💡 Tips

- **Keep Docker Desktop running** while developing
- **Use VS Code** with Docker extension for easier container management
- **Check logs frequently** when things don't work as expected
- **Commit to Git regularly** to track your progress
- **Don't expose your .env file** - it contains sensitive API keys

---

**Happy coding! 🚀** Questions? Check the logs first, then Google/ChatGPT for specific errors.
