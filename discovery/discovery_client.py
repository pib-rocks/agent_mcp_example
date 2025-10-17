# First, install the fastmcp library:
# pip install fastmcp

import asyncio
from fastmcp import Client

# Define the server's SSE endpoint
SERVER_URL = "http://127.0.0.1:8000/sse"

async def discover_and_call_tools():
    """
    Connects to the FastMCP server and discovers available tools,
    then allows the user to call them interactively.
    """
    print(f"🔗 Verbinde mit FastMCP Server: {SERVER_URL}")
    
    try:
        # Create client and connect to the server
        client = Client(SERVER_URL)
        
        async with client:
            print("✅ Erfolgreich mit dem Server verbunden!")
            
            # List available tools
            tools = await client.list_tools()
            
            if not tools:
                print("⚠️ Keine Tools auf dem Server gefunden.")
                return
            
            print(f"\n✅ Verfügbare Tools gefunden ({len(tools)}):")
            for i, tool in enumerate(tools):
                print(f"  [{i + 1}] {tool.name}")
                if tool.description:
                    print(f"      Beschreibung: {tool.description}")
                if tool.inputSchema and tool.inputSchema.get('properties'):
                    print(f"      Parameter: {list(tool.inputSchema['properties'].keys())}")
                print()
            
            # Let user choose a tool
            while True:
                try:
                    choice = int(input("Welches Tool möchten Sie aufrufen? (Nummer eingeben): "))
                    if 1 <= choice <= len(tools):
                        selected_tool = tools[choice - 1]
                        await call_tool_interactively(client, selected_tool)
                        break
                    else:
                        print("Ungültige Auswahl. Bitte versuchen Sie es erneut.")
                except ValueError:
                    print("Bitte geben Sie eine gültige Nummer ein.")
    
    except Exception as e:
        print(f"❌ Fehler bei der Verbindung zum Server: {e}")
        print("Stellen Sie sicher, dass der Server läuft: python fastmcp_server.py")


async def call_tool_interactively(client: Client, tool):
    """
    Prompts the user for tool parameters and calls the tool.
    """
    print(f"\n--- Aufruf des Tools '{tool.name}' ---")
    
    # Get tool parameters from input schema
    input_schema = tool.inputSchema or {}
    properties = input_schema.get('properties', {})
    required_params = input_schema.get('required', [])
    
    if not properties:
        print("Dieses Tool benötigt keine Parameter.")
        args = {}
    else:
        print("Bitte geben Sie die Parameter ein:")
        args = {}
        
        for param_name, param_info in properties.items():
            param_type = param_info.get('type', 'string')
            param_desc = param_info.get('description', '')
            is_required = param_name in required_params
            
            while True:
                required_text = " (erforderlich)" if is_required else " (optional)"
                prompt = f"  {param_name} ({param_type}){required_text}: "
                
                if param_desc:
                    prompt += f" - {param_desc}"
                
                user_input = input(prompt).strip()
                
                # Handle empty input for optional parameters
                if not user_input and not is_required:
                    break
                
                if not user_input and is_required:
                    print("    Dieser Parameter ist erforderlich!")
                    continue
                
                try:
                    # Convert input to appropriate type
                    if param_type == "number":
                        args[param_name] = float(user_input)
                    elif param_type == "integer":
                        args[param_name] = int(user_input)
                    elif param_type == "boolean":
                        args[param_name] = user_input.lower() in ['true', '1', 'yes', 'ja']
                    else:
                        args[param_name] = user_input
                    break
                except ValueError:
                    print(f"    Ungültige Eingabe für Typ '{param_type}'. Bitte versuchen Sie es erneut.")
    
    print(f"\n🚀 Rufe Tool '{tool.name}' mit Parametern auf:")
    for key, value in args.items():
        print(f"  {key}: {value}")
    
    try:
        # Call the tool
        result = await client.call_tool(tool.name, args)
        
        print("\n🎉 Erfolgreiche Antwort vom Server erhalten:")
        if hasattr(result, 'content') and result.content:
            for content in result.content:
                if hasattr(content, 'text'):
                    print(content.text)
                else:
                    print(content)
        else:
            print(result)
    
    except Exception as e:
        print(f"\n❌ Fehler beim Aufruf des Tools: {e}")


if __name__ == "__main__":
    print("🔧 FastMCP Client - Verbindung zum Server")
    print("=" * 50)
    asyncio.run(discover_and_call_tools())

