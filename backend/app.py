from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pdfplumber
from sentence_transformers import SentenceTransformer, util
import torch
import json
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Similarity model for semantic matching
similarity_model = SentenceTransformer('all-MiniLM-L6-v2')

# Primary and fallback models for skill/entity extraction
primary_model_name = "mistralai/Mistral-7B-Instruct"
fallback_model_name = "google/flan-t5-small"
tiny_model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

# Try loading models with fallback logic
try:
    llm_pipeline = pipeline("text-generation", model=primary_model_name, torch_dtype=torch.float16, device_map="auto")
    llm_model_name = primary_model_name
except Exception:
    try:
        llm_pipeline = pipeline("text2text-generation", model=fallback_model_name)
        llm_model_name = fallback_model_name
    except Exception:
        llm_pipeline = pipeline("text-generation", model=tiny_model_name)
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
        "You are an expert resume evaluator. Compare the resume and job description below. "
        "Extract and return a JSON object with keys: Matching_Skills, Missing_Skills, and Unique_Strengths.\n"
        f"Resume:\n{resume_text}\n\n"
        f"Job Description:\n{job_text}\n"
        "Respond ONLY with the JSON output."
    )

    try:
        response = llm_pipeline(prompt, max_new_tokens=512, do_sample=False)[0]["generated_text"]
        json_start = response.find('{')
        if json_start != -1:
            return json.loads(response[json_start:])
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
