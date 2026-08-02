import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

print("Testing gemini-1.5-flash...")
try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    res = model.generate_content("Hello! What is your model name?")
    print(f"Success! Response: {res.text.strip()}")
except Exception as e:
    print(f"Failed: {str(e)}")
