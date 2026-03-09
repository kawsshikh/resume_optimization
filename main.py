import streamlit as st
from io import BytesIO
from src.utils.utilities import extract_pdf, extract_docx
from src.core.resume_generator import get_resume
from src.core.resume_builder import ResumeBuilder
from src.config import *
from st_copy_to_clipboard import st_copy_to_clipboard
import extra_streamlit_components as stx
import time


cookie_manager = stx.CookieManager()


st.set_page_config(
    page_title="Resume Optimizer",
    layout="wide",
    initial_sidebar_state="expanded"
)

### initialization of session state elements
defaults = {
    "step": 1,
    "optimized_json": {},
    "resume_text": "",
    "full_prompt": {},
    "gemini_key": "",
    "desc": "",
    "cookie_loaded": False,
    "render_count": 0
}


for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value
st.session_state.render_count +=1

if not st.session_state.cookie_loaded and st.session_state.render_count > 1:
    cookie_val = cookie_manager.get("gemini_api_key")
    if cookie_val:
        st.session_state.gemini_key = cookie_val
    st.session_state.cookie_loaded = True

with st.sidebar:
    st.markdown("""
    # Resume ATS Optimizer
    *Tailor your professional story for every application in seconds.*

    ---

    ### :material/info: About the Project
    This tool leverages **Gemini 2.5 Flash** to intelligently re-write and re-order your resume. By aligning your experience with the specific keywords and requirements of a **Job Description**, we help you clear the initial ATS (Applicant Tracking System) filters.

    ### :material/settings: Tech Stack
    :blue[**Python**] | :orange[**Streamlit**] | :green[**Python-docx**] | :red[**pdfplumber**] | :grey[**GenAI**]

    ---

    ### :material/ads_click: How to use:
    1. **Upload or Paste** | Provide your current resume in PDF or DOCX format.
    2. **Paste the JD** | Drop the target job description into the text area.
    3. **Review & Edit** | Fine-tune the AI-generated suggestions in Step 2.
    4. **Export** | Download your optimized, ATS-friendly `.docx` file.

    > **Disclaimer:** This tool uses the *Gemini 2.5 Flash* model. Always perform a final human review of the generated content for accuracy.

    ---
    [📂 View Source Code on GitHub](https://github.com/kawsshikh/resume-optimizer)
""")


if st.session_state.gemini_key:
    with st.popover("logout"):
        if st.button("Forget API KEY"):
            cookie_manager.delete("gemini_api_key")
            st.session_state.gemini_key = ""
            st.session_state.step = 1
            st.session_state.cookie_loaded = True
            time.sleep(1)
            st.rerun()


def inputs():
    st.markdown("### Provide Resume and Job Description to Optimize")
    resume, jd = st.columns(2)
    with resume:
        with st.container(border=True):
            st.subheader("Resume")
            uploaded_file = st.file_uploader("Upload PDF or DOCX", type=["pdf", "docx"])
            if uploaded_file and not st.session_state.resume_text:
                if uploaded_file.type == "application/pdf":
                    st.session_state.resume_text = extract_pdf(uploaded_file)
                else:
                    st.session_state.resume_text = extract_docx(uploaded_file)
            st.session_state.resume_text = st.text_area("Edit text:", value=st.session_state.resume_text, height=300)
    with jd:
        with st.container(border=True):
            st.subheader("Job Description")
            st.session_state.desc = st.text_area("Paste JD here:", height=410)

    _, analyse, left = st.columns([5, 2, 5])
    with analyse:
        if st.button("Optimize", type="primary", use_container_width=True):
            if st.session_state.resume_text and st.session_state.desc:
                with open("src/core/ai_prompt_raw", "r") as f:
                    prompt_template = f.read()
                st.session_state.full_prompt = f"{prompt_template}\n\nJD: {st.session_state.desc}\n\nResume: {st.session_state.resume_text}\n\nFormat: {skeleton}"
                st.session_state.step = 2
                st.rerun()
            else:
                with _:
                    st.warning("Provide both resume and job description")


def select():
    st.markdown("## Code Optimization Strategy")
    st.info("Choose your preferred method to refine and enhance your resume.")
    st.markdown("### Option 1: Instant AI Optimization")
    with st.container(border=True):
        left, right = st.columns(2)
        with left:
            st.markdown("""
                            **Powered by Gemini 2.5 Flash**
                            * **Speed:** Near-instant processing and refactoring.
                            * **Precision:** Automated logic analysis and modern syntax application.
                            * **Effort:** Zero manual copying required.
                            """)
        with right:
            if st.session_state.gemini_key:
                st.markdown(""" <br> <br> """, unsafe_allow_html=True)
                if st.button("Optimize & Format", type="primary", use_container_width=True):
                    with st.spinner("Analyzing with Gemini..."):
                        raw_res = get_resume(st.session_state.gemini_key,st.session_state.full_prompt)
                        clean_res = raw_res.replace("```json", "").replace("```", "").strip()
                        st.session_state.optimized_json = json.loads(clean_res)
                        st.session_state.step = 3
                        st.rerun()
            else:
                st.warning("API key not found")
                api_key_input = st.text_input("Add API KEY", key="api_key_input", type="password")
                if st.button("Add Key"):
                    if api_key_input:
                        st.session_state.gemini_key = api_key_input
                        cookie_manager.set("gemini_api_key", api_key_input)
                        st.success("Key added")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.warning("Please enter an API key")

    st.markdown("### Option 2: Manual Refinement")
    with st.container(border=True):
        left, right = st.columns(2)
        with left:
            st.markdown("""
                    **Best for custom LLMs or enterprise-grade models (GPT-4, Claude 3.5)**
                    1.  **Copy** our specialized optimization prompt.
                    2.  **Process** it in your preferred external AI environment.
                    3.  **Return** the resulting JSON output here to proceed. <br> <br> <br> <br>
                    """, unsafe_allow_html=True)
            st.info(""" click below to copy prompt """)
            st_copy_to_clipboard(st.session_state.full_prompt, "📋 Copy Prompt", "✅ Copied!")
        with right:

            st.markdown("""### Ready with Result? """)
            raw_input = st.text_area("Paste result here", height=300)
            if raw_input:
                st.session_state.optimized_json =  json.loads(raw_input)
            if st.button("Proceed to Formating", type="primary", use_container_width=True):
                st.session_state.step = 3
                st.rerun()


def edit():
    st.markdown("## Review the Result")
    updated_data = {}

    for section, content in st.session_state.optimized_json.items():
        with st.expander(f"## {section.replace('_', ' ').title()}", expanded=False):

            # --- VIEW 1: Categorized Skills (dict -> list) ---
            if isinstance(content, dict) and any(isinstance(v, list) for v in content.values()):
                sub_dict = {}
                for cat_name, items in content.items():
                    st.markdown(f"**{cat_name}**")
                    items_str = ", ".join([str(i) for i in items])
                    edited = st.text_area(f"Items for {cat_name}", value=items_str, key=f"cat_{section}_{cat_name}",
                                          height=100)
                    sub_dict[cat_name] = [i.strip() for i in edited.split(",") if i.strip()]
                updated_data[section] = sub_dict

            # --- VIEW 2: Flat Dictionary (Personal Info) ---
            elif isinstance(content, dict) and all(not isinstance(v, (dict, list)) for v in content.values()):
                updated_data[section] = {}
                cols = st.columns(2)
                for i, (key, value) in enumerate(content.items()):
                    with cols[i % 2]:
                        updated_data[section][key] = st.text_input(key.replace('_', ' ').title(), value=str(value),
                                                                   key=f"flat_{section}_{key}")

            # --- VIEW 3: Detailed Experiences (list of dicts) ---
            elif isinstance(content, list) and len(content) > 0 and isinstance(content[0], dict):
                updated_list = []
                for idx, item in enumerate(content):
                    with st.container(border=True):
                        st.markdown(f"**Entry #{idx + 1}**")
                        new_item = {}
                        simple_f = {k: v for k, v in item.items() if not isinstance(v, (list, dict))}
                        detail_f = {k: v for k, v in item.items() if isinstance(v, (list, dict))}

                        if simple_f:
                            cols = st.columns(2)
                            for i, (k, v) in enumerate(simple_f.items()):
                                with cols[i % 2]:
                                    new_item[k] = st.text_input(k.title(), value=str(v),
                                                                key=f"nest_str_{section}_{idx}_{k}")

                        for k, v in detail_f.items():
                            if isinstance(v, list):
                                v_str = "\n".join([str(x) for x in v])
                                edited = st.text_area(f"{k.title()} (one per line)", value=v_str,
                                                      key=f"nest_list_{section}_{idx}_{k}", height=300)
                                new_item[k] = [l.strip() for l in edited.split("\n") if l.strip()]
                            else:
                                new_item[k] = st.text_area(k.title(), value=str(v),
                                                           key=f"nest_solo_{section}_{idx}_{k}")
                        updated_list.append(new_item)
                updated_data[section] = updated_list

            # --- VIEW 4: Simple List ---
            elif isinstance(content, list):
                list_str = "\n".join([str(item) for item in content])
                edited = st.text_area(f"Edit {section}", value=list_str, key=f"list_{section}")
                updated_data[section] = [i.strip() for i in edited.split("\n") if i.strip()]

            # --- VIEW 5: Simple String ---
            else:
                updated_data[section] = st.text_area(f"Edit {section}", value=str(content), key=f"solo_{section}")
            st.divider()

    if st.button("Looks Good! Proceed to Download", type="primary"):
        st.session_state.optimized_json = updated_data
        st.session_state.step = 4
        st.rerun()


def download():
    st.markdown("## Download Optimized Resume")
    available = ["Personal", "Summary", "Skills", "Work Experience", "Education", "Projects"]
    order = st.multiselect("Reorder sections:", options=available, default=available)

    st.markdown("---")
    custom_filename = st.text_input("💾 Save Resume As:", value="Optimized_Resume")

    # Ensure the filename has the correct extension
    if not custom_filename.endswith(".docx"):
        final_filename = f"{custom_filename}.docx"
    else:
        final_filename = custom_filename

    if st.button("Generate .docx"):
        try:
            temp_path = "src/templates/temp_optimized.json"
            with open(temp_path, "w") as f:
                json.dump(st.session_state.optimized_json, f)

            builder = ResumeBuilder(temp_path, FONT_PATH, order)
            buffer = BytesIO()
            builder.build_resume(buffer)
            buffer.seek(0)

            # Use the final_filename variable here
            st.download_button(
                label="📥 Download Resume",
                data=buffer,
                file_name=final_filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        except Exception as e:
            st.error(f"Error: {e}")


if st.session_state.step == 1:
    inputs()
if st.session_state.step == 2:
    select()
if st.session_state.step == 3:
    edit()
if st.session_state.step == 4:
    download()