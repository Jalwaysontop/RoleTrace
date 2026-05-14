import faiss
import numpy as np
import json
from sentence_transformers import SentenceTransformer

# IMPORT FROM YOUR MODULES
from services.resume_processor import process_resume
from services.skill_extractor import get_skills

model = SentenceTransformer("all-MiniLM-L6-v2")

# ---------------------------
# LOAD FAISS + DATA
# ---------------------------
index = faiss.read_index("jobs.index")

with open("jobs_meta.json", "r") as f:
    jobs = json.load(f)


# ---------------------------
# EMBEDDING
# ---------------------------
def get_embedding(text):
    emb = model.encode([text]).astype("float32")
    faiss.normalize_L2(emb)
    return emb


# ---------------------------
# SKILL BOOST
# ---------------------------
def skill_overlap_score(resume_skills, job_text):

    if not resume_skills:
        return 0

    job_text = job_text.lower()
    return sum(1 for s in resume_skills if s in job_text)


# ---------------------------
# MAIN FUNCTION (CLEAN PIPELINE)
# ---------------------------
def get_top_matches(resume_file_path, k=3):

    # STEP 1: USE resume_processor.py
    resume_data = process_resume(resume_file_path)
    resume_text = resume_data["cleaned_text"]

    # STEP 2: USE skill_extractor.py
    resume_skills = get_skills(resume_text)

    # STEP 3: EMBEDDING (only here)
    resume_emb = get_embedding(resume_text)

    # STEP 4: FAISS search
    scores, indices = index.search(resume_emb, k * 5)

    results = []

    for i in range(len(indices[0])):

        idx = indices[0][i]
        base_score = float(scores[0][i]) * 100

        job = jobs[idx]
        job_text = (job["title"] + " " + job["description"]).lower()

        # STEP 5: skill boost (light signal)
        boost = skill_overlap_score(resume_skills, job_text) * 1.5

        final_score = base_score + boost

        results.append({
            **job,
            "match_score": round(final_score, 2),
            "matched_skills": resume_skills
        })

    results.sort(key=lambda x: x["match_score"], reverse=True)

    return results[:k]