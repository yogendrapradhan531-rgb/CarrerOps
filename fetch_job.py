from fastapi import FastAPI
import requests
import sqlite3

app = FastAPI()

FEED_URL = "https://www.arbeitnow.com/api/job-board-api"

# 1. Define Your Master Skill List
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

# 2. Create the Scoring Function with Bonus & Penalty Rules
def calculate_score(title: str) -> int:
    """
    Calculates a deterministic match score (0% to 100%) based on skills,
    plus a junior bonus or senior penalty.
    """
    if not title:
        return 0
        
    lower_title = title.lower()
    
    # Base skill matching score
    matches = 0
    for skill in MY_SKILLS:
        if skill in lower_title:
            matches += 1
            
    base_score = (matches / len(MY_SKILLS)) * 100
    
    # Define Junior keywords for bonus
    junior_keywords = ["fresher", "junior", "intern", "associate", "entry"]
    # Define Senior keywords for penalty
    senior_keywords = ["senior", "lead", "staff", "architect", "5+ years", "director", "head"]
    
    # Apply Junior Bonus (+20%)
    for word in junior_keywords:
        if word in lower_title:
            base_score += 20
            break
            
    # Apply Senior Penalty (-50% or cut in half)
    for word in senior_keywords:
        if word in lower_title:
            base_score = base_score * 0.5
            break
            
    # Ensure score stays between 0 and 100
    final_score = max(0, min(int(base_score), 100))
    return final_score

@app.post("/sync")
def sync_jobs():
    """Fetches external jobs, cleans them, and saves to SQLite."""
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
    """Reads saved jobs from SQLite, calculates match scores with rules, and sorts them."""
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
    
    jobs_list = []
    for row in rows:
        title = row[1]
        score = calculate_score(title)
        
        job_dict = {
            "id": row[0],
            "title": title,
            "company": row[2],
            "location": row[3],
            "url": row[4],
            "remote": row[5],
            "match_score": f"{score}%"
        }
        jobs_list.append(job_dict)
        
    # Sort from highest match score to lowest
    jobs_list = sorted(jobs_list, key=lambda x: int(x["match_score"].replace("%", "")), reverse=True)
    
    return {
        "status": "success",
        "keyword_filter": keyword,
        "total_matches": len(jobs_list),
        "jobs": jobs_list
    }