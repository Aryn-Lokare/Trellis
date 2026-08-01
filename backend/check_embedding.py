import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai

logging.basicConfig(level=logging.INFO)

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

print(f"API Key: {api_key[:10]}...")

try:
    print("Testing embed_content with models/embedding-001...")
    res = genai.embed_content(
        model="models/embedding-001",
        content="test text",
        task_type="retrieval_document"
    )
    print("Success! Embedding length:", len(res["embedding"]))
except Exception as e:
    print("Failed models/embedding-001:", str(e))

try:
    print("\nTesting list_models to see what is available...")
    for m in genai.list_models():
        if "embed" in m.name:
            print(f"  Model: {m.name} (Supported: {m.supported_generation_methods})")
except Exception as e:
    print("Failed list_models:", str(e))
