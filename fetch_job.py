from fastapi import FastAPI
import requests
import sqlite3

app = FastAPI()

FEED_URL = "https://www.arbeitnow.com/api/job-board-api"

MY_SKILLS = [
    "python", "fastapi", "react", "postgresql", 
    "sql", "javascript", "tailwind", "git", "jwt", "rest api"
]

def init_db():
    """Initialize the SQLite database and create the jobs table."""
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            company TEXT,
            location TEXT,
            url TEXT UNIQUE,
            remote TEXT
        )
    """)
    conn.commit()
    conn.close()

# Run database initialization when the app starts
init_db()

@app.post("/sync")
def sync_jobs():
    """Endpoint 1: Fetches external jobs, cleans them, and saves to SQLite."""
    response = requests.get(FEED_URL)
    data = response.json()
    
    # Handle different possible JSON response structures safely
    if isinstance(data, dict):
        raw_jobs = data.get("data", [])
    elif isinstance(data, list):
        raw_jobs = data
    else:
        raw_jobs = []
    
    # Extract essential fields into cleaned_jobs list
    cleaned_jobs = []
    for job in raw_jobs:
        if isinstance(job, dict):
            clean_job = {
                "title": job.get("title"),
                "company": job.get("company_name"),
                "location": job.get("location"),
                "url": job.get("url"),
                "remote": str(job.get("remote"))
            }
            cleaned_jobs.append(clean_job)
        
    # Save Cleaned Jobs into the Database (with duplicate protection)
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    
    for job in cleaned_jobs:
        cursor.execute("""
            INSERT OR IGNORE INTO jobs (title, company, location, url, remote)
            VALUES (?, ?, ?, ?, ?)
        """, (
            job["title"],
            job["company"],
            job["location"],
            job["url"],
            job["remote"]
        ))
        
    conn.commit()
    conn.close()
    
    return {
        "status": "success",
        "message": f"Successfully synced and checked {len(cleaned_jobs)} jobs into database."
    }

@app.get("/jobs")
def get_saved_jobs():
    """Endpoint 2: Reads saved jobs directly from SQLite instantly without internet."""
    conn = sqlite3.connect("jobs.db")
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    cursor = conn.cursor()
    
    cursor.execute("SELECT title, company, location, url, remote FROM jobs")
    rows = cursor.fetchall()
    conn.close()
    
    # Convert sqlite3 rows to a list of dictionaries
    jobs_list = [dict(row) for row in rows]
    
    return {
        "status": "success",
        "total_saved_jobs": len(jobs_list),
        "jobs": jobs_list
    }