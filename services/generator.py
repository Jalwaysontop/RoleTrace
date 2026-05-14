import os
import re
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ---------------------------
# EXTRACT NAME / EMAIL FROM RESUME
# ---------------------------
def extract_name_email(resume_text: str):
    if not resume_text:
        return "", ""

    prompt = f"""
From this resume text, extract ONLY:
1. The full name of the person
2. Their email address

Return ONLY valid JSON like:
{{"name": "John Doe", "email": "john@example.com"}}

If not found, use empty string "".

Resume:
{resume_text[:1500]}
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        raw = response.choices[0].message.content
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
            return data.get("name", ""), data.get("email", "")
    except Exception:
        pass
    return "", ""


# ---------------------------
# GENERATE ESSAY FIELDS VIA LLM
# ---------------------------
def generate_essay_fields(job: dict, fields: list, resume_text: str) -> dict:
    role = job.get("role", job.get("title", "this role"))
    company = job.get("company", "this company")
    skills = job.get("skills", "")

    essay_fields = [f for f in fields if f not in ("full_name", "email")]

    if not essay_fields:
        return {}

    fields_str = "\n".join([f"- {f}" for f in essay_fields])

    prompt = f"""
You are helping a candidate apply for an internship.

Role: {role}
Company: {company}
Required Skills: {skills}

Candidate Resume Summary:
{resume_text[:2000] if resume_text else "Not provided. Write generic but professional answers."}

Fill these application form fields with professional, personalized answers (2-4 sentences each):
{fields_str}

Return ONLY valid JSON like:
{{
  "why_internship": "...",
  "experience": "...",
  "why_you": "..."
}}

Be specific to the role. Sound genuine, not robotic.
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        raw = response.choices[0].message.content
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        print(f"Essay generation failed: {e}")

    return {}


# ---------------------------
# MAIN GENERATE FUNCTION
# ---------------------------
def generate_autofill(job: dict, fields: list, resume_text: str = "") -> dict:
    result = {}

    # personal info fields
    if "full_name" in fields or "email" in fields:
        name, email = extract_name_email(resume_text)
        if "full_name" in fields:
            result["full_name"] = name
        if "email" in fields:
            result["email"] = email

    # essay fields
    essay_result = generate_essay_fields(job, fields, resume_text)
    result.update(essay_result)

    return result


# ---------------------------
# FOLLOW-UP REWRITE FUNCTION
# ---------------------------
def rewrite_fields(job: dict, instruction: str, current_answers: dict,
                   fields: list, resume_text: str = "") -> dict:
    """
    Takes the user's follow-up instruction + current filled answers,
    rewrites only the essay fields (or specific ones) accordingly.
    """
    role = job.get("role", job.get("title", "this role"))
    company = job.get("company", "this company")

    # Only rewrite essay fields, skip name/email unless explicitly mentioned
    rewrite_targets = [f for f in fields if f not in ("full_name", "email")]

    if not rewrite_targets:
        return {}

    current_str = "\n".join([
        f"[{f}]: {current_answers.get(f, '(empty)')}"
        for f in rewrite_targets
    ])

    return_format = "{\n" + ",\n".join([f'  "{f}": "..."' for f in rewrite_targets]) + "\n}"

    prompt = f"""
You are editing a candidate's internship application form.

Role: {role}
Company: {company}

The user wants you to rewrite the following answers based on this instruction:
"{instruction}"

Current answers:
{current_str}

Rules:
- Apply the instruction to ALL fields provided below unless the instruction targets a specific one.
- Keep the same factual basis, just rewrite the tone/style/content as instructed.
- Each answer should be 2–4 sentences.
- Return ONLY valid JSON with exactly the following keys:

Return format:
{return_format}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        raw = response.choices[0].message.content
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        print(f"Rewrite failed: {e}")

    return {}
