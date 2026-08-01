import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

texts = ["hello", "world", "compliance", "framework"]
print("Calling embed_content with 4 texts...")
try:
    response = genai.embed_content(
        model="models/gemini-embedding-2",
        content=texts,
        task_type="retrieval_document",
        output_dimensionality=768
    )
    print("Keys in response:", list(response.keys()))
    print("Type of response['embedding']:", type(response["embedding"]))
    
    # If it is a list of lists, print the length of each list
    val = response["embedding"]
    if isinstance(val, list):
        print("Length of response['embedding']:", len(val))
        if len(val) > 0:
            print("Type of first element:", type(val[0]))
            if isinstance(val[0], list):
                print("Length of first element:", len(val[0]))
            else:
                # If the first element is a float, it means it returned a single embedding list of floats!
                print("Wait, is it a flat list of floats? Length:", len(val))
except Exception as e:
    print("Error:", str(e))
