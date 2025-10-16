# pip install fastapi "uvicorn[standard]" requests
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Numbers(BaseModel):
    a: float
    b: float

# Define the API endpoint
@app.post("/bestand")
def multiply_numbers(numbers: Numbers):
    """Liefert die Lagerbestände der beiden Artikelnummern."""
    print(f"-> Request received to multiply {numbers.a} and {numbers.b}")
    result = 5 * numbers.a + 7 * numbers.b
    print(f"<- Sending result: {result}")
    return {"bestand": result}

# Run the server when the script is executed
if __name__ == "__main__":
    print("✅ FastAPI server is starting on http://127.0.0.1:8000")
    print("   Visit http://127.0.0.1:8000/docs for interactive API docs.")
    uvicorn.run(app, host="127.0.0.1", port=8000)