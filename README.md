---
title: RoleTrace
emoji: 🚀
colorFrom: purple
colorTo: indigo
sdk: docker
pinned: false
app_port: 7860
---

# RoleTrace AI — Smart Internship Application Suite 🚀

RoleTrace is an AI-powered platform designed to streamline the internship hunt. It combines a professional job discovery portal with a powerful Chrome Extension that autofills complex application forms using high-quality, AI-generated answers.

## ✨ Key Features

- **Smart Match Engine**: Uses FAISS vector search to match your resume against real-world internship descriptions with precise match scores.
- **AI Autofill**: Character-by-character typewriter animation for a premium "human-like" filling experience.
- **Follow-up Chat / Rewrite**: Don't like an AI answer? Use the floating chat widget to refine specific sections (e.g., "Make my experience section sound more leadership-focused").
- **Chrome Extension Side-Panel**: A dedicated panel that detects application forms and orchestrates the AI filling process.
- **Modern UI**: A sleek, dark-themed dashboard with glassmorphism and smooth transitions.

---

## 🛠️ Project Structure

```text
├── app.py                 # FastAPI Backend
├── build_index.py         # Script to generate FAISS vector index
├── services/              # AI Logic (Matcher, Generator, Resume Processor)
├── data/                  # Job listings and vector metadata
├── templates/             # Web portal HTML files
└── extension/             # Chrome Extension (MV3) source code
```

---

## 🚀 Getting Started

### 1. Backend Setup
1. **Clone the repository** and navigate to the folder.
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure Environment Variables**:
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```
5. **Rebuild the Search Index** (Optional):
   ```bash
   python build_index.py
   ```
6. **Run the server**:
   ```bash
   uvicorn app:app --reload
   ```

### 2. Chrome Extension Setup
1. Open Chrome and go to `chrome://extensions/`.
2. Enable **Developer mode** (top right).
3. Click **Load unpacked** and select the `extension/` folder from this project.
4. Pin the **RoleTrace AI** icon to your toolbar.

---

## 📖 How to Use

1. **Find Matches**: Open `http://127.0.0.1:8000`, upload your PDF resume, and view your matched internships.
2. **Apply**: Click "Apply Now" on any job card.
3. **Autofill**: On the apply page, click the **"🤖 Auto Fill with AI"** button.
4. **Refine**: Once filled, use the **✨ Floating Widget** in the bottom-right to rewrite specific answers with your own feedback.
5. **Submit**: Hit submit and watch the success animation!

---

## 🌐 Deployment

This project is configured for **Render.com**. It includes a `render.yaml` and `Procfile` for automatic deployment. Remember to set your `GROQ_API_KEY` in the Render environment variables.

---

*Powered by Groq Llama-3 & FAISS Vector Search.*
