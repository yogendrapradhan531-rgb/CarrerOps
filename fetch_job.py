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

def calculate_score_and_skills(title: str):
    """
    Calculates score (0-100%) with bonus/penalties and 
    returns BOTH the final score and the list of matched skills.
    """
    if not title:
        return 0, []
        
    lower_title = title.lower()
    
    # Track which specific skills were found
    matched_skills = []
    for skill in MY_SKILLS:
        if skill in lower_title:
            matched_skills.append(skill)
            
    base_score = (len(matched_skills) / len(MY_SKILLS)) * 100
    
    # Junior Bonus & Senior Penalty Rules
    junior_keywords = ["fresher", "junior", "intern", "associate", "entry"]
    senior_keywords = ["senior", "lead", "staff", "architect", "5+ years", "director", "head"]
    
    for word in junior_keywords:
        if word in lower_title:
            base_score += 20
            break
            
    for word in senior_keywords:
        if word in lower_title:
            base_score = base_score * 0.5
            break
            
    final_score = max(0, min(int(base_score), 100))
    return final_score, matched_skills

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
    """Reads all saved jobs from SQLite and returns them with scores and matched skills."""
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
        score, matched_skills = calculate_score_and_skills(row[1])
        jobs_list.append({
            "id": row[0],
            "title": row[1],
            "company": row[2],
            "location": row[3],
            "url": row[4],
            "remote": row[5],
            "match_score": f"{score}%",
            "matched_skills": matched_skills
        })
        
    jobs_list = sorted(jobs_list, key=lambda x: int(x["match_score"].replace("%", "")), reverse=True)
    
    return {
        "status": "success",
        "total_matches": len(jobs_list),
        "jobs": jobs_list
    }

@app.get("/jobs/top-matches")
def get_top_matches(threshold: int = 40):
    """
    Endpoint 4: Returns only jobs scoring above the specified threshold (default >= 40%),
    sorted from highest to lowest score with attached matching skills.
    """
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, company, location, url, remote FROM jobs")
    rows = cursor.fetchall()
    conn.close()
    
    top_jobs = []
    for row in rows:
        score, matched_skills = calculate_score_and_skills(row[1])
        
        # Filter by threshold score
        if score >= threshold:
            top_jobs.append({
                "id": row[0],
                "title": row[1],
                "company": row[2],
                "location": row[3],
                "url": row[4],
                "remote": row[5],
                "match_score": f"{score}%",
                "matched_skills": matched_skills
            })
            
    # Sort in descending order (highest score first)
    top_jobs = sorted(top_jobs, key=lambda x: int(x["match_score"].replace("%", "")), reverse=True)
    
    return {
        "status": "success",
        "threshold_applied": f"{threshold}%",
        "total_top_matches": len(top_jobs),
        "jobs": top_jobs
    }

@app.get("/skills/learning-roadmap")
def get_learning_roadmap():
    """
    Analyzes all saved jobs in SQLite, aggregates which skills appear most frequently,
    and returns a learning roadmap showing which skills you have vs. which ones to learn.
    """
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT title FROM jobs")
    rows = cursor.fetchall()
    conn.close()
    
    # Track frequency of all skills found in job titles across the database
    skill_demand_count = {skill: 0 for skill in MY_SKILLS}
    other_skills_found = {}
    
    for row in rows:
        title = row[1].lower() if len(row) > 1 and row[1] else ""
        for skill in MY_SKILLS:
            if skill in title:
                skill_demand_count[skill] += 1
                
    # Sort your skills by market demand (how often they appear in fetched jobs)
    sorted_market_skills = sorted(
        [{"skill": skill, "jobs_found_in": count} for skill, count in skill_demand_count.items()],
        key=lambda x: x["jobs_found_in"],
        reverse=True
    )
    
    return {
        "status": "success",
        "my_master_skills": MY_SKILLS,
        "market_demand_analysis": sorted_market_skills,
        "learning_suggestion": "Focus on the skills at the top of your market demand list that have lower coverage, or explore adding new complementary frameworks!"
    }