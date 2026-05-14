import os
import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import tempfile
import shutil

load_dotenv()


def read_html(filename: str) -> str:
    path = os.path.join(os.path.dirname(__file__), "templates", filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

from services.matcher import get_top_matches
from services.generator import generate_autofill
from utils.helpers import save_session, get_session

app = FastAPI(title="RoleTrace", version="1.0.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# HEALTH CHECK
# ---------------------------
@app.get("/health")
def health():
    return {"status": "ok", "app": "RoleTrace"}


# ---------------------------
# HOME PAGE
# ---------------------------
@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(content=read_html("index.html"))


# ---------------------------
# APPLY PAGE
# ---------------------------
@app.get("/apply", response_class=HTMLResponse)
def apply_page():
    return HTMLResponse(content=read_html("apply.html"))


# ---------------------------
# UPLOAD RESUME + MATCH
# ---------------------------
@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...), k: int = 6):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        matches = get_top_matches(tmp_path, k=k)

        session_id = str(uuid.uuid4())
        from services.resume_processor import process_resume
        resume_data = process_resume(tmp_path)
        save_session(session_id, resume_data)

        return JSONResponse({
            "session_id": session_id,
            "matches": matches
        })

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


# ---------------------------
# AI AUTOFILL GENERATE
# ---------------------------
class GenerateRequest(BaseModel):
    job: dict
    fields: list
    session_id: str = ""


@app.post("/generate")
async def generate(req: GenerateRequest):
    resume_data = get_session(req.session_id) if req.session_id else {}
    resume_text = resume_data.get("raw_text", "") if resume_data else ""

    result = generate_autofill(
        job=req.job,
        fields=req.fields,
        resume_text=resume_text
    )

    return JSONResponse(result)


# ---------------------------
# AI FOLLOW-UP REWRITE
# ---------------------------
class RewriteRequest(BaseModel):
    job: dict
    instruction: str          # user's feedback e.g. "make it more enthusiastic"
    current_answers: dict     # current filled field values
    fields: list              # which fields to rewrite (all, or specific)
    session_id: str = ""


@app.post("/rewrite")
async def rewrite(req: RewriteRequest):
    from services.generator import rewrite_fields
    resume_data = get_session(req.session_id) if req.session_id else {}
    resume_text = resume_data.get("raw_text", "") if resume_data else ""

    result = rewrite_fields(
        job=req.job,
        instruction=req.instruction,
        current_answers=req.current_answers,
        fields=req.fields,
        resume_text=resume_text
    )
    return JSONResponse(result)
