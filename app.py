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
from src.config import FONT_PATH, skeleton, DEFAULTS
from src.core.resume_builder import ResumeBuilder


## LOAD CSS
def load_css(path: str) -> None:
    if Path(path).exists():
        st.markdown(f"<style>{Path(path).read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

def build_prompt() -> None:
    if st.session_state.resume_text and st.session_state.desc:
        prompt_path = Path("src/core/ai_prompt_raw")
        prompt_template = prompt_path.read_text() if prompt_path.exists() else ""
        st.session_state.full_prompt = (
            f"{prompt_template}\n\n"
            f"JD: {st.session_state.desc}\n\n"
            f"Resume: {st.session_state.resume_text}\n\n"
            f"Format: {skeleton}"
        )


def ai_calling() -> None:
    with st.spinner("Analyzing with Gemini…"):
        try:
            raw_res = get_resume(st.session_state.gemini_key, st.session_state.full_prompt)
            clean_res = raw_res.replace("```json", "").replace("```", "").strip()
            st.session_state.optimized_json = json.loads(clean_res)
            st.session_state.step = 5
            st.rerun()
        except json.JSONDecodeError:
            st.error("Gemini returned malformed JSON — please try again or use the Manual option.")
        except Exception as e:
            st.error(f"API error: {e}")

def _render_section(section: str, content) -> object:
    """Render one resume section inside an expander and return the edited value."""

    with st.expander(f"**{section.replace('_', ' ').title()}**", expanded=False):

        ## Nested dict where values are lists (e.g. Skills by category)
        if isinstance(content, dict) and any(isinstance(v, list) for v in content.values()):
            sub_dict = {}
            for cat_name, items in content.items():
                st.markdown(f"**{cat_name}**")
                edited = st.text_area(
                    f"Items for {cat_name}",
                    value=", ".join(str(i) for i in items),
                    key=f"cat_{section}_{cat_name}",
                    height=100,
                )
                sub_dict[cat_name] = [i.strip() for i in edited.split(",") if i.strip()]
            return sub_dict

        ## Flat dict (e.g. Personal info)
        if isinstance(content, dict) and all(not isinstance(v, (dict, list)) for v in content.values()):
            result = {}
            cols = st.columns(2)
            for i, (key, value) in enumerate(content.items()):
                with cols[i % 2]:
                    result[key] = st.text_input(
                        key.replace("_", " ").title(),
                        value=str(value),
                        key=f"flat_{section}_{key}",
                    )
            return result

        ## List of dicts (e.g. Work Experience entries)
        if isinstance(content, list) and content and isinstance(content[0], dict):
            updated_list = []
            for idx, item in enumerate(content):
                with st.container(border=True):
                    st.markdown(f"**Entry #{idx + 1}**")
                    new_item = {}
                    simple = {k: v for k, v in item.items() if not isinstance(v, (list, dict))}
                    nested = {k: v for k, v in item.items() if isinstance(v, (list, dict))}

                    if simple:
                        cols = st.columns(2)
                        for i, (k, v) in enumerate(simple.items()):
                            with cols[i % 2]:
                                new_item[k] = st.text_input(k.title(), value=str(v), key=f"ns_{section}_{idx}_{k}")

                    for k, v in nested.items():
                        if isinstance(v, list):
                            edited = st.text_area(
                                f"{k.title()} (one per line)",
                                value="\n".join(str(x) for x in v),
                                key=f"nl_{section}_{idx}_{k}",
                                height=150,
                            )
                            new_item[k] = [line.strip() for line in edited.split("\n") if line.strip()]
                        else:
                            new_item[k] = st.text_area(k.title(), value=str(v), key=f"nd_{section}_{idx}_{k}")

                    updated_list.append(new_item)
            return updated_list

        ## Plain list
        if isinstance(content, list):
            edited = st.text_area(
                f"Edit {section}",
                value="\n".join(str(i) for i in content),
                key=f"list_{section}",
            )
            return [i.strip() for i in edited.split("\n") if i.strip()]

        ## Scalar fallback
        return st.text_area(f"Edit {section}", value=str(content), key=f"solo_{section}")


load_css("styles.css")


## CONFIG ADD
st.set_page_config(
    page_title="Resume Optimizer",
    layout="wide",
    initial_sidebar_state="collapsed",
)
load_css("styles2.css")

cookie_manager = stx.CookieManager()
cookies = cookie_manager.get_all()
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

##GET GEMINI KEY
if cookies.get("gemini_key"):
    st.session_state.gemini_key = cookies.get("gemini_key")

##FOOTER
st.markdown(
    '<div class="fixed-footer"><p>A project by <strong>Kawsshikh Sajjana Gandla</strong></p></div>',
    unsafe_allow_html=True,
)


## PAGE 0
def landing() -> None:
    st.markdown("""
        <div class="landing-hero">
          <div class="badge-row">
            <span class="landing-badge">AI-Powered</span>
            <span class="landing-badge">ATS-Friendly</span>
            <span class="landing-badge">Instant</span>
          </div>
          <h1 class="landing-title">Resume<br><em>Optimizer</em></h1>
          <div class="badge-row badge-row--tech">
            <span class="landing-badge landing-badge--tech">Python</span>
            <span class="landing-badge landing-badge--tech">Streamlit</span>
            <span class="landing-badge landing-badge--tech">Gemini 2.5 Flash</span>
            <span class="landing-badge landing-badge--tech">python-docx</span>
            <span class="landing-badge landing-badge--tech">pdfplumber</span>
          </div>
          <p class="landing-steps-title">How it works</p>
          <div class="steps-grid">
            <div class="step-card">
              <div class="step-num">1</div>
              <p class="step-title">Upload Your Documents</p>
              <p>Attach your resume and job description as PDF or DOCX, or paste the text directly.</p>
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

    _, col_left, col_right, _ = st.columns([2, 3, 3, 2])

    if not st.session_state.gemini_key:
        with col_left:
            if st.button("Add Gemini API Key", type="primary", use_container_width=True):
                st.session_state.step = 1
                st.rerun()
        with col_right:
            if st.button("Continue as Guest", use_container_width=True):
                st.session_state.step = 3
                st.rerun()
    else:
        with col_left:
            if st.button("Forget API Key", use_container_width=True):
                st.session_state.clear()
                cookie_manager.delete("gemini_key")
                time.sleep(0.1)
                st.session_state.step = 2
                st.rerun()
        with col_right:
            if st.button("Get Started →", type="primary", use_container_width=True):
                st.session_state.step = 3
                st.rerun()

    st.markdown("""
        <p class="landing-disclaimer">
          Review all AI-generated content carefully before downloading your resume.<br>
          <a href="https://github.com/kawsshikh/resume_optimization" target="_blank">View source on GitHub ↗</a>
        </p>
    """, unsafe_allow_html=True)


## PAGE 1
def login() -> None:
    st.markdown("""
        <div class="landing-hero">
          <h1 class="landing-title">Add your<br><em>Gemini Key</em></h1>
        </div>
        <div class="login-steps-grid">
          <div class="step-card">
            <div class="step-num">1</div>
            <p class="step-title">Go to Google AI Studio</p>
            <p>Visit <a href="https://aistudio.google.com" target="_blank">aistudio.google.com</a> and sign in with your Google account.</p>
          </div>
          <div class="step-card">
            <div class="step-num">2</div>
            <p class="step-title">Create an API Key</p>
            <p>Click <strong>Get API key</strong> in the left sidebar, then <strong>Create API key</strong>. Copy the key shown.</p>
          </div>
          <div class="step-card">
            <div class="step-num">3</div>
            <p class="step-title">Paste it below</p>
            <p>Your key is stored only in your browser cookie — never sent to any server other than Google's.</p>
          </div>
        </div>
    """, unsafe_allow_html=True)

    key = st.text_input("Paste your Gemini API Key", type="password", placeholder="AIza…", label_visibility="collapsed")

    _, col_save, col_back, _ = st.columns([1, 3, 3, 1])
    with col_save:
        if st.button("Store API Key", type="primary", use_container_width=True):
            if key:
                st.session_state.gemini_key = key
                cookie_manager.set("gemini_key", key, max_age=365 * 24 * 60 * 60)
                st.session_state.step = 0
                time.sleep(1)
                st.rerun()
            else:
                st.warning("Please paste your API key before saving.")
    with col_back:
        if st.button("← Back to Home", use_container_width=True):
            st.session_state.step = 0
            st.rerun()

## PAGE 2
def thankyou() -> None:
    st.markdown("""
        <div class="landing-hero">
          <h1 class="landing-title">Key<br><em>Removed</em></h1>
          <p class="landing-subtitle">Your Gemini API key has been cleared from this browser.</p>
        </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([3, 3, 3])
    with col:
        if st.button("Go to Home", type="primary", use_container_width=True):
            st.session_state.clear()
            st.rerun()

## PAGE 3
def inputs() -> None:
    st.markdown('<div class="app-nav"><span class="nav-brand">Resume Optimizer</span></div>', unsafe_allow_html=True)

    col_resume, col_jd = st.columns(2, gap="large")

    with col_resume:
        with st.container(border=True):
            st.markdown("#### Your Resume")
            uploaded_file = st.file_uploader(
                "Upload PDF or DOCX",
                type=["pdf", "docx"],
                label_visibility="collapsed",
            )
            if uploaded_file:
                ext = uploaded_file.type
                st.session_state.resume_text = (
                    extract_pdf(uploaded_file) if ext == "application/pdf"
                    else extract_docx(uploaded_file)
                )

            st.session_state.resume_text = st.text_area(
                "resume_text_area",
                value=st.session_state.resume_text,
                height=150,
                placeholder="Upload a file above, or paste your resume text here…",
                label_visibility="collapsed",
            )

            resume_ok = bool(st.session_state.resume_text.strip())
            st.markdown(
                '<p class="field-ok">✓ Resume ready</p>' if resume_ok
                else '<p class="field-hint">Paste or upload your resume to continue.</p>',
                unsafe_allow_html=True,
            )

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
            st.markdown(
                '<p class="field-ok">✓ Job description ready</p>' if jd_ok
                else '<p class="field-hint">Paste a job description to continue.</p>',
                unsafe_allow_html=True,
            )

    both_ready = resume_ok and jd_ok
    if both_ready:
        build_prompt()

    st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)

    if not both_ready:
        st.warning("Fill in both your resume and job description above to unlock optimization.")
        return

    if st.session_state.gemini_key:
        col_ai, col_or, col_manual = st.columns([5, 1, 5])
        with col_ai:
            if st.button("⚡ Optimize with Gemini", type="primary", use_container_width=True):
                ai_calling()
        with col_or:
            st.markdown('<div class="or-divider">or</div>', unsafe_allow_html=True)
        with col_manual:
            if st.button("Explore Options →", use_container_width=True):
                st.session_state.step = 4
                st.rerun()
    else:
        _, col, _ = st.columns([2, 3, 2])
        with col:
            if st.button("Continue to Optimization →", type="primary", use_container_width=True):
                st.session_state.step = 4
                st.rerun()

## PAGE 4
def select() -> None:
    st.markdown('<div class="app-nav"><span class="nav-brand">Optimization Strategy</span></div>', unsafe_allow_html=True)
    st.markdown("### Choose how you'd like to refine your resume")

    ## Option 1 — Instant AI
    with st.container(key="option_1_card"):
        st.markdown("#### Option 1 — Instant AI")
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
                st.markdown("<div style='height:2.5rem'></div>", unsafe_allow_html=True)
                if st.button("⚡ Optimize & Format", type="primary", use_container_width=True, key="opt_ai"):
                    ai_calling()
            else:
                st.markdown("""
                    <div class="guest-warning">
                      <p class="guest-warning-title">Gemini not available</p>
                      <p class="guest-warning-body">
                        You're browsing as a guest. AI optimisation requires a Gemini API key.
                        Go back to the home screen to add one — it only takes a minute.
                      </p>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("← Add API Key", type="primary", use_container_width=True, key="guest_home"):
                    st.session_state.step = 0
                    st.rerun()

    st.markdown("<div class='section-gap-sm'></div>", unsafe_allow_html=True)

    ## Option 2 — Manual via any LLM
    with st.container(key="option_2_card"):
        st.markdown("#### Option 2 — Manual Refinement")
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
                        st.session_state.step = 5
                        st.rerun()
                    except json.JSONDecodeError as e:
                        st.error(f"Invalid JSON: {e}")
                else:
                    st.warning("Paste the JSON result before proceeding.")

    st.markdown("<div class='section-gap-sm'></div>", unsafe_allow_html=True)
    if st.button("← Back to Inputs"):
        st.session_state.step = 3
        st.rerun()

def edit() -> None:
    st.markdown('<div class="app-nav"><span class="nav-brand">Resume Optimizer</span></div>', unsafe_allow_html=True)
    st.markdown("## Review & Edit")
    st.markdown(
        "<p class='page-subtitle'>Expand each section to review and fine-tune the AI-generated content.</p>",
        unsafe_allow_html=True,
    )

    updated_data = {
        section: _render_section(section, content)
        for section, content in st.session_state.optimized_json.items()
    }

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
            if st.button("⬇ Generate .docx", type="primary", use_container_width=True, key="generate_docx"):
                with st.spinner("Building your resume…"):
                    try:
                        with tempfile.NamedTemporaryFile(
                            mode="w", suffix=".json", delete=False, dir=tempfile.gettempdir()
                        ) as tmp:
                            json.dump(st.session_state.optimized_json, tmp)
                            temp_path = tmp.name
                        try:
                            builder = ResumeBuilder(temp_path, FONT_PATH, order)
                            buf = BytesIO()
                            builder.build_resume(buf)
                            buf.seek(0)
                            st.session_state.docx_buffer = buf.getvalue()
                        finally:
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error generating document: {e}")

        if st.session_state.docx_buffer:
            st.download_button(
                label="⬇ Download Resume (.docx)",
                data=st.session_state.docx_buffer,
                file_name=final_filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="download_btn",
                type="primary",
                use_container_width=True,
            )
            st.success("✅ Your resume is ready!")
            st.markdown("<div class='section-gap-sm'></div>", unsafe_allow_html=True)
            _, col, _ = st.columns([4, 2, 4])
            with col:
                if st.button("🔄 Start Over", use_container_width=True):
                    for key, value in DEFAULTS.items():
                        st.session_state[key] = value
                    st.rerun()

    st.markdown("<div class='section-gap-sm'></div>", unsafe_allow_html=True)
    if st.button("← Back to Strategy"):
        st.session_state.step = 4
        st.rerun()


_PAGES = {
    0: landing,
    1: login,
    2: thankyou,
    3: inputs,
    4: select,
    5: edit,
}

_PAGES.get(st.session_state.step, landing)()