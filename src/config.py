import json

FONT_PATH = "../assets/Aptos.ttf"
MODEL_ID = "gemini-2.5-flash"

try:
    with open("src/templates/skeleton.json", "r") as file:
        skeleton = json.load(file)
except FileNotFoundError:
    skeleton = {"Persoanal_Info": {}, "Professional_Experience": [], "Skills": {}}