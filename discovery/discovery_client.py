# First, install the required libraries:
# pip install fastmcp google-generativeai python-dotenv

import asyncio
import os
import google.generativeai as genai
from dotenv import load_dotenv
from fastmcp import Client
import json
import threading
import queue
import time

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY not found in environment variables!")
    print("Please set your Gemini API key in one of these ways:")
    print("1. Create a .env file with: GEMINI_API_KEY=your_api_key_here")
    print("2. Set environment variable: set GEMINI_API_KEY=your_api_key_here")
    print("3. Get your API key from: https://makersuite.google.com/app/apikey")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)

# Define the server's SSE endpoint
SERVER_URL = "http://127.0.0.1:8000/sse"

class MCPToolExecutor:
    """Handles MCP tool execution in a separate thread to avoid async/sync conflicts."""
    
    def __init__(self):
        self.tool_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.running = False
        self.thread = None
        self.mcp_client = None
        
    def start(self):
        """Start the MCP tool executor thread."""
        self.running = True
        self.thread = threading.Thread(target=self._run_async_loop)
        self.thread.daemon = True
        self.thread.start()
        
    def stop(self):
        """Stop the MCP tool executor thread."""
        self.running = False
        if self.thread:
            self.thread.join()
            
    def _run_async_loop(self):
        """Run the async event loop in a separate thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self._async_main())
        finally:
            loop.close()
            
    async def _async_main(self):
        """Main async function that handles MCP tool calls."""
        try:
            self.mcp_client = Client(SERVER_URL)
            async with self.mcp_client:
                while self.running:
                    try:
                        # Get tool call from queue
                        tool_call = self.tool_queue.get(timeout=1.0)
                        if tool_call is None:  # Shutdown signal
                            break
                            
                        tool_name, kwargs = tool_call
                        
                        # Call the MCP tool
                        result = await self.mcp_client.call_tool(tool_name, kwargs)
                        
                        # Extract the result
                        if hasattr(result, 'content') and result.content:
                            for content in result.content:
                                if hasattr(content, 'text'):
                                    response_text = content.text
                                    self.result_queue.put(response_text)
                                    break
                        else:
                            self.result_queue.put(str(result))
                            
                    except queue.Empty:
                        continue
                    except Exception as e:
                        self.result_queue.put(f"Error: {e}")
                        
        except Exception as e:
            self.result_queue.put(f"Connection error: {e}")
            
    def call_tool(self, tool_name: str, **kwargs):
        """Call an MCP tool synchronously."""
        print(f"[Tool] Calling MCP tool '{tool_name}' with args: {kwargs}")
        
        # Put the tool call in the queue
        self.tool_queue.put((tool_name, kwargs))
        
        # Wait for the result
        try:
            result = self.result_queue.get(timeout=30)
            print(f"[Tool] MCP tool '{tool_name}' returned: {result}")
            return result
        except queue.Empty:
            return "Error: Tool call timed out"

# Global tool executor
tool_executor = MCPToolExecutor()

def create_tool_function(tool_name: str, tool_description: str, input_schema: dict = None):
    """Create a Gemini-compatible tool function with proper parameter definitions."""
    
    if input_schema and 'properties' in input_schema:
        # Create a function with actual parameters based on the schema
        properties = input_schema['properties']
        required_params = input_schema.get('required', [])
        
        # Build function signature dynamically
        param_names = list(properties.keys())
        
        # Create a function with the correct parameters
        def create_dynamic_function():
            # Create function code dynamically
            func_code = f"""
def {tool_name}({', '.join(param_names)}):
    \"\"\"{tool_description}\"\"\"
    return tool_executor.call_tool('{tool_name}', {', '.join([f'{name}={name}' for name in param_names])})
"""
            # Execute the function definition
            local_vars = {'tool_executor': tool_executor}
            exec(func_code, globals(), local_vars)
            return local_vars[tool_name]
        
        return create_dynamic_function()
    else:
        # Fallback for tools without schema
        def tool_wrapper(**kwargs):
            """Wrapper function that calls the MCP tool."""
            return tool_executor.call_tool(tool_name, **kwargs)
        
        tool_wrapper.__name__ = tool_name
        tool_wrapper.__doc__ = tool_description
        return tool_wrapper

async def discover_mcp_tools():
    """
    Connects to the FastMCP server and discovers available tools.
    """
    print(f"🔗 Connecting to FastMCP Server: {SERVER_URL}")
    
    try:
        # Create client and connect to the server
        client = Client(SERVER_URL)
        
        async with client:
            print("✅ Successfully connected to the server!")
            
            # List available tools
            mcp_tools = await client.list_tools()
            
            if not mcp_tools:
                print("⚠️ No tools found on the server.")
                return []
            
            print(f"\n✅ Found {len(mcp_tools)} MCP tools:")
            tools = []
            for tool in mcp_tools:
                print(f"  • {tool.name}")
                if tool.description:
                    print(f"    Description: {tool.description}")
                if tool.inputSchema and tool.inputSchema.get('properties'):
                    params = list(tool.inputSchema['properties'].keys())
                    print(f"    Parameters: {params}")
                print()
                
                tools.append({
                    'name': tool.name,
                    'description': tool.description or f"MCP tool: {tool.name}",
                    'inputSchema': tool.inputSchema
                })
            
            return tools
    
    except Exception as e:
        print(f"❌ Error connecting to MCP server: {e}")
        print("Make sure the server is running: python fastmcp_server.py")
        return []


async def run_mcp_demo():
    """
    Main demo function that asks for a single string and processes it with Gemini + MCP tools.
    """
    print("🔧 MCP Demo - Gemini + FastMCP Integration")
    print("=" * 60)
    
    # Start the tool executor
    tool_executor.start()
    
    try:
        # Discover MCP tools
        tools = await discover_mcp_tools()
        
        if not tools:
            print("❌ Could not discover MCP tools. Exiting.")
            return
        
        # Create tool functions for Gemini
        gemini_tools = []
        for tool_info in tools:
            print(f"🔧 Creating function for tool: {tool_info['name']}")
            if tool_info.get('inputSchema') and 'properties' in tool_info['inputSchema']:
                params = list(tool_info['inputSchema']['properties'].keys())
                print(f"   Parameters: {params}")
            
            tool_function = create_tool_function(
                tool_info['name'], 
                tool_info['description'],
                tool_info.get('inputSchema')
            )
            gemini_tools.append(tool_function)
        
        # Set up Gemini model
        print("🤖 Setting up Gemini with MCP tools...")
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            tools=gemini_tools
        )
        
        # Get user input
        print("\n" + "=" * 60)
        print("📝 Please enter your request or question:")
        print("   (This will be processed by Gemini using the available MCP tools)")
        print("=" * 60)
        
        user_input = input("\n👤 Your request: ").strip()
        
        if not user_input:
            print("❌ No input provided. Exiting.")
            return
        
        print(f"\n🚀 Processing your request: '{user_input}'")
        print("-" * 60)
        
        # Process with Gemini using chat session for better function call handling
        print("🤖 Gemini is thinking and may use MCP tools...")
        chat = model.start_chat(enable_automatic_function_calling=True)
        response = chat.send_message(user_input)
        
        print("\n🎉 Response from Gemini:")
        print("=" * 60)
        print(response.text)
        print("=" * 60)
        
        # Show what tools were used (simplified for chat session)
        print("\n💡 Note: If MCP tools were used, you would see their results in the response above.")
        
        print("\n✅ Demo completed successfully!")
    
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")

    finally:
        # Stop the tool executor
        tool_executor.stop()

if __name__ == "__main__":
    asyncio.run(run_mcp_demo())

