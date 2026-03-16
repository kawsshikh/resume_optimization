import json
import time
import tempfile
import os
from io import BytesIO
from pathlib import Path

import streamlit as st
import extra_streamlit_components as stx
from st_copy_to_clipboard import st_copy_to_clipboard

from src.utils.utilities import extract_pdf, extract_docx
from src.core.resume_generator import get_resume
from src.core.resume_builder import ResumeBuilder
from src.config import FONT_PATH, skeleton

## ── CSS loader ───────────────────────────────────────────────
def load_css(path: str):
    css = Path(path).read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

## ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Resume Optimizer",
    layout="wide",
    initial_sidebar_state="collapsed",
)
load_css("styles2.css")

## ── Cookie manager ───────────────────────────────────────────
# Instantiated AFTER set_page_config, at module level (not cached).
# A unique key prevents duplicate-widget warnings on rerun.
cookie_manager = stx.CookieManager(key="resume_optimizer_cm")

## ── Session state ────────────────────────────────────────────
DEFAULTS = {
    "step": 0,
    "optimized_json": {},
    "resume_text": "",
    "full_prompt": "",
    "gemini_key": "",
    "desc": "",
    "download_ready": False,
    "docx_buffer": None,
    "cookie_checked": False,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

## ── Bootstrap: load key from cookie ─────────────────────────
# stx.CookieManager needs one render cycle to hydrate its iframe.
# We use a flag so we only attempt the read AFTER the first render,
# and only until we successfully find a value (then we stop forever).
if not st.session_state.gemini_key:
    if not st.session_state.cookie_checked:
        # First render — iframe not ready yet. Just flip the flag and rerun.
        st.session_state.cookie_checked = True
        st.rerun()
    else:
        # Second render onward — iframe is ready, read is reliable.
        val = cookie_manager.get("gemini_api_key")
        if val:
            st.session_state.gemini_key = val


## ── Cookie helpers ───────────────────────────────────────────
def save_api_key(key: str):
    st.session_state.gemini_key = key
    cookie_manager.set("gemini_api_key", key, max_age=60 * 60 * 24 * 30)  # 30 days

def forget_api_key():
    st.session_state.gemini_key = ""
    cookie_manager.delete("gemini_api_key")


## ── AI call helper ───────────────────────────────────────────
def ai_calling():
    with st.spinner("Analyzing with Gemini…"):
        try:
            raw_res = get_resume(st.session_state.gemini_key, st.session_state.full_prompt)
            clean_res = raw_res.replace("```json", "").replace("```", "").strip()
            st.session_state.optimized_json = json.loads(clean_res)
            st.session_state.step = 3
            st.rerun()
        except json.JSONDecodeError:
            st.error("Gemini returned malformed JSON. Please try again or use the Manual option.")
        except Exception as e:
            st.error(f"API error: {e}")


## ── Build prompt helper ──────────────────────────────────────
def build_prompt():
    if st.session_state.resume_text and st.session_state.desc:
        with open("src/core/ai_prompt_raw", "r") as f:
            prompt_template = f.read()
        st.session_state.full_prompt = (
            f"{prompt_template}\n\n"
            f"JD: {st.session_state.desc}\n\n"
            f"Resume: {st.session_state.resume_text}\n\n"
            f"Format: {skeleton}"
        )


## ════════════════════════════════════════════════════════════
## STEP 0 — LANDING PAGE
## ════════════════════════════════════════════════════════════
def landing():
    st.markdown("""
    <style>
      .main .block-container {
        background: transparent !important;
        box-shadow: none !important;
        border-radius: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 3rem !important;
        margin-top: 0 !important;
      }
      section[data-testid="stMain"] > div:first-child { padding-top: 0 !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="landing-hero">
      <div class="landing-badge">AI-Powered</div>
      <div class="landing-badge">ATS-Friendly</div>
      <div class="landing-badge">Instant</div>
      <h1 class="landing-title">Resume<br><em>Optimizer</em></h1>
      <div class="landing-badge">Python</div>
      <div class="landing-badge">Streamlit</div>
      <div class="landing-badge">Gemini 2.5 Flash</div>
      <div class="landing-badge">python-docx</div>
      <div class="landing-badge">pdfplumber</div>
      <div class="landing-badge">CSS</div>
      <div class="landing-steps-title">How it works</div>
      <div class="steps-grid">
        <div class="step-card">
          <div class="step-num">1</div>
          <p class="step-title">Upload Your Documents</p>
          <p>Attach your resume and job description as a PDF or DOCX, or paste the text directly.</p>
        </div>
        <div class="step-card">
          <div class="step-num">2</div>
          <p class="step-title">Choose an Optimization Mode</p>
          <p>Select between Gemini AI-powered tailoring or manual refinement using your preferred tool.</p>
        </div>
        <div class="step-card">
          <div class="step-num">3</div>
          <p class="step-title">Review &amp; Polish</p>
          <p>Fine-tune the generated content section by section to ensure perfect alignment with the role.</p>
        </div>
        <div class="step-card">
          <div class="step-num">4</div>
          <p class="step-title">Download Your Resume</p>
          <p>Export your tailored, ATS-optimized <code>.docx</code> file and start applying with confidence.</p>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    _, cta_col, _ = st.columns([3, 2, 3])
    with cta_col:
        if st.button("Get Started →", type="primary", use_container_width=True):
            st.session_state.step = 1
            st.rerun()

    st.markdown("""
    <p class="landing-disclaimer">
      Be sure to review all AI-generated content carefully before downloading your resume.<br>
      <a href="https://github.com/kawsshikh/resume_optimization" target="_blank">View source on GitHub</a>
    </p>
    """, unsafe_allow_html=True)


## ════════════════════════════════════════════════════════════
## STEP 1 — INPUTS
## ════════════════════════════════════════════════════════════
def inputs():
    st.markdown("""<div class="app-nav">
      <span class="nav-brand">INPUT</span>
    </div>""", unsafe_allow_html=True)

    # ── API key bar ───────────────────────────────────────────
    if st.session_state.gemini_key:
        with st.popover("🔑 Logged in — click to log out"):
            if st.button("Forget API Key"):
                forget_api_key()
                time.sleep(0.5)
                st.rerun()
    else:
        with st.container(border=True):
            st.markdown("#### 🔑 Gemini API Key")
            st.caption("[Get a free key at Google AI Studio](https://aistudio.google.com) — stored only in your browser, never shared.")
            c1, c2 = st.columns([5, 1])
            with c1:
                api_key_input = st.text_input(
                    "API Key",
                    key="api_key_input_step1",
                    type="password",
                    label_visibility="collapsed",
                    placeholder="Paste your Gemini API key…",
                )
            with c2:
                if st.button("Save", key="save_key_step1", type="primary", use_container_width=True):
                    if api_key_input:
                        save_api_key(api_key_input)
                        st.rerun()

    st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)

    # ── Two-column inputs ─────────────────────────────────────
    col_resume, col_jd = st.columns(2, gap="large")

    with col_resume:
        with st.container(border=True):
            st.markdown("#### Your Resume")
            uploaded_file = st.file_uploader(
                "Upload PDF or DOCX",
                type=["pdf", "docx"],
                label_visibility="collapsed",
            )
            if uploaded_file and not st.session_state.resume_text:
                if uploaded_file.type == "application/pdf":
                    st.session_state.resume_text = extract_pdf(uploaded_file)
                else:
                    st.session_state.resume_text = extract_docx(uploaded_file)

            st.session_state.resume_text = st.text_area(
                "resume_text_area",
                value=st.session_state.resume_text,
                height=150,
                placeholder="Upload a file above, or paste your resume text here…",
                label_visibility="collapsed",
            )

            resume_ok = bool(st.session_state.resume_text.strip())
            if resume_ok:
                st.markdown('<p class="field-ok">✓ Resume ready</p>', unsafe_allow_html=True)
            else:
                st.markdown('<p class="field-hint">Paste or upload your resume to continue.</p>', unsafe_allow_html=True)

    with col_jd:
        with st.container(border=True):
            st.markdown("#### Job Description")
            st.session_state.desc = st.text_area(
                "jd_text_area",
                value=st.session_state.desc,
                height=270,
                placeholder="Paste the full job description here…",
                label_visibility="collapsed",
            )

            jd_ok = bool(st.session_state.desc.strip())
            if jd_ok:
                st.markdown('<p class="field-ok">✓ Job description ready</p>', unsafe_allow_html=True)
            else:
                st.markdown('<p class="field-hint">Paste a job description to continue.</p>', unsafe_allow_html=True)

    both_ready = resume_ok and jd_ok
    build_prompt()

    st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)

    if not both_ready:
        st.markdown("""
        <div class="action-blocker">
          <span class="blocker-icon">⬆</span>
          Fill in both your resume and job description above to unlock optimization.
        </div>
        """, unsafe_allow_html=True)
    else:
        if st.session_state.gemini_key:
            col1, col_or, col2 = st.columns([5, 1, 5])
            with col1:
                if st.button("⚡ Optimize with Gemini", type="primary", use_container_width=True):
                    ai_calling()
            with col_or:
                st.markdown('<div class="or-divider">or</div>', unsafe_allow_html=True)
            with col2:
                if st.button("🛠 Explore Options", use_container_width=True):
                    st.session_state.step = 2
                    st.rerun()
        else:
            _, c, _ = st.columns([2, 3, 2])
            with c:
                if st.button("Continue to Optimization →", type="primary", use_container_width=True):
                    st.session_state.step = 2
                    st.rerun()


## ════════════════════════════════════════════════════════════
## STEP 2 — SELECT OPTIMIZATION OPTION
## ════════════════════════════════════════════════════════════
def select():
    st.markdown("""<div class="app-nav"><span class="nav-brand">Resume Optimizer</span></div>""", unsafe_allow_html=True)

    st.markdown("## Optimization Strategy")
    st.markdown("<p class='page-subtitle'>Choose how you'd like to refine your resume.</p>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("#### ⚡ Option 1 — Instant AI")
        col_desc, col_action = st.columns([3, 2], gap="large")

        with col_desc:
            st.markdown("""
            **Powered by Gemini 2.5 Flash**

            - Near-instant processing
            - Automated ATS keyword analysis
            - No manual copying required
            """)

        with col_action:
            if st.session_state.gemini_key:
                st.markdown("<div style='height: 2.5rem'></div>", unsafe_allow_html=True)
                if st.button("⚡ Optimize & Format", type="primary", use_container_width=True, key="opt_btn_2"):
                    ai_calling()
            else:
                st.warning("No API key found. Enter one to continue.")
                api_key_input = st.text_input(
                    "Gemini API Key",
                    key="api_key_input_s2",
                    type="password",
                    label_visibility="collapsed",
                    placeholder="Paste API key…",
                )
                if st.button("Save Key", key="save_key_s2", type="primary", use_container_width=True):
                    if api_key_input:
                        save_api_key(api_key_input)
                        st.rerun()
                    else:
                        st.warning("Please enter an API key.")

    st.markdown("<div class='section-gap-sm'></div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("#### 🛠 Option 2 — Manual Refinement")
        col_desc, col_action = st.columns([3, 2], gap="large")

        with col_desc:
            st.markdown("""
            **Best for GPT-4, Claude, or any enterprise LLM**

            1. Copy the optimization prompt
            2. Process it in your preferred AI tool
            3. Paste the resulting JSON here
            """)
            st_copy_to_clipboard(st.session_state.full_prompt, "📋 Copy Prompt", "✅ Copied!")

        with col_action:
            raw_input = st.text_area(
                "Paste JSON result here:",
                height=180,
                key="manual_json_input",
                placeholder='{ "Personal": { ... }, ... }',
            )
            if st.button("Proceed to Formatting →", type="primary", use_container_width=True):
                if raw_input:
                    try:
                        st.session_state.optimized_json = json.loads(raw_input)
                        st.session_state.step = 3
                        st.rerun()
                    except json.JSONDecodeError as e:
                        st.error(f"Invalid JSON: {e}")
                else:
                    st.warning("Paste the JSON result before proceeding.")

    st.markdown("<div class='section-gap-sm'></div>", unsafe_allow_html=True)
    if st.button("← Back to Inputs"):
        st.session_state.step = 1
        st.rerun()


## ════════════════════════════════════════════════════════════
## STEP 3 — EDIT AND DOWNLOAD
## ════════════════════════════════════════════════════════════
def edit():
    st.markdown("""<div class="app-nav"><span class="nav-brand">Resume Optimizer</span></div>""", unsafe_allow_html=True)

    st.markdown("## Review & Edit")
    st.markdown("<p class='page-subtitle'>Expand each section to review and fine-tune the AI-generated content.</p>", unsafe_allow_html=True)

    updated_data = {}

    for section, content in st.session_state.optimized_json.items():
        with st.expander(f"**{section.replace('_', ' ').title()}**", expanded=False):

            if isinstance(content, dict) and any(isinstance(v, list) for v in content.values()):
                sub_dict = {}
                for cat_name, items in content.items():
                    st.markdown(f"**{cat_name}**")
                    items_str = ", ".join(str(i) for i in items)
                    edited = st.text_area(f"Items for {cat_name}", value=items_str, key=f"cat_{section}_{cat_name}", height=100)
                    sub_dict[cat_name] = [i.strip() for i in edited.split(",") if i.strip()]
                updated_data[section] = sub_dict

            elif isinstance(content, dict) and all(not isinstance(v, (dict, list)) for v in content.values()):
                updated_data[section] = {}
                cols = st.columns(2)
                for i, (key, value) in enumerate(content.items()):
                    with cols[i % 2]:
                        updated_data[section][key] = st.text_input(
                            key.replace("_", " ").title(), value=str(value), key=f"flat_{section}_{key}"
                        )

            elif isinstance(content, list) and content and isinstance(content[0], dict):
                updated_list = []
                for idx, item in enumerate(content):
                    with st.container(border=True):
                        st.markdown(f"**Entry #{idx + 1}**")
                        new_item = {}
                        simple_fields = {k: v for k, v in item.items() if not isinstance(v, (list, dict))}
                        detail_fields = {k: v for k, v in item.items() if isinstance(v, (list, dict))}
                        if simple_fields:
                            cols = st.columns(2)
                            for i, (k, v) in enumerate(simple_fields.items()):
                                with cols[i % 2]:
                                    new_item[k] = st.text_input(k.title(), value=str(v), key=f"nest_str_{section}_{idx}_{k}")
                        for k, v in detail_fields.items():
                            if isinstance(v, list):
                                v_str = "\n".join(str(x) for x in v)
                                edited = st.text_area(f"{k.title()} (one per line)", value=v_str, key=f"nest_list_{section}_{idx}_{k}", height=150)
                                new_item[k] = [line.strip() for line in edited.split("\n") if line.strip()]
                            else:
                                new_item[k] = st.text_area(k.title(), value=str(v), key=f"nest_solo_{section}_{idx}_{k}")
                        updated_list.append(new_item)
                updated_data[section] = updated_list

            elif isinstance(content, list):
                list_str = "\n".join(str(item) for item in content)
                edited = st.text_area(f"Edit {section}", value=list_str, key=f"list_{section}")
                updated_data[section] = [i.strip() for i in edited.split("\n") if i.strip()]

            else:
                updated_data[section] = st.text_area(f"Edit {section}", value=str(content), key=f"solo_{section}")

    st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)

    if st.button("✅ Looks Good — Proceed to Download", type="primary", use_container_width=True):
        st.session_state.optimized_json = updated_data
        st.session_state.download_ready = True
        st.session_state.docx_buffer = None

    if st.session_state.download_ready:
        st.markdown("---")
        st.markdown("## Download Your Resume")

        available_sections = ["Personal", "Summary", "Skills", "Work Experience", "Education", "Projects", "Certification"]
        order = st.multiselect(
            "Reorder / select sections to include:",
            options=available_sections,
            default=available_sections,
            key="section_order",
        )
        custom_filename = st.text_input("File name:", value="Optimized_Resume", key="filename_input")
        final_filename = custom_filename if custom_filename.endswith(".docx") else f"{custom_filename}.docx"

        st.markdown("<div class='section-gap-sm'></div>", unsafe_allow_html=True)

        if not st.session_state.docx_buffer:
            if st.button("⬇️ Generate .docx", type="primary", use_container_width=True, key="generate_docx"):
                with st.spinner("Building your resume…"):
                    try:
                        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, dir=tempfile.gettempdir()) as tmp_file:
                            json.dump(st.session_state.optimized_json, tmp_file)
                            temp_path = tmp_file.name
                        try:
                            builder = ResumeBuilder(temp_path, FONT_PATH, order)
                            buffer = BytesIO()
                            builder.build_resume(buffer)
                            buffer.seek(0)
                            st.session_state.docx_buffer = buffer.getvalue()
                        finally:
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error generating document: {e}")

        if st.session_state.docx_buffer:
            st.download_button(
                label="⬇️ Download Resume (.docx)",
                data=st.session_state.docx_buffer,
                file_name=final_filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="download_btn",
                type="primary",
                use_container_width=True,
            )
            st.success("✅ Your resume is ready! Download above or start over below.")
            st.markdown("<div class='section-gap-sm'></div>", unsafe_allow_html=True)
            _, c, _ = st.columns([4, 2, 4])
            with c:
                if st.button("🔄 Start Over", use_container_width=True):
                    for key, value in DEFAULTS.items():
                        st.session_state[key] = value
                    st.rerun()

    st.markdown("<div class='section-gap-sm'></div>", unsafe_allow_html=True)
    if st.button("← Back to Strategy"):
        st.session_state.step = 2
        st.rerun()


## ── Router ───────────────────────────────────────────────────
if st.session_state.step == 0:
    landing()
elif st.session_state.step == 1:
    inputs()
elif st.session_state.step == 2:
    select()
elif st.session_state.step == 3:
    edit()

## ── Fixed footer ─────────────────────────────────────────────
st.markdown(
    '<div class="fixed-footer"><p>A project by <strong>Kawsshikh Sajjana Gandla</strong></p></div>',
    unsafe_allow_html=True,
)