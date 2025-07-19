from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pdfplumber
from sentence_transformers import SentenceTransformer, util
import torch
import json
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

similarity_model = SentenceTransformer('all-MiniLM-L6-v2')

# Fallback model setup
fallback_model_name = "t5-small"
tiny_model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

# Load primary model
try:
    llm_model_name = "google/flan-t5-base"
    tokenizer = AutoTokenizer.from_pretrained(llm_model_name)
    llm_model = AutoModelForSeq2SeqLM.from_pretrained(llm_model_name)
except Exception:
    try:
        tokenizer = AutoTokenizer.from_pretrained(fallback_model_name)
        llm_model = AutoModelForSeq2SeqLM.from_pretrained(fallback_model_name)
        llm_model_name = fallback_model_name
    except Exception:
        tokenizer = AutoTokenizer.from_pretrained(tiny_model_name)
        llm_model = AutoModelForSeq2SeqLM.from_pretrained(tiny_model_name)
        llm_model_name = tiny_model_name

@app.get("/")
async def root():
    return JSONResponse(content={"status": "Backend is live"}, status_code=200)

def extract_text_from_pdf(uploaded_file):
    with pdfplumber.open(uploaded_file) as pdf:
        return "".join(page.extract_text() for page in pdf.pages if page.extract_text())

def extract_skills_with_llm(resume_text, job_text):
    resume_embedding = similarity_model.encode(resume_text, convert_to_tensor=True, normalize_embeddings=True)
    job_embedding = similarity_model.encode(job_text, convert_to_tensor=True, normalize_embeddings=True)

    similarity = util.cos_sim(resume_embedding, job_embedding).item()

    extracted_skills = call_llm_locally(resume_text, job_text)

    return {
        "ATS_Score": round(similarity * 100, 2),
        "Recommendation": interpret_score(similarity),
        "Extracted_Skills": extracted_skills,
        "Model_Used": llm_model_name
    }

def interpret_score(score):
    if score > 0.75:
        return "Strong Match"
    elif score > 0.5:
        return "Moderate Match"
    else:
        return "Weak Match"

def call_llm_locally(resume_text, job_text):
    prompt = (
        "Extract technical and domain-specific skills from the resume and compare with the job description. "
        "Provide a JSON with Matching_Skills, Missing_Skills, and Unique_Strengths.\n"
        f"Resume:\n{resume_text}\n\n"
        f"Job Description:\n{job_text}\n"
    )

    try:
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
        outputs = llm_model.generate(**inputs, max_new_tokens=512)
        decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)

        json_start = decoded.find('{')
        if json_start != -1:
            return json.loads(decoded[json_start:])
        return {"error": "No valid JSON found in model output."}
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
