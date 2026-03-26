import json

FONT_PATH = "../assets/Aptos.ttf"
MODEL_ID = "gemini-2.5-flash"

DEFAULTS = {
    "step": 0,
    "optimized_json": {},
    "resume_text": "",
    "full_prompt": "",
    "gemini_key": "",
    "desc": "",
    "download_ready": False,
    "docx_buffer": None,
}



try:
    with open("src/templates/skeleton.json", "r") as file:
        skeleton = json.load(file)
except FileNotFoundError:
    skeleton = {"Persoanal_Info": {}, "Professional_Experience": [], "Skills": {}}