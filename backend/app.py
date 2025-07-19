# ats_dual_model_pipeline.py

from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pdfplumber
import tempfile
from sentence_transformers import SentenceTransformer, util
from sklearn.metrics.pairwise import cosine_similarity
import torch
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Semantic Similarity Model
embedding_model = SentenceTransformer('BAAI/bge-large-en-v1.5')

# Basic skills list (can be replaced with LLM or extended list)
skill_keywords = [
    "python", "java", "c++", "sql", "excel", "machine learning", "data analysis",
    "communication", "project management", "aws", "docker", "linux", "git",
    "react", "node.js", "nlp", "deep learning", "api", "flask", "fastapi"
]


def extract_text_from_pdf(file):
    with pdfplumber.open(file) as pdf:
        return "\n".join(
            page.extract_text() for page in pdf.pages if page.extract_text()
        )


def clean_text(text):
    return re.sub(r"[^a-zA-Z0-9\s]", "", text.lower())


def extract_skills_from_text(text):
    text = clean_text(text)
    return [skill for skill in skill_keywords if skill in text]


def get_embedding(text):
    return embedding_model.encode(text, convert_to_tensor=True)


def score_resume_pipeline(resume_text, jd_text):
    resume_skills = extract_skills_from_text(resume_text)
    jd_skills = extract_skills_from_text(jd_text)

    # Semantic similarity
    resume_embedding = get_embedding(resume_text)
    jd_embedding = get_embedding(jd_text)
    similarity_score = float(util.cos_sim(resume_embedding, jd_embedding)[0])

    matched_skills = list(set(resume_skills) & set(jd_skills))
    skill_match_score = len(matched_skills) / max(len(jd_skills), 1)

    ats_score = round((0.7 * similarity_score + 0.3 * skill_match_score) * 100)

    return {
        "ATS_Score": ats_score,
        "Strengths": matched_skills,
        "Gaps": list(set(jd_skills) - set(matched_skills)),
        "Recommendation": "Well aligned" if ats_score > 75 else "Needs improvement"
    }


@app.get("/")
async def root():
    return JSONResponse(content={"status": "Backend is live"}, status_code=200)


@app.post("/api/score")
async def score_resume(
    resume: UploadFile,
    job_description: str = Form(None),
    jd_pdf: UploadFile = None
):
    try:
        # Extract resume text
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(await resume.read())
            resume_text = extract_text_from_pdf(tmp.name)

        # Extract JD text from file or form
        if jd_pdf:
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(await jd_pdf.read())
                jd_text = extract_text_from_pdf(tmp.name)
        elif job_description:
            jd_text = job_description
        else:
            return JSONResponse(status_code=400, content={"error": "JD missing."})

        result = score_resume_pipeline(resume_text, jd_text)
        return JSONResponse(content=result)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
