# 🚀 QUICK START GUIDE

## Get Up and Running in 10 Minutes!

### Step 1: Get Adzuna API Credentials (5 minutes)
1. Go to https://developer.adzuna.com/signup
2. Sign up (free, no credit card needed)
3. Log in and find your `app_id` and `app_key` on the dashboard
4. Keep these handy - you'll need them in Step 3!

### Step 2: Install Docker Desktop
1. Download Docker Desktop for Mac: https://www.docker.com/products/docker-desktop/
2. Install and start Docker Desktop
3. Make sure Docker is running (you'll see the whale icon in your menu bar)

### Step 3: Set Up Your Project
1. Download the `job-search-ai` folder to your MacBook
2. Open Terminal
3. Navigate to the folder:
   ```bash
   cd ~/Downloads/job-search-ai
   ```
4. Create your `.env` file with Adzuna credentials:
   ```bash
   cd backend
   cp .env.example .env
   ```
5. Edit the `.env` file (use TextEdit or any editor):
   - Replace `your_app_id_here` with your actual Adzuna app_id
   - Replace `your_app_key_here` with your actual Adzuna app_key
   - Save the file
6. Go back to the project root:
   ```bash
   cd ..
   ```

### Step 4: Start Everything
Run this single command:
```bash
docker-compose up --build
```

**What to expect:**
- First time will take 5-10 minutes (downloading and building containers)
- You'll see lots of logs - this is normal!
- Wait until you see: "Application startup complete"

### Step 5: Open Your Browser
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs

### Step 6: Try It Out!
Click one of the quick search buttons or type:
- "Find Python developer jobs in Toronto"
- "Find Software Engineer jobs in Vancouver"

You should see real job results from Adzuna! 🎉

---

## Common Issues & Fixes

### "Port already in use"
Something else is using port 3000 or 8000.
```bash
# Kill the process
lsof -ti:3000 | xargs kill -9
lsof -ti:8000 | xargs kill -9
```

### "Docker daemon not running"
Start Docker Desktop app from Applications folder.

### Want to stop everything?
Press `Ctrl + C` in Terminal, then run:
```bash
docker-compose down
```

---

## Daily Development Workflow

**Start working:**
```bash
cd job-search-ai
docker-compose up
```

**Make changes:**
1. Edit files in VS Code (or any editor)
2. Save
3. Refresh browser - changes appear automatically!

**Stop working:**
```bash
# Press Ctrl + C
docker-compose down
```

---

## What's Included?

✅ **Backend API** (FastAPI + Python)
- Runs on http://localhost:8000
- Auto-reloads when you change code
- **Real Adzuna job search integration**
- Sample endpoints for chat

✅ **Frontend UI** (React)
- Runs on http://localhost:3000
- Beautiful chat interface with job cards
- Auto-reloads when you change code
- Quick search buttons

✅ **Real Job Data** (Adzuna)
- 1,000 free API calls per month
- Search by job title and location
- Real-time results from Canada job market

✅ **Database** (PostgreSQL + SQLite)
- Runs automatically in the background
- Ready for Phase 3 when you need it

---

## Next Steps

1. ✅ Get it running (you're here!)
2. ✅ Try different job searches
3. 📖 Read the full README.md and ADZUNA_SETUP.md
4. 🎓 Learn FastAPI basics: https://fastapi.tiangolo.com/tutorial/
5. 🎓 Learn React basics: https://react.dev/learn
6. 🔨 Get ready for Phase 3 - RAG and AI integration!

---

## Need Help?

1. **Check the logs**: They usually tell you what's wrong
2. **Google the error**: Copy/paste error messages
3. **Read the full README.md**: More detailed troubleshooting there

**You got this! 🚀**
