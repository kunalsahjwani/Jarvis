# test_mcp_connection.py - Windows-compatible MCP test
# import os
# import asyncio
# import shutil
# from dotenv import load_dotenv

# load_dotenv()

# async def test_mcp_gmail():
#     """Test MCP Gmail connection - Windows compatible"""
#     try:
#         print("Testing MCP Gmail connection...")
        
#         # Test 1: Find npx path
#         npx_path = shutil.which("npx")
#         print(f"npx path: {npx_path}")
        
#         if not npx_path:
#             print("npx not found in PATH")
#             return False
        
#         # Test 2: Try langchain-mcp-adapters import
#         from langchain_mcp_adapters.client import MultiServerMCPClient
#         print("MCP adapters imported successfully")
        
#         # Test 3: MCP config with full npx path
#         mcp_config = {
#             "gmail": {
#                 "command": npx_path,
#                 "transport": "stdio",
#                 "args": ["@peakmojo/mcp-server-headless-gmail"]
#             }
#         }
        
#         print("Creating MCP client...")
#         client = MultiServerMCPClient(mcp_config)
        
#         print("Getting tools (this may take a moment)...")
#         tools = await client.get_tools()
        
#         print(f"SUCCESS! MCP connected. Available tools: {[tool.name for tool in tools]}")
#         return True
        
#     except Exception as e:
#         print(f"MCP test failed: {e}")
#         print(f"Error type: {type(e)}")
#         import traceback
#         traceback.print_exc()
#         return False

# if __name__ == "__main__":
#     asyncio.run(test_mcp_gmail())