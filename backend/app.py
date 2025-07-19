from fastapi import FastAPI, UploadFile, Form, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pdfplumber
import json

app = FastAPI()

# Enable CORS for all origins (adjust as needed)
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
async def score_resume(
    resume: UploadFile = File(...),
    jd_pdf: UploadFile = File(None),
    job_description: str = Form(None)
):
    try:
        # Extract resume text
        with pdfplumber.open(resume.file) as pdf:
            resume_text = "".join(
                page.extract_text() for page in pdf.pages if page.extract_text()
            )

        # Extract JD from uploaded PDF or fallback to pasted text
        if jd_pdf:
            with pdfplumber.open(jd_pdf.file) as jd_pdf_obj:
                jd_text = "".join(
                    page.extract_text() for page in jd_pdf_obj.pages if page.extract_text()
                )
        elif job_description:
            jd_text = job_description
        else:
            return JSONResponse(
                content={"error": "Please provide a job description (PDF or text)."},
                status_code=400
            )

        # --- Dummy scoring logic ---
        response = {
            "ATS_Score": 88,
            "Strengths": ["Python", "Leadership"],
            "Gaps": ["AWS", "Project Management"],
            "Recommendation": "Candidate shows strong alignment with the JD."
        }

        return response

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
