from google import genai
from src.config import MODEL_ID
import re

def get_resume(api_key, ai_prompt):
    client = genai.Client(api_key=api_key)
    chat = client.chats.create(model=MODEL_ID)
    try:
        response = chat.send_message(ai_prompt)
        raw_text = response.candidates[0].content.parts[0].text
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_text, re.DOTALL)
        return json_match.group(1)

    except Exception as e:
        return e