from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return JSONResponse(content={"status": "Backend is live"}, status_code=200)

@app.post("/api/score")
async def score_resume(resume: UploadFile, job_description: str = Form(...)):
    try:
        with pdfplumber.open(resume.file) as pdf:
            resume_text = "".join(page.extract_text() for page in pdf.pages if page.extract_text())

        # Dummy score logic
        response = {
            "ATS_Score": 85,
            "Strengths": ["Python", "SQL"],
            "Gaps": ["FinTech experience"],
            "Recommendation": "Candidate is strong but lacks domain experience."
        }

        return response
    except Exception as e:
        return {"error": str(e)}