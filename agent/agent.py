# pip install google-generativeai
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

def bestand(a: float, b: float):
    """Liefert die Lagerbestände für die beiden Artikelnummern"""
    return 5 * a + 7 * b

model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    tools=[bestand]
)

chat = model.start_chat(enable_automatic_function_calling=True)

prompt = "Wie ist der Lagerbestand der Produkte mit Artikelnummer 3 und 4?"
print(f"User: {prompt}")

response = chat.send_message(prompt)

print(f"\n\nAgent: {response.text}")