from backend.auth.auth_utils import register_user, login_user, is_admin
from typing import Annotated, List
import threading

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from backend.analytics.project_metrics import compute_project_metrics
from backend.rag.rag_engine import _candidate_corpus, run_candidate_search, run_llm_rag_pipeline, run_rag_pipeline
from backend.resume_processing.resume_uploader import upload_resume_bulk

UploadFilesParam = Annotated[
    List[UploadFile],
    File(..., description="Upload files"),
]

app = FastAPI(title="AI Recruitment System")


# ==============================
# REQUEST MODELS
# ==============================

class CandidateSearchRequest(BaseModel):
    role: str
    experience: str = "Any"
    additional_skills: List[str] = []


class AuthRequest(BaseModel):
    username: str
    password: str


# 🔥 NEW: ADMIN SIGNUP REQUEST
class AdminSignupRequest(BaseModel):
    admin_username: str
    admin_password: str
    username: str
    password: str


print("MAIN FILE RUNNING")


# ==============================
# CACHE WARMUP
# ==============================
def _warm_candidate_search_cache():
    try:
        _candidate_corpus()
    except Exception:
        pass


@app.on_event("startup")
def warm_caches_on_startup():
    threading.Thread(target=_warm_candidate_search_cache, daemon=True).start()


# ==============================
# BASIC ROUTES
# ==============================

@app.get("/")
def home():
    return {"message": "AI Recruitment System Running"}


# ==============================
# CUSTOM DOCS (KEEPING YOUR HTML)
# ==============================
@app.get("/docs", include_in_schema=False)
def custom_swagger_ui():
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{app.title} API Portal</title>
    </head>
    <body>
        <h1>API Running</h1>
        <p>Use default Swagger at /redoc or enable docs if needed</p>
    </body>
    </html>
    """
    return HTMLResponse(html)


# ==============================
# FILE UPLOAD
# ==============================
@app.post("/upload_resume")
async def upload(files: UploadFilesParam):
    print("FILE UPLOAD HIT")

    result = await upload_resume_bulk(files)

    return {
        "message": "Uploaded successfully",
        "data": result
    }


# ==============================
# SEARCH APIs
# ==============================
@app.get("/search", include_in_schema=False)
def search(query: str):
    data = run_rag_pipeline(query)

    return {
        "query": query,
        "results": data["candidates"]
    }


@app.get("/search_llm")
def search_llm(query: str):
    data = run_llm_rag_pipeline(query)

    return {
        "query": query,
        "results": data["candidates"],
        "llm_enabled": data["llm_enabled"],
        "llm_insights": data["llm_insights"],
    }


@app.post("/candidate_search", include_in_schema=False)
def candidate_search(payload: CandidateSearchRequest):
    data = run_candidate_search(
        role=payload.role,
        experience_value=payload.experience,
        additional_skills=payload.additional_skills,
    )

    return data


@app.get("/dashboard_metrics", include_in_schema=False)
def dashboard_metrics():
    return compute_project_metrics()


# ==============================
# 🔐 AUTH APIs (ADMIN CONTROLLED)
# ==============================

# 🔥 ADMIN-ONLY SIGNUP
@app.post("/auth/signup")
def signup(data: AdminSignupRequest):
    try:
        # ✅ Only admin can create users
        if not is_admin(data.admin_username, data.admin_password):
            return {"error": "Unauthorized: Only admin can create users"}

        if register_user(data.username, data.password):
            return {"message": "User created successfully"}

        return {"error": "User already exists"}

    except Exception as e:
        print("Signup Error:", e)
        return {"error": str(e)}


# 🔥 NORMAL LOGIN
@app.post("/auth/login")
def login(data: AuthRequest):
    try:
        if login_user(data.username, data.password):
            return {"message": "Login successful"}
        return {"error": "Invalid credentials"}

    except Exception as e:
        print("Login Error:", e)
        return {"error": str(e)}