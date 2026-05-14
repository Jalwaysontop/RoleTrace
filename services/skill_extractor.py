import os
import ast
import re
import json
from groq import Groq
from dotenv import load_dotenv
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ---------------------------
# AI skill extraction
# ---------------------------
def extract_skills_ai(text):

    prompt = f"""
Extract professional skills from this resume.

Rules:
- Scan full resume (projects, experience, tools)
- Only extract explicitly mentioned skills
- Do NOT infer or guess
- Return ONLY a valid Python list like:
["python", "sql", "machine learning"]

Max 20 skills.

Resume:
{text}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    return response.choices[0].message.content


# ---------------------------
# SAFE PARSER
# ---------------------------

def parse_skills(raw_output):

    print("RAW LLM OUTPUT:")
    print(raw_output+'\n')

    if not raw_output:
        return []

    # ---------------------------
    # STEP 1: extract list part only
    # ---------------------------
    match = re.search(r"\[.*\]", raw_output, re.DOTALL)
    if match:
        raw_output = match.group()

    # ---------------------------
    # STEP 2: try JSON
    # ---------------------------
    try:
        return json.loads(raw_output)
    except:
        pass

    # ---------------------------
    # STEP 3: fallback to python eval
    # ---------------------------
    try:
        return ast.literal_eval(raw_output)
    except:
        return []


# ---------------------------
# MAIN FUNCTION
# ---------------------------
def get_skills(text):

    raw = extract_skills_ai(text)
    skills = parse_skills(raw)

    # cleanup
    cleaned = []
    for s in skills:
        if isinstance(s, str):
            cleaned.append(s.lower().strip())

    return list(set(cleaned))