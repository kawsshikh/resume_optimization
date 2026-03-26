# 🚀 Resume Optimizer

> An AI-powered, ATS-optimized resume tailoring app built with Streamlit and Google Gemini.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red?logo=streamlit)](https://streamlit.io)
[![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-4285F4?logo=google)](https://aistudio.google.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 📌 Overview

**Resume Optimizer** is a full-stack web application that takes your existing resume and a job description, then uses Google Gemini AI to rewrite and tailor your resume for maximum ATS compatibility. The final output is a cleanly formatted, professionally styled `.docx` file ready to submit.

The app supports two optimization paths:
- **AI-Powered** — Gemini 2.5 Flash analyzes your resume against the JD and rewrites it automatically, targeting a 98%+ ATS score.
- **Manual** — A structured prompt is generated and copied to your clipboard so you can process it in any LLM (ChatGPT, Claude, etc.) and paste the result back for a better formatted resume.

---

## ✨ Features

- 📄 **Upload or paste** your resume (PDF or DOCX)
- 📋 **Paste a job description** to align your resume with
- ⚡ **Gemini AI optimization** with a self-evaluating, iterative prompt that enforces ATS best practices
- ✏️ **Section-by-section editor** to review and fine-tune AI output before downloading
- 🔀 **Drag-to-reorder sections** before generating the final document
- 📥 **Download a polished `.docx`** with professional formatting (Aptos font, hyperlinks, ruled section headers, right-aligned dates)
- 🔑 **API key stored in browser cookie** — never sent to any server other than Google's
- 👤 **Guest mode** for manual workflow without a Gemini key

---

## 🖥️ App Flow

```
Landing Page
    ├── [Add Gemini Key]  →  API Key Page  →  Landing Page
    └── [Get Started / Continue as Guest]
            ↓
      Inputs Page  (Upload Resume + Paste JD)
            ├── [Optimize with Gemini]  ─────────────────────┐
            └── [Explore Options]                            │
                    ↓                                        │
           Strategy Page                                     │
                ├── Option 1: Instant AI (Gemini)  ──────────┤
                └── Option 2: Manual (Copy Prompt → Paste JSON)
                                                             ↓
                                                     Review & Edit Page
                                                     (Section-by-section editor)
                                                             ↓
                                                     Download Page
                                                     (.docx generation + export)
```

---

## 🗂️ Project Structure

```
resume_optimization/
│
├── app.py                        # Main Streamlit app — all page routing and UI logic
├── styles.css                    # Custom CSS
├── requirements.txt              # Python dependencies
│
└── assets/
│    ├── Aptos.ttf                 # Aptos font
│
└── src/
    ├── config.py                 # App-wide constants (model ID, font path, session defaults)
    │
    ├── core/
    │   ├── resume_generator.py   # Gemini API client — sends prompt, returns raw JSON
    │   ├── resume_builder.py     # python-docx engine — builds .docx from optimized JSON
    │   └── ai_prompt_raw         # Master AI prompt with ATS rules and self-eval loop
    │
    ├── utils/
    │   └── utilities.py          # File parsers — PDF (pdfplumber) and DOCX (python-docx)
    │
    └── templates/
        └── skeleton.json         # JSON schema that defines the resume data structure
```

---

## ⚙️ Installation

### Prerequisites

- Python 3.10 or higher
- A [Google Gemini API key](https://aistudio.google.com) (free tier available)
- The **Aptos** font file placed at `../assets/Aptos.ttf` relative to the project root (used for `.docx` generation)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/kawsshikh/resume_optimization.git
cd resume_optimization

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Web UI framework |
| `extra-streamlit-components` | Cookie manager for persisting API key |
| `st-copy-to-clipboard` | One-click prompt copy in manual mode |
| `python-docx` | `.docx` file generation and formatting |
| `google-genai` | Google Gemini API client |
| `pdfplumber` | Text extraction from PDF resumes |
| `Pillow` | Image/font utilities |
| `fonttools` | Font metrics for tab-stop calculations in `.docx` |

---

## 🔑 Gemini API Key Setup

1. Go to [Google AI Studio](https://aistudio.google.com)
2. Sign in with your Google account
3. Click **Get API key** → **Create API key** → Copy it
4. Paste it into the app on the **Add Gemini Key** screen

Your key is stored only in a browser cookie (expires in 365 days). It is never sent to any server other than Google's Gemini API.

To revoke the key from the app, click **Forget API Key** on the landing screen.

---

## 🤖 AI Prompt Design

The optimization prompt (`src/core/ai_prompt_raw`) enforces a rigorous set of rules before outputting any JSON:

| Rule | Detail |
|---|---|
| **Summary** | 60–80 word paragraph with years of experience, JD-aligned title, key skills, and 1 quantified achievement |
| **Skills** | 4–6 labeled categories (≤17 chars each), ordered by JD relevance, no cross-category duplicates |
| **Experience bullets** | XYZ formula: `[Action Verb] + [Task] + [Tool/Method] + [Metric/Result]`, no repeated verbs |
| **Tense** | Present tense for current role, past tense for all prior roles |
| **Projects** | At most 3 JD-relevant projects, each with exactly 3 measurable bullets |
| **Numbers** | Always numerals (`15%`, `3x`) — never spelled out |
| **ATS self-eval loop** | Gemini silently scores the draft across 5 dimensions (100 pts total) and rewrites until it hits 98+ before outputting |

---

## 📄 Resume JSON Schema

The app structures all resume data according to `skeleton.json`:

```json
{
  "basics":                 { "name", "location", "phone", "email", "url", "linkedin", "github" },
  "summary":                "string",
  "education":              [{ "institution", "degree", "graduation_date", "gpa" }],
  "skills":                 { "Category Name": ["skill", "skill"] },
  "professional_experience":[{ "company", "role", "duration", "responsibilities": [] }],
  "projects":               [{ "title", "tech_stack": [], "description": [], "link" }],
  "certification":          ["string"]
}
```

---

## 🛠️ Document Generation

The `ResumeBuilder` class (`src/core/resume_builder.py`) converts the optimized JSON into a formatted `.docx` using `python-docx`. Key formatting features:

- **Font:** Aptos, 10pt body / 11pt section headers / 18pt name
- **Margins:** 0.25 inches on all sides (maximizes content space)
- **Section headers:** Bold, uppercase, with a ruled bottom border
- **Dates:** Right-aligned using dynamic tab stops
- **Skills:** Left-aligned with tab stops calculated from actual font metrics (via `fonttools`)
- **Hyperlinks:** Inline blue hyperlinks for LinkedIn, GitHub, and project URLs
- **Section order:** User-selectable via multiselect before download

---

## 🎨 UI & Styling

The app uses a custom CSS theme (`styles.css`) built on top of Streamlit's default styles:

- **Fonts:** DM Sans (body) and DM Serif Display (headings) via Google Fonts
- **Brand color:** `#E8501A` (warm orange) used for CTAs, footer, and accents
- **Design:** Card-based layout with subtle shadows, smooth hover transitions, and responsive columns
- **Header/toolbar:** Hidden for a clean, app-like feel

---

## 🧩 Usage Guide

### Option A — AI Optimization (Recommended)

1. Open the app and add your Gemini API key (stored in cookie for future visits)
2. Upload your resume (PDF/DOCX) or paste the text
3. Paste the job description
4. Click **Optimize with Gemini**
5. Review and edit each section in the accordion editor
6. Reorder sections if needed, then click **Generate .docx**
7. Download your tailored resume

### Option B — Manual with External LLM

1. Open the app and click **Continue as Guest** (no API key needed)
2. Upload your resume and paste the JD
3. Click **Continue to Optimization** → **Explore Options**
4. Under **Option 2**, click **📋 Copy Prompt**
5. Paste the prompt into ChatGPT, Claude, or any LLM
6. Copy the JSON output and paste it back under **Option 2**
7. Click **Proceed to Formatting**, then review, customize, and download

---

## ⚠️ Disclaimer

- Always review AI-generated content carefully before submitting your resume.
- The AI may occasionally hallucinate metrics or rephrase content in ways that need correction — the section editor exists for this reason.
- This app does not store your resume data; all processing is done in-session.

---

## 👤 Author

**Kawsshikh Sajjana Gandla**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-kawsshikh-0A66C2?logo=linkedin)](https://linkedin.com/in/kawsshikh)
[![GitHub](https://img.shields.io/badge/GitHub-kawsshikh-181717?logo=github)](https://github.com/kawsshikh)

---

## 📃 License

This project is licensed under the [MIT License](LICENSE).
