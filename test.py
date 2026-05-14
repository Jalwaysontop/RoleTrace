from services.resume_processor import process_resume
from services.skill_extractor import get_skills
from services.matcher import get_top_matches

# ---------------------------
# CONFIG
# ---------------------------
RESUME_PATH = "resume.pdf"


# ---------------------------
# STEP 1: RESUME PROCESSING
# ---------------------------
print("\n📄 Processing Resume...")

resume_data = process_resume(RESUME_PATH)

resume_text = resume_data["cleaned_text"]

print("\n🧹 Cleaned Resume Text (preview):")
print(resume_text[:300])


# ---------------------------
# STEP 2: SKILL EXTRACTION
# ---------------------------
print("\n🧠 Extracting Skills...")

resume_skills = get_skills(resume_text)

print("\n✅ Skills Found:")
print(resume_skills)


# ---------------------------
# STEP 3: MATCHING
# ---------------------------
print("\n🔍 Running AI Matching Engine...")

top_matches = get_top_matches(RESUME_PATH)


# ---------------------------
# STEP 4: OUTPUT RESULTS
# ---------------------------
print("\n🏆 TOP 3 INTERNSHIP MATCHES:\n")

for i, job in enumerate(top_matches, 1):
    print(f"{i}. {job['title']} at {job['company']}")
    print(f"   📍 Location: {job['location']}")
    print(f"   🎯 Match Score: {job['match_score']}%")

    if "matched_skills" in job:
        print(f"   🧠 Skills Used: {job['matched_skills']}")

    print("-" * 50)