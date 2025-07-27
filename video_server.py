import uvicorn
from fastapi import FastAPI
from langchain_mcp_adapters.server import MCPServer, ToolRegistry
import mcp_tools
import os

# --- Tool Registration ---
# Create a registry and add the functions from your tools file.
# The registry will automatically create tool definitions from the function signatures.
registry = ToolRegistry()
registry.register_tool(mcp_tools.trim_video)
registry.register_tool(mcp_tools.change_speed)
registry.register_tool(mcp_tools.add_text_overlay)
registry.register_tool(mcp_tools.crop_video)


# --- Server Setup ---
# Create a FastAPI app, which will be used to host the MCP server.
app = FastAPI(
    title="Video Editing Tool Server",
    description="A server that exposes video editing tools via the Multi-Component Protocol (MCP).",
    version="0.1.0",
)

# Create the MCP server instance with the tool registry.
mcp_server = MCPServer(registry)

# Mount the MCP server on the FastAPI app at the "/mcp" endpoint.
app.mount("/mcp", mcp_server.app)


# --- Main Execution ---
if __name__ == "__main__":
    print("Starting Video Editing Tool Server...")
    print("Available tools:")
    for tool_name, tool in registry.get_tools().items():
        print(f"- {tool_name}: {tool.description}")
    
    # Ensure output directories exist
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    if not os.path.exists("outputs"):
        os.makedirs("outputs")

    # Run the server on localhost, port 8001.
    uvicorn.run(app, host="0.0.0.0", port=8001)

