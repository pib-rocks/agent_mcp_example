# pip install google-generativeai
import os
import google.generativeai as genai
from dotenv import load_dotenv
import requests

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

def bestand(a: float, b: float):
    """Liefert die Lagerbestände für die beiden Artikelnummern"""
    url = "http://127.0.0.1:8000/bestand"
    payload = {"a": a, "b": b}
    
    try:
        print(f"[Tool] Sending POST request to {url} with data: {payload}")
        response = requests.post(url, json=payload)
        print(payload)
                
        result_data = response.json()
        product = result_data.get("bestand")
        
        print(f"[Tool] Received product from API: {product}")
        return product
        
    except requests.exceptions.RequestException as e:
        print(f"[Tool] Error: Could not connect to the calculation API: {e}")
        return f"Error: The calculation service is unavailable. Details: {e}"

model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    tools=[bestand]
)

chat = model.start_chat(enable_automatic_function_calling=True)

# --- 4. Send a Prompt That Requires the Tool ---
prompt = "Wie ist der Lagerbestand der Produkte mit Artikelnummer 3 und 4?"
print(f"User: {prompt}")

response = chat.send_message(prompt)

print(f"\n\nAgent: {response.text}")