import json
import urllib.request

# Target endpoint
url = "https://www.arbeitnow.com/api/job-board-api"

# Set a User-Agent header (good practice for public APIs)
req = urllib.request.Request(
    url, 
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
)

# Send request and parse response
with urllib.request.urlopen(req) as response:
    raw_data = response.read().decode("utf-8")
    payload = json.loads(raw_data)

# Extract and inspect jobs
jobs = payload.get("data", [])

print(f"Retrieved {len(jobs)} jobs from page 1:\n")
for job in jobs[:5]:  # Display first 5 jobs
    print(f"Title:    {job.get('title')}")
    print(f"Company:  {job.get('company_name')}")
    print(f"Location: {job.get('location')}")
    print(f"Remote:   {job.get('remote')}")
    print(f"URL:      {job.get('url')}")
    print("-" * 40)