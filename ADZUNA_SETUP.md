# 🔑 Setting Up Adzuna API

Your project now has **real job search** functionality powered by Adzuna!

## Step 1: Add Your API Credentials

1. **Copy the example environment file:**
   ```bash
   cd job-search-ai/backend
   cp .env.example .env
   ```

2. **Edit the `.env` file** and add your Adzuna credentials:
   ```
   ADZUNA_APP_ID=your_actual_app_id_here
   ADZUNA_APP_KEY=your_actual_app_key_here
   ```

3. **Save the file**

## Step 2: Restart Docker

If your containers are already running, restart them to pick up the new environment variables:

```bash
docker-compose restart backend
```

Or restart everything:
```bash
docker-compose down
docker-compose up
```

## Step 3: Test It Out!

1. **Open the app:** http://localhost:3000

2. **Try these searches:**
   - "Find Python developer jobs in Toronto"
   - "Find Software Engineer jobs in Vancouver"
   - "Find Data Scientist jobs in Ontario"

3. **Or click the quick search buttons** on the welcome screen!

## What Changed?

✅ **Real Adzuna Integration**
- Backend now fetches real jobs from Adzuna API
- Supports search by job title and location
- Returns up to 10 results per search

✅ **Enhanced Frontend**
- Job cards show company, location, salary, and description
- Click "View Job" to see the full posting
- Quick search buttons for easy testing

✅ **Smart Parsing**
- Automatically extracts job title and location from your queries
- Works with natural language like "Find X jobs in Y"

## Troubleshooting

**"Adzuna API credentials not configured" error:**
- Make sure you created the `.env` file in the `backend/` folder
- Make sure you added both `ADZUNA_APP_ID` and `ADZUNA_APP_KEY`
- Restart the backend: `docker-compose restart backend`

**No jobs found:**
- Try broader search terms (e.g., "developer" instead of "senior python developer")
- Try different locations (e.g., "Ontario" instead of a specific city)
- Check that your Adzuna API credentials are valid

**API not responding:**
- Check Adzuna dashboard: https://developer.adzuna.com/
- You get 1,000 free API calls per month
- Make sure you haven't exceeded the limit

## Next Steps

Now that Phase 2 is working, you can:

1. ✅ Test different job searches
2. 📖 Learn how the code works (check `backend/app/adzuna_service.py`)
3. 🎨 Customize the UI (edit `frontend/src/App.js` and `App.css`)
4. 🔨 Prepare for Phase 3 - RAG and AI integration!

---

**Enjoy your real job search system! 🎉**
