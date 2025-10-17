# First, install the required libraries:
# pip install "uvicorn[standard]" fastmcp pydantic

import uvicorn
from pydantic import BaseModel, Field
from fastmcp import FastMCP

# 1. Initialize the FastMCP application.
# This wraps a FastAPI instance and sets up the /mcp endpoint.
mcp_app = FastMCP()

# 2. Define the message models (request and response) using Pydantic.
# These models define the structure of the data sent to and from the server.

class BestandAnfrage(BaseModel):
    """
    Anfragemodell für Lagerbestände.
    Represents the "ask" message for inventory levels.
    """
    artikel_a: float = Field(..., description="Die Menge des Artikels A.", json_schema_extra={"example": 10})
    artikel_b: float = Field(..., description="Die Menge des Artikels B.", json_schema_extra={"example": 20})

class BestandAntwort(BaseModel):
    """
    Antwortmodell mit dem berechneten Lagerbestand.
    Represents the "tell" message containing the calculated inventory.
    """
    bestand: float = Field(..., description="Der berechnete Gesamtbestand.", json_schema_extra={"example": 190})


# 3. Define a tool function for calculating inventory.
# The @mcp_app.tool decorator automatically registers this function as an MCP tool.
@mcp_app.tool
def calculate_inventory(artikel_a: float, artikel_b: float) -> dict:
    """
    Verarbeitet die Anfrage und liefert die Lagerbestände der beiden Artikelnummern.
    Calculates inventory based on quantities of articles A and B.
    
    Args:
        artikel_a: Die Menge des Artikels A (Quantity of article A)
        artikel_b: Die Menge des Artikels B (Quantity of article B)
    
    Returns:
        dict: Dictionary containing the calculated inventory result
    """
    print(f"-> Anfrage für Artikel A={artikel_a}, B={artikel_b} erhalten.")

    # Business logic: Calculate the final inventory number
    result = 5 * artikel_a + 7 * artikel_b

    print(f"<- Ergebnis wird gesendet: {result}")
    
    # Return a dictionary that FastMCP will serialize
    return {"bestand": result}

# 4. Run the server when the script is executed
if __name__ == "__main__":
    print("✅ FastMCP server is starting...")
    print("   The server will run with SSE transport on http://127.0.0.1:8000")
    print("   Visit http://127.0.0.1:8000/docs for interactive API docs.")
    mcp_app.run(transport="sse", host="127.0.0.1", port=8000)