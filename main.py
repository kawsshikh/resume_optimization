import json
import time
from io import BytesIO

import streamlit as st
import extra_streamlit_components as stx
from st_copy_to_clipboard import st_copy_to_clipboard

from src.utils.utilities import extract_pdf, extract_docx
from src.core.resume_generator import get_resume
from src.core.resume_builder import ResumeBuilder
from src.config import FONT_PATH, skeleton

## Cookies manager to extract API key
cookie_manager = stx.CookieManager()

## Configure Page
st.set_page_config(
    page_title="Resume Optimizer",
    layout="wide",
    initial_sidebar_state="expanded"
)

### initialization of session state elements
DEFAULTS = {
    "step": 1,
    "optimized_json": {},
    "resume_text": "",
    "full_prompt": "",
    "gemini_key": "",
    "desc": "",
    "cookie_loaded": False,
    "render_count": 0,
    "download_ready": False,
    "docx_buffer": None,
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value
st.session_state.render_count +=1


## Check if API key is present in cookies
if not st.session_state.cookie_loaded and st.session_state.render_count > 1:
    cookie_val = cookie_manager.get("gemini_api_key")
    if cookie_val:
        st.session_state.gemini_key = cookie_val
    st.session_state.cookie_loaded = True

## Instructions to the user
with st.sidebar:
        st.markdown("""
        # Resume ATS Optimizer
        #### By Kawsshikh Sajjana Gandla
        *Tailor your professional story in seconds.*

        ---

        ### :material/info: About the Project
        An AI-powered resume refactoring tool that leverages the Gemini 2.5 Flash engine to intelligently rewrite and reorder your resume based on a specific job description. This application eliminates the need to jump between multiple apps and spend hours formatting, delivering a clean, ATS-friendly output that increases your visibility to recruiters.

        ### :material/settings: Tech Stack
        :blue[**Python**] | :orange[**Streamlit**] | :green[**Python-docx**] | :red[**pdfplumber**] | :violet[**Google GenAI**] | :grey[**Pillow**] | :orange[**extra-streamlit-components**] | :green[**st-copy-to-clipboard**]

        ---

        ### :material/ads_click: How to use:
        1. **Upload or Paste** | Provide your current resume in PDF or DOCX format.
        2. **Input the JD** | Paste the target job description into the text area.
        3. **Review & Edit** | Fine-tune the AI-generated suggestions provided in Step 2.
        4. **Export** | Download your optimized, ATS-friendly `.docx` file.

        > **Disclaimer:** This tool utilizes the *Gemini 2.5 Flash* model. Always perform a final human review of the generated content to ensure accuracy.

        [View Source Code on GitHub](https://github.com/kawsshikh/resume_optimization)
    """)

## Log out option implementation
if st.session_state.gemini_key:
    with st.popover("Logged in - click to logout"):
        if st.button("Forget API KEY"):
            cookie_manager.delete("gemini_api_key")
            st.session_state.gemini_key = ""
            st.session_state.step = 1
            st.session_state.cookie_loaded = True
            time.sleep(1)
            st.rerun()

## Instructions to obtain API  key
else:
    st.info("""
    **Gemini AI Integration**
    * Please have your API key ready to optimize seamlessly.
    * To get you API key: [click here](https://aistudio.google.com)
    * Ensure you are on a trusted device before entering your credentials.
    ---
    **Privacy Note:** Your API key is stored locally in your browser session. It is never seen by the app owner. You can remove it at any time by clicking the **Log Out** button in the sidebar.
    """)


## GET RESUME AND JOB DESCRIPTION
def inputs():
    st.markdown("### Provide Resume and Job Description to Optimize")
    col_resume, col_jd = st.columns(2)

    with col_resume:
        with st.container(border=True):
            st.subheader("Resume")
            uploaded_file = st.file_uploader("Upload PDF or DOCX", type=["pdf", "docx"])
            if uploaded_file and not st.session_state.resume_text:
                if uploaded_file.type == "application/pdf":
                    st.session_state.resume_text = extract_pdf(uploaded_file)
                else:
                    st.session_state.resume_text = extract_docx(uploaded_file)
            st.session_state.resume_text = st.text_area(
                "Paste Resume/Edit extracted text:",
                value=st.session_state.resume_text,
                height=300,
            )

    with col_jd:
        with st.container(border=True):
            st.subheader("Job Description")
            st.session_state.desc = st.text_area("Paste JD here:", height=410)

    _, col_btn, col_warn = st.columns([4, 4, 4])
    with col_btn:
        if st.button("Optimize", type="primary", use_container_width=True):
            if st.session_state.resume_text and st.session_state.desc:
                with open("src/core/ai_prompt_raw", "r") as f:
                    prompt_template = f.read()
                st.session_state.full_prompt = (
                    f"{prompt_template}\n\n"
                    f"JD: {st.session_state.desc}\n\n"
                    f"Resume: {st.session_state.resume_text}\n\n"
                    f"Format: {skeleton}"
                )
                st.session_state.step = 2
                st.rerun()
            else:
                with col_warn:
                    st.warning("Please provide both a resume and a job description.")

## SELECT OPTIMIZATION OPTION
def select():
    st.markdown("## Optimization Strategy")
    st.info("Choose your preferred method to refine and enhance your resume.")


    st.markdown("### Option 1: Instant AI Optimization")
    with st.container(border=True):
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("""
            **Powered by Gemini 2.5 Flash**
            - **Speed:** Near-instant processing.
            - **Precision:** Automated analysis and modern syntax.
            - **Effort:** Zero manual copying required.
            """)
        with col_r:
            if st.session_state.gemini_key:
                st.markdown("<br><br>", unsafe_allow_html=True)
                if st.button("Optimize & Format", type="primary", use_container_width=True):
                    with st.spinner("Analyzing with Gemini…"):
                        try:
                            raw_res = get_resume(st.session_state.gemini_key, st.session_state.full_prompt)
                            clean_res = raw_res.replace("```json", "").replace("```", "").strip()
                            st.session_state.optimized_json = json.loads(clean_res)
                            st.session_state.step = 3
                            st.rerun()
                        except json.JSONDecodeError:
                            st.error("Gemini returned malformed JSON. Try again or use Option 2.")
                        except Exception as e:
                            st.error(f"API error: {e}")
            else:
                st.warning("API key not found.")
                api_key_input = st.text_input("Enter Gemini API Key", key="api_key_input", type="password")
                if st.button("Save Key"):
                    if api_key_input:
                        st.session_state.gemini_key = api_key_input
                        cookie_manager.set("gemini_api_key", api_key_input)
                        st.success("Key saved!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.warning("Please enter an API key.")


    st.markdown("### Option 2: Manual Refinement")
    with st.container(border=True):
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("""
            **Best for GPT-4, Claude, or any enterprise LLM**
            1. **Copy** the specialized optimization prompt below.
            2. **Process** it in your preferred AI environment.
            3. **Paste** the resulting JSON output on the right.
            """)
            st.info("Click below to copy the full prompt.")
            st_copy_to_clipboard(st.session_state.full_prompt, "Copy Prompt", "✅ Copied!")

        with col_r:
            st.markdown("### Ready with Result?")
            raw_input = st.text_area("Paste JSON result here:", height=300)
            if st.button("Proceed to Formatting", type="primary", use_container_width=True):
                if raw_input:
                    try:
                        st.session_state.optimized_json = json.loads(raw_input)
                        st.session_state.step = 3
                        st.rerun()
                    except json.JSONDecodeError as e:
                        st.error(f"Invalid JSON: {e}")
                else:
                    st.warning("Paste the JSON result before proceeding.")

## EDIT AND DOWNLOAD DOCUMENT AS .docx
def edit():
    st.markdown("## Review & Edit Generated Resume")
    updated_data = {}

    for section, content in st.session_state.optimized_json.items():
        with st.expander(f"## {section.replace('_', ' ').title()}", expanded=False):

            # VIEW 1: Categorized Skills (dict of lists)
            if isinstance(content, dict) and any(isinstance(v, list) for v in content.values()):
                sub_dict = {}
                for cat_name, items in content.items():
                    st.markdown(f"**{cat_name}**")
                    items_str = ", ".join(str(i) for i in items)
                    edited = st.text_area(
                        f"Items for {cat_name}",
                        value=items_str,
                        key=f"cat_{section}_{cat_name}",
                        height=100,
                    )
                    sub_dict[cat_name] = [i.strip() for i in edited.split(",") if i.strip()]
                updated_data[section] = sub_dict

            # VIEW 2: Flat dict (Personal Info)
            elif isinstance(content, dict) and all(not isinstance(v, (dict, list)) for v in content.values()):
                updated_data[section] = {}
                cols = st.columns(2)
                for i, (key, value) in enumerate(content.items()):
                    with cols[i % 2]:
                        updated_data[section][key] = st.text_input(
                            key.replace("_", " ").title(),
                            value=str(value),
                            key=f"flat_{section}_{key}",
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
                                    new_item[k] = st.text_input(
                                        k.title(), value=str(v), key=f"nest_str_{section}_{idx}_{k}"
                                    )

                        for k, v in detail_fields.items():
                            if isinstance(v, list):
                                v_str = "\n".join(str(x) for x in v)
                                edited = st.text_area(
                                    f"{k.title()} (one per line)",
                                    value=v_str,
                                    key=f"nest_list_{section}_{idx}_{k}",
                                    height=300,
                                )
                                new_item[k] = [line.strip() for line in edited.split("\n") if line.strip()]
                            else:
                                new_item[k] = st.text_area(
                                    k.title(), value=str(v), key=f"nest_solo_{section}_{idx}_{k}"
                                )
                        updated_list.append(new_item)
                updated_data[section] = updated_list


            elif isinstance(content, list):
                list_str = "\n".join(str(item) for item in content)
                edited = st.text_area(f"Edit {section}", value=list_str, key=f"list_{section}")
                updated_data[section] = [i.strip() for i in edited.split("\n") if i.strip()]


            else:
                updated_data[section] = st.text_area(
                    f"Edit {section}", value=str(content), key=f"solo_{section}"
                )

            st.divider()


    if st.button("✅ Looks Good! Proceed to Download", type="primary"):
        st.session_state.optimized_json = updated_data
        st.session_state.download_ready = True

    if st.session_state.download_ready:
        st.markdown("---")
        st.markdown("## Download Optimized Resume")

        available_sections = ["Personal", "Summary", "Skills", "Work Experience", "Education", "Projects", "Certification"]
        order = st.multiselect(
            "Reorder / select sections to include:",
            options=available_sections,
            default=available_sections,
            key="section_order",
        )

        custom_filename = st.text_input("Save Resume As:", value="Optimized_Resume", key="filename_input")
        final_filename = custom_filename if custom_filename.endswith(".docx") else f"{custom_filename}.docx"

        if st.button("Generate .docx", key="generate_docx"):
            with st.spinner("Building your resume..."):
                try:
                    temp_path = "src/templates/temp_optimized.json"
                    with open(temp_path, "w") as f:
                        json.dump(st.session_state.optimized_json, f)

                    builder = ResumeBuilder(temp_path, FONT_PATH, order)
                    buffer = BytesIO()
                    builder.build_resume(buffer)
                    buffer.seek(0)

                    st.session_state.docx_buffer = buffer.getvalue()

                except Exception as e:
                    st.error(f"Error generating document: {e}")
        if st.session_state.docx_buffer:
            st.download_button(
                label="⬇️ Download Resume",
                data=st.session_state.docx_buffer,
                file_name=final_filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="download_btn",
            )


if st.session_state.step == 1:
    inputs()
if st.session_state.step == 2:
    select()
if st.session_state.step == 3:
    edit()
