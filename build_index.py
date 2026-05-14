import faiss
import numpy as np
import json
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

# Load jobs
with open("data/internships.json") as f:
    jobs = json.load(f)

embeddings = []
job_data = []

for job in jobs:
    text = job["title"] + " " + job["description"]
    emb = model.encode(text)

    embeddings.append(emb)
    job_data.append(job)

# Convert to numpy
embeddings = np.array(embeddings).astype("float32")

# Normalize (important for cosine similarity)
faiss.normalize_L2(embeddings)

# Create FAISS index
dimension = embeddings.shape[1]
index = faiss.IndexFlatIP(dimension)  # Inner Product = cosine after normalization
index.add(embeddings)

# Save index + metadata
faiss.write_index(index, "jobs.index")

with open("jobs_meta.json", "w") as f:
    json.dump(job_data, f)