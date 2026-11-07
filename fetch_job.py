from fastapi import FastAPI
import requests
import sqlite3

app = FastAPI()

FEED_URL = "https://www.arbeitnow.com/api/job-board-api"

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
    
    if isinstance(data, dict):
        raw_jobs = data.get("data", [])
    elif isinstance(data, list):
        raw_jobs = data
    else:
        raw_jobs = []
    
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
def get_saved_jobs(keyword: str = None):
    """Endpoint 2: Reads saved jobs from SQLite and converts raw tuples into clean dictionaries."""
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    
    if keyword:
        cursor.execute("""
            SELECT id, title, company, location, url, remote 
            FROM jobs 
            WHERE title LIKE ?
        """, (f"%{keyword}%",))
    else:
        cursor.execute("SELECT id, title, company, location, url, remote FROM jobs")
        
    rows = cursor.fetchall()
    conn.close()
    
    # 3. Convert each tuple row into a clean dictionary
    jobs_list = []
    for row in rows:
        job_dict = {
            "id": row[0],
            "title": row[1],
            "company": row[2],
            "location": row[3],
            "url": row[4],
            "remote": row[5]
        }
        jobs_list.append(job_dict)
    
    return {
        "status": "success",
        "keyword_filter": keyword,
        "total_matches": len(jobs_list),
        "jobs": jobs_list
    }