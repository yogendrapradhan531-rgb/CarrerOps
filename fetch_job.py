from fastapi import FastAPI
import requests

app = FastAPI()

FEED_URL = "https://www.arbeitnow.com/api/job-board-api"

@app.get("/jobs")
def get_jobs():
    response = requests.get(FEED_URL)
    print(f"API Status Code: {response.status_code}")
    
    # 1. Extract the raw job list under the key "data"
    raw_jobs = response.json().get("data", [])
    
    # 2. Create an empty list
    cleaned_jobs = []
    
    # 3. Loop through raw jobs and extract the 5 essential fields
    for job in raw_jobs:
        clean_job = {
            "title": job.get("title"),
            "company": job.get("company_name"),
            "location": job.get("location"),
            "url": job.get("url"),
            "remote": job.get("remote")
        }
        cleaned_jobs.append(clean_job)
        
    # 4. Return cleaned_jobs instead of the raw response
    return cleaned_jobs