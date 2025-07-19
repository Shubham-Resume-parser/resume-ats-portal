from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pdfplumber
from sentence_transformers import SentenceTransformer, util
from transformers import pipeline
import torch
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

model = SentenceTransformer('all-MiniLM-L6-v2')

# Retain flan-alpaca-large as per request
skill_extraction_pipeline = pipeline("text2text-generation", model="declare-lab/flan-alpaca-large")

@app.get("/")
async def root():
    return JSONResponse(content={"status": "Backend is live"}, status_code=200)

def extract_text_from_pdf(uploaded_file):
    with pdfplumber.open(uploaded_file) as pdf:
        return "".join(page.extract_text() for page in pdf.pages if page.extract_text())

def extract_skills_with_llm(resume_text, job_text):
    resume_embedding = model.encode(resume_text, convert_to_tensor=True, normalize_embeddings=True)
    job_embedding = model.encode(job_text, convert_to_tensor=True, normalize_embeddings=True)

    similarity = util.cos_sim(resume_embedding, job_embedding).item()

    extracted_skills = call_local_llm_for_skills(resume_text, job_text)

    return {
        "ATS_Score": round(similarity * 100, 2),
        "Recommendation": interpret_score(similarity),
        "Extracted_Skills": extracted_skills
    }

def interpret_score(score):
    if score > 0.75:
        return "Strong Match"
    elif score > 0.5:
        return "Moderate Match"
    else:
        return "Weak Match"

def call_local_llm_for_skills(resume_text, job_text):
    prompt = (
        "Extract technical and domain-specific skills from the resume and compare with the job description. "
        "Provide a JSON with Matching_Skills, Missing_Skills, and Unique_Strengths.\n"
        f"Resume:\n{resume_text}\n\n"
        f"Job Description:\n{job_text}\n"
    )

    try:
        result = skill_extraction_pipeline(prompt, max_new_tokens=256)[0]['generated_text']
        json_start = result.find('{')
        if json_start != -1:
            return json.loads(result[json_start:])
        else:
            return {"error": "No JSON found in model output."}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/score")
async def score_resume(
    resume: UploadFile,
    job_description: str = Form(None),
    jd_pdf: UploadFile = None
):
    try:
        resume_text = extract_text_from_pdf(resume.file)

        if jd_pdf:
            jd_text = extract_text_from_pdf(jd_pdf.file)
        elif job_description:
            jd_text = job_description
        else:
            return JSONResponse(content={"error": "No job description provided."}, status_code=400)

        score_result = extract_skills_with_llm(resume_text, jd_text)

        return score_result
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
