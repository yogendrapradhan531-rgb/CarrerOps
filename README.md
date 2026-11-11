<div align="center">

# 🚀 CareerOps
### Autonomous Job Intelligence & Application Engineering Platform

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57.svg?logo=sqlite&logoColor=white)](https://sqlite.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)](https://docker.com)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-3.0-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

*An end-to-end full-stack data pipeline that automates job discovery, evaluates skill alignment via deterministic heuristics, injects live GitHub repository metadata, and generates tailored application packages under an enforced human-in-the-loop approval gate.*

[Live Demo](http://localhost:8000) • [Architecture](#-system-architecture) • [Key Features](#-key-engineering-features) • [API Reference](#-api-documentation) • [Quickstart](#-quickstart--installation)

</div>

---

## 📌 The Problem & The Solution

* **The Problem:** The entry-level software job market demands high personalization at scale. Fresh graduates spend 2–3 hours every day manually opening 20 browser tabs, reading irrelevant senior job listings, manually copying cover letters, and trying to tailor resumes.
* **The Solution:** **CareerOps** replaces this manual toil with a production-grade software pipeline:
  1. Automated ingestion of live job feeds with idempotent database persistence.
  2. A custom scoring engine that filters out senior positions and highlights entry-level opportunities.
  3. Dynamic context retrieval connecting directly to the developer's live GitHub profile.
  4. An enforced **Human-in-the-Loop** state machine ensuring no application is exported without human approval.

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              CAREEROPS PIPELINE ARCHITECTURE                           │
└────────────────────────────────────────────────────────────────────────────────────────┘

 [ 1. External Feeds ]
   Arbeitnow / Public Job APIs
          │
          │  (HTTP GET via requests)
          ▼
 [ 2. Extract & Normalize (ETL) ]
   Type-safe parsing ──▶ Standardized 5-field Schema (Title, Company, Location, URL, Remote)
          │
          │  (INSERT OR IGNORE INTO jobs)
          ▼
 [ 3. Relational Persistence ]
   SQLite Database (`jobs.db`) ──▶ Deduplication enforced via UNIQUE(url) constraint
          │
          ├───────────────────────────────────────────────────────┐
          ▼                                                       ▼
 [ 4. Local Search Layer ]                               [ 5. Intelligence Engine ]
   GET /jobs?keyword=python                                GET /jobs/top-matches
   (Fast indexed query via SQL WHERE)                      (Deterministic skill overlap:
                                                            +20% Junior bonus, -50% Senior penalty)
                                                                  │
                                                                  │  (Select Job #ID)
                                                                  ▼
                                                         [ 6. Agentic Tailoring ]
                                                           POST /jobs/{id}/tailor
                                                           Reads live GitHub Repos via API
                                                           Injects repos into resume_template.md
                                                                  │
                                                                  │  (Saved with status = 'DRAFT')
                                                                  ▼
                                                         [ 7. Human Approval Gate ]
                                                           GET /applications (SQL JOIN)
                                                           POST /applications/{id}/approve
                                                           POST /applications/{id}/reject
                                                                  │
                                                                  │  (status transitions to 'APPROVED')
                                                                  ▼
                                                         [ 8. Dispatch & Archival ]
                                                           GET /applications/{id}/export
                                                           Writes formatted email & tailored resume
                                                           to /outbox/ directory
```

---

## ⚡ Key Engineering Features

### 1. Idempotent Ingestion & Deduplication
- Pulls raw listings from third-party APIs.
- Normalizes disparate schemas into a uniform contract.
- Enforces an `INSERT OR IGNORE` SQL strategy backed by a `UNIQUE(url)` index, ensuring that running the pipeline repeatedly never produces duplicate rows or crashes on key collisions.

### 2. Deterministic Scoring & Seniority Penalty Engine
- Rather than relying solely on non-deterministic LLMs for basic filtering, CareerOps computes a mathematical match score ($0\%$ to $100\%$) based on keyword set intersection against a verified skill bank.
- **Junior Bonus (+20%):** Automatically boosts listings containing `"fresher"`, `"junior"`, `"intern"`, or `"associate"`.
- **Senior Penalty (-50%):** Heavily penalizes or filters listings requiring `"senior"`, `"lead"`, `"architect"`, or `"5+ years"`.

### 3. Dynamic Context Injection via Live GitHub API
- The tailoring engine calls GitHub's public REST API (`/users/{username}/repos`) to inspect public repositories, descriptions, languages, and star counts in real time.
- Matches job requirements against actual GitHub project metadata, injecting the most relevant projects into a base Markdown resume template (`resume_template.md`).

### 4. Human-in-the-Loop Safety Gate (State Machine)
- Applications transition through a strict finite state lifecycle:  
  $$\text{DRAFT} \longrightarrow \text{APPROVED} \quad \text{or} \quad \text{REJECTED}$$
- **Fail-Closed Export:** The export dispatcher explicitly blocks any application whose status is not `APPROVED` (returning HTTP 400), guaranteeing that AI-generated drafts are never dispatched without human sign-off.

### 5. Single-Page Command Center (Frontend)
- A responsive, modern dashboard built with **HTML5, Tailwind CSS, and Vanilla JavaScript (Fetch API)**.
- Features real-time search, quick-filter tags, infinite batch loading (`skip`/`limit` cursors), and an interactive modal review studio with 1-click clipboard export.

### 6. Containerized Deployment (Docker)
- Fully containerized with a lightweight `python:3.11-slim` multi-stage Dockerfile.
- Decouples host environment dependencies; runs identically in local development or deployed on cloud platforms like Render or AWS.

---

## 🛠️ Tech Stack

| Domain | Technology | Purpose |
|---|---|---|
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com/) | High-performance ASGI REST API with auto-generated OpenAPI docs |
| **Language** | [Python 3.11+](https://python.org) | Core business logic, data normalization, and async workflows |
| **Database** | [SQLite3](https://sqlite.org/) | Embedded relational storage with foreign key constraints & indexing |
| **AI / LLM Integration** | [Google Gemini API](https://ai.google.dev/) | Application synthesis, contextual pitch, and cover letter tailoring |
| **External Integrations** | [GitHub REST API](https://docs.github.com/en/rest) | Live repository metadata extraction and dynamic project routing |
| **Frontend UI** | HTML5, [Tailwind CSS](https://tailwindcss.com), JS | Client-Side Rendered (CSR) visual command center |
| **Containerization** | [Docker](https://docker.com) | Isolated Linux container deployment with volume mounts |

---

## 📡 API Documentation

Interactive Swagger documentation is available out of the box at `/docs` when the server is running.

| Method | Endpoint | Description | Status Code |
|---|---|---|---|
| `GET` | `/` | Serves the single-page visual dashboard | `200 OK` |
| `POST` | `/sync` | Triggers the external feed ETL ingestion into SQLite | `200 OK` |
| `GET` | `/jobs` | Returns all saved jobs with optional `?keyword=` filtering and pagination | `200 OK` |
| `GET` | `/jobs/top-matches` | Returns listings filtered by match score threshold ($\ge 40\%$) | `200 OK` |
| `POST` | `/jobs/{job_id}/tailor` | Generates a tailored draft & compiles custom resume into `/outbox` | `200 OK` |
| `GET` | `/applications` | Uses SQL `JOIN` to list applications alongside company metadata | `200 OK` |
| `POST` | `/applications/{app_id}/approve` | State machine transition: changes status from `DRAFT` to `APPROVED` | `200 OK` |
| `POST` | `/applications/{app_id}/reject` | State machine transition: marks application as `REJECTED` | `200 OK` |
| `GET` | `/applications/{app_id}/export` | Safety check: Exports approved application package to disk | `200 OK` / `400 Bad Request` |

---

## 📂 Project Structure

```text
Careerops/
│
├── main.py                  # Core FastAPI application, routers & business logic
├── database.py              # SQLite schema initialization & connection factory
├── index.html               # Single-page Tailwind CSS dashboard UI
├── resume_template.md       # Master Markdown resume with {{TAILORED_PROJECTS}} tag
│
├── outbox/                  # Local archive of approved applications & custom resumes
│   ├── application_*.txt    # Exported ready-to-send email packages
│   └── resume_*.md          # Tailored company-specific Markdown resumes
│
├── Dockerfile               # Multi-stage Linux container recipe
├── .dockerignore            # Excludes cache, venv, and local database from image
└── requirements.txt         # Pinned project dependencies
```

---

## 🚀 Quickstart & Installation

### Option 1: Running Locally with Python

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yogendrapradhan531-rgb/CareerOps.git
   cd CareerOps
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # Windows PowerShell
   python -m venv carrier
   .\carrier\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the development server:**
   ```bash
   uvicorn main:app --reload
   ```

5. **Open the dashboard:**  
   Navigate to [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

---

### Option 2: Running with Docker

1. **Build the container image:**
   ```bash
   docker build -t careerops .
   ```

2. **Run in detached background mode:**
   ```bash
   docker run -d -p 8000:8000 --restart unless-stopped --name careerops-app careerops
   ```

3. **Verify running containers:**
   ```bash
   docker ps
   ```
   Access the dashboard at [http://localhost:8000/](http://localhost:8000/).

---

## 🛡️ Fault Tolerance & Edge Cases

* **External API Outages (Gemini):** Calls to the generative model are wrapped in a `try...except` block with a deterministic fallback template. If the API key is missing or quota limits are exceeded (HTTP 429), the system degrades gracefully without returning a 500 Internal Server Error.
* **Malformed Feed Payloads:** Ingestion logic uses defensive type checks (`isinstance(data, dict)`) and safe dictionary access (`.get()`) to prevent crashes when external APIs return unexpected structures or null fields.
* **Dynamic Path Resolution:** Uses `os.path.abspath(__file__)` and `os.makedirs("outbox", exist_ok=True)` to ensure files are read and written reliably regardless of the working directory or host OS.

---

## 👨‍💻 Author

**Yogendra Pradhan**  
*Master of Computer Applications (MCA)* — Presidency University, Bengaluru  
*Bachelor of Computer Applications (BCA)* — Sikkim Manipal Institute of Technology (SMIT)  
- **GitHub:** [@yogendrapradhan531-rgb](https://github.com/yogendrapradhan531-rgb)  
- **Email:** yogendrapradhan531@gmail.com  
- **Location:** Bengaluru, Karnataka, India

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
