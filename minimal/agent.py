# pip install google-generativeai
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
)

chat = model.start_chat()

prompt = "Wie ist der Lagerbestand der Produkte mit Artikelnummer 3 und 4?"
print(f"User: {prompt}")

response = chat.send_message(prompt)

print(f"\n\nAgent: {response.text}")