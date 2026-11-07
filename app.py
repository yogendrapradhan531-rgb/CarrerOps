from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import requests
import sqlite3
import os
import google.generativeai as genai
from database import init_db, get_db_connection

app = FastAPI()

FEED_URL = "https://www.arbeitnow.com/api/job-board-api"

# Configure Gemini API
# genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MY_SKILLS = [
    "python", "fastapi", "react", "postgresql", 
    "sql", "javascript", "tailwind", "git", "jwt", "rest api"
]

CANDIDATE_PROFILE = (
    "Yogendra is an MCA student at Presidency University with strong full-stack and backend development skills. "
    "Proficient in Python, FastAPI, Java, and JavaScript. Experienced in building web-based systems, "
    "automated database architectures, and full-stack applications like NutriMed-CDS and inventory backends."
)

# Initialize database on startup
init_db()

@app.get("/")
def home():
    """Serves the frontend CareerOps dashboard HTML file."""
    return FileResponse("index.html")

def calculate_score_and_skills(title: str):
    """Calculates score (0-100%) with bonus/penalties and matched skills."""
    if not title:
        return 0, []
        
    lower_title = title.lower()
    matched_skills = [skill for skill in MY_SKILLS if skill in lower_title]
    base_score = (len(matched_skills) / len(MY_SKILLS)) * 100
    
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
            
    return max(0, min(int(base_score), 100)), matched_skills

@app.post("/sync")
def sync_jobs():
    """Fetches external jobs, cleans them, and saves to SQLite."""
    response = requests.get(FEED_URL)
    data = response.json()
    raw_jobs = data.get("data", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    
    cleaned_jobs = [{
        "title": job.get("title"),
        "company": job.get("company_name"),
        "location": job.get("location"),
        "url": job.get("url"),
        "remote": str(job.get("remote"))
    } for job in raw_jobs if isinstance(job, dict)]
        
    conn = get_db_connection()
    cursor = conn.cursor()
    for job in cleaned_jobs:
        cursor.execute("""
            INSERT OR IGNORE INTO jobs (title, company, location, url, remote)
            VALUES (?, ?, ?, ?, ?)
        """, (job["title"], job["company"], job["location"], job["url"], job["remote"]))
    conn.commit()
    conn.close()
    
    return {"status": "success", "message": f"Successfully synced {len(cleaned_jobs)} jobs."}

@app.get("/jobs")
def get_saved_jobs(keyword: str = None, limit: int = 50):
    """Reads saved jobs from SQLite with a default limit for fast loading."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if keyword:
        cursor.execute("SELECT id, title, company, location, url, remote FROM jobs WHERE title LIKE ? LIMIT ?", (f"%{keyword}%", limit))
    else:
        cursor.execute("SELECT id, title, company, location, url, remote FROM jobs LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    jobs_list = []
    for row in rows:
        score, matched_skills = calculate_score_and_skills(row["title"])
        jobs_list.append({
            "id": row["id"], "title": row["title"], "company": row["company"],
            "location": row["location"], "url": row["url"], "remote": row["remote"],
            "match_score": f"{score}%", "matched_skills": matched_skills
        })
    return {"status": "success", "jobs": sorted(jobs_ist if 'jobs_ist' in locals() else jobs_list, key=lambda x: int(x["match_score"].replace("%", "")), reverse=True)}

@app.get("/jobs/top-matches")
def get_top_matches(threshold: int = 40):
    """Returns only jobs scoring above the threshold."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, company, location, url, remote FROM jobs")
    rows = cursor.fetchall()
    conn.close()
    
    top_jobs = []
    for row in rows:
        score, matched_skills = calculate_score_and_skills(row[1])
        if score >= threshold:
            top_jobs.append({
                "id": row[0], "title": row[1], "company": row[2],
                "location": row[3], "url": row[4], "remote": row[5],
                "match_score": f"{score}%", "matched_skills": matched_skills
            })
    return {"status": "success", "jobs": sorted(top_jobs, key=lambda x: int(x["match_score"].replace("%", "")), reverse=True)}

@app.post("/jobs/{job_id}/tailor")
def tailor_application(job_id: int):
    """Generates a tailored application package via Gemini and stores it as a DRAFT."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, company FROM jobs WHERE id = ?", (job_id,))
    job = cursor.fetchone()
    conn.close()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    _, title, company = job
    
    prompt = (
        f"You are an assistant helping Yogendra apply for a job.\n\n"
        f"Here is the Job: {title} at {company}.\n"
        f"Here is Yogendra's real profile & project background: {CANDIDATE_PROFILE}\n"
        f"Master technical skills: {', '.join(MY_SKILLS)}.\n\n"
        f"Write a concise 2-paragraph tailored cover letter and a brief 1-sentence pitch summary connecting Yogendra's real experience directly to what this role needs. Do NOT invent fake projects."
    )
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        cover_letter = response.text
        pitch_summary = f"Tailored pitch for {title} at {company} emphasizing full-stack Python/FastAPI capabilities."
    except Exception:
        pitch_summary = f"Strong alignment for {title} at {company} utilizing Python and backend expertise."
        cover_letter = (
            f"Dear Hiring Manager at {company},\n\n"
            f"I am writing to express my strong interest in the {title} position. "
            f"With my background in full-stack development, Python, and FastAPI, I am confident in my ability "
            f"to contribute effectively to your engineering team...\n\nBest regards,\nYogendra"
        )
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO applications (job_id, cover_letter, pitch_summary, status)
        VALUES (?, ?, ?, 'DRAFT')
    """, (job_id, cover_letter, pitch_summary))
    app_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "status": "success",
        "message": "Application draft generated successfully under human review gate.",
        "application_id": app_id,
        "approval_gate": "DRAFT",
        "pitch_summary": pitch_summary,
        "cover_letter": cover_letter
    }

@app.get("/applications")
def get_applications():
    """Uses a SQL JOIN to fetch applications alongside job details."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT applications.id, jobs.title, jobs.company, applications.cover_letter, applications.status
        FROM applications
        JOIN jobs ON applications.job_id = jobs.id
    """)
    rows = cursor.fetchall()
    conn.close()
    
    applications_list = [{
        "application_id": row[0],
        "job_title": row[1],
        "company": row[2],
        "cover_letter": row[3],
        "status": row[4]
    } for row in rows]
        
    return {"status": "success", "total_applications": len(applications_list), "applications": applications_list}

@app.post("/applications/{app_id}/approve")
def approve_application(app_id: int):
    """Human GO button to approve a draft application."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT applications.id, jobs.company 
        FROM applications 
        JOIN jobs ON applications.job_id = jobs.id 
        WHERE applications.id = ?
    """, (app_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Application not found")
        
    company_name = row[1]
    cursor.execute("UPDATE applications SET status = 'APPROVED' WHERE id = ?", (app_id,))
    conn.commit()
    conn.close()
    
    return {"status": f"Application #{app_id} APPROVED for {company_name}! Ready to send."}

@app.post("/applications/{app_id}/reject")
def reject_application(app_id: int):
    """Rejects an application draft."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM applications WHERE id = ?", (app_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Application not found")
        
    cursor.execute("UPDATE applications SET status = 'REJECTED' WHERE id = ?", (app_id,))
    conn.commit()
    conn.close()
    
    return {"status": f"Application #{app_id} REJECTED"}

@app.get("/applications/{app_id}/export")
def export_application(app_id: int):
    """Validates approval, compiles email package, and saves to outbox/."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT applications.id, jobs.title, jobs.company, applications.cover_letter, applications.status
        FROM applications
        JOIN jobs ON applications.job_id = jobs.id
        WHERE applications.id = ?
    """, (app_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")
        
    app_id, job_title, company, cover_letter, status = row
    
    if status != "APPROVED":
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot export. Application status is '{status}'. It must be 'APPROVED' by human review first."
        )
        
    subject = f"Application for {job_title} - Yogendra Pradhan"
    signature = (
        "\n\n---\n"
        "Yogendra Pradhan\n"
        "MCA Student | Full-Stack & Backend Developer\n"
        "Email: yogendra@example.com | Phone: +91 XXXXX XXXXX\n"
        "GitHub: https://github.com/ | LinkedIn: https://linkedin.com/"
    )
    email_body = f"Subject: {subject}\n\n{cover_letter}{signature}"
    
    safe_company_name = "".join(c for c in company if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
    filename = f"outbox/application_{safe_company_name}_{app_id}.txt"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(email_body)
        
    return {
        "status": "success",
        "message": f"Application successfully exported and archived to {filename}",
        "export_file_path": filename,
        "email_package": {
            "subject": subject,
            "recipient_company": company,
            "body": email_body
        }
    }