# src/mcp/gmail_mcp_client.py
"""
MCP Gmail Client for Steve Connect - Final Working Version
Uses dedicated thread with Windows-compatible event loop for MCP operations
Safe approach that doesn't affect other parts of the application
"""

import os
import asyncio
import shutil
import concurrent.futures
import threading
import sys
import json
from typing import Dict, Any, Optional
from langchain_mcp_adapters.client import MultiServerMCPClient
from dotenv import load_dotenv

load_dotenv()

class GmailMCPClient:
    """
    Professional MCP client with isolated Windows-compatible event loop
    """
    
    def __init__(self):
        self.client = None
        self.is_connected = False
        
        # Find npx path
        self.npx_path = shutil.which("npx")
        
        # Create dedicated thread pool for MCP operations (max 1 worker for simplicity)
        self.mcp_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=1, 
            thread_name_prefix="mcp_gmail"
        )
        
        # MCP server configuration
        if self.npx_path:
            self.mcp_config = {
                "gmail": {
                    "command": self.npx_path,
                    "args": ["@peakmojo/mcp-server-headless-gmail"],
                    "transport": "stdio"
                }
            }
            print(f"Gmail MCP Client initialized with isolated event loop (npx: {self.npx_path})")
        else:
            print("Warning: npx not found, MCP will fail")
            self.mcp_config = {}
        
        # Gmail credentials from environment
        self.gmail_credentials = {
            "google_client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "google_client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "google_access_token": os.getenv("GOOGLE_ACCESS_TOKEN"),
            "google_refresh_token": os.getenv("GOOGLE_REFRESH_TOKEN")
        }
        
        print(f"Gmail credentials loaded: {bool(self.gmail_credentials['google_access_token'])}")
    
    def __del__(self):
        """Cleanup thread pool on destruction"""
        if hasattr(self, 'mcp_executor'):
            self.mcp_executor.shutdown(wait=False)
    
    async def connect(self) -> bool:
        """Connect using isolated event loop for Windows compatibility"""
        if sys.platform == "win32":
            print("Using isolated Windows-compatible event loop for MCP connection...")
            return await self._run_mcp_operation(self._connect_internal)
        else:
            print("Using direct connection on non-Windows platform...")
            return await self._connect_internal()
    
    async def send_email(self, recipient: str, subject: str, body: str, html_body: str = None) -> Dict[str, Any]:
        """Send email using isolated event loop"""
        if not self.is_connected:
            print("Not connected, attempting to connect...")
            connect_result = await self.connect()
            if not connect_result:
                return {"success": False, "error": "Failed to connect to MCP server"}
        
        if sys.platform == "win32":
            return await self._run_mcp_operation(
                self._send_email_internal, 
                recipient, subject, body, html_body
            )
        else:
            return await self._send_email_internal(recipient, subject, body, html_body)
    
    async def refresh_token(self) -> Dict[str, Any]:
        """Refresh Gmail access token using isolated event loop"""
        if sys.platform == "win32":
            return await self._run_mcp_operation(self._refresh_token_internal)
        else:
            return await self._refresh_token_internal()
    
    async def get_recent_emails(self, max_results: int = 5) -> Dict[str, Any]:
        """Get recent emails using isolated event loop"""
        if sys.platform == "win32":
            return await self._run_mcp_operation(self._get_recent_emails_internal, max_results)
        else:
            return await self._get_recent_emails_internal(max_results)
    
    async def _run_mcp_operation(self, operation, *args):
        """
        Run MCP operation in isolated thread with Windows-compatible event loop
        This prevents Windows subprocess issues from affecting the main FastAPI event loop
        """
        def run_in_thread():
            # Create new event loop for this thread
            if sys.platform == "win32":
                # Use ProactorEventLoop for Windows subprocess support
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                print(f"Created isolated event loop: {loop.__class__.__name__}")
            else:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            try:
                # Run the MCP operation in the isolated event loop
                return loop.run_until_complete(operation(*args))
            except Exception as e:
                print(f"Error in isolated MCP operation: {e}")
                import traceback
                traceback.print_exc()
                raise
            finally:
                # Clean up the event loop
                loop.close()
        
        # Run in thread pool to avoid affecting main event loop
        try:
            future = self.mcp_executor.submit(run_in_thread)
            # Wait for the result with a timeout
            return await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: future.result(timeout=30)  # 30 second timeout
            )
        except concurrent.futures.TimeoutError:
            return {"success": False, "error": "MCP operation timed out"}
        except Exception as e:
            return {"success": False, "error": f"MCP operation failed: {str(e)}"}
    
    async def _connect_internal(self) -> bool:
        """Internal connection method - runs in isolated event loop"""
        try:
            if not self.npx_path:
                print("Cannot connect: npx not found")
                return False
            
            # Validate credentials before connecting
            if not self.gmail_credentials["google_access_token"]:
                print("Error: Missing GOOGLE_ACCESS_TOKEN in environment variables")
                return False
            
            print("Connecting to MCP Gmail server...")
            print(f"Using config: {self.mcp_config}")
            
            self.client = MultiServerMCPClient(self.mcp_config)
            
            # Get available tools to test connection
            print("Fetching available tools...")
            tools = await self.client.get_tools()
            tool_names = [tool.name for tool in tools]
            print(f"MCP connected! Available tools: {tool_names}")
            
            # Verify gmail_send_email tool exists
            if "gmail_send_email" not in tool_names:
                print(f"Warning: gmail_send_email tool not found in: {tool_names}")
                return False
            
            self.is_connected = True
            return True
            
        except Exception as e:
            print(f"MCP connection failed: {e}")
            print(f"Error type: {type(e)}")
            import traceback
            traceback.print_exc()
            self.is_connected = False
            return False
    
    async def _send_email_internal(self, recipient: str, subject: str, body: str, html_body: str = None) -> Dict[str, Any]:
        """Internal send email method - runs in isolated event loop"""
        try:
            # Prepare email data in correct format for headless Gmail MCP server
            email_data = {
                "google_access_token": self.gmail_credentials["google_access_token"],
                "to": recipient,
                "subject": subject,
                "body": body
            }
            
            # Add HTML body if provided
            if html_body:
                email_data["html_body"] = html_body
            
            print(f"Email data prepared: to={recipient}, subject={subject}")
            
            # Get tools and find the exact gmail_send_email tool
            tools = await self.client.get_tools()
            send_tool = None
            
            for tool in tools:
                if tool.name == "gmail_send_email":
                    send_tool = tool
                    break
            
            if not send_tool:
                available_tools = [tool.name for tool in tools]
                return {
                    "success": False, 
                    "error": f"gmail_send_email tool not found. Available tools: {available_tools}"
                }
            
            # Send the email using the correct tool
            print(f"Invoking {send_tool.name} with email data...")
            result = await send_tool.ainvoke(email_data)
            
            print(f"MCP tool result: {result}")
            
            # Parse JSON string response if needed
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                    print(f"Parsed JSON result: {result}")
                except json.JSONDecodeError:
                    return {"success": False, "error": f"Invalid JSON response: {result}"}
            
            # Check for error in parsed result
            if isinstance(result, dict) and "error" in result:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error from Gmail API"),
                    "details": result.get("details", "")
                }
            
            # Check if result indicates explicit failure
            if isinstance(result, dict) and result.get("success") is False:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error from MCP tool")
                }
            
            # Success case - Gmail API returns messageId, not message_id
            return {
                "success": True,
                "message_id": result.get("messageId", result.get("message_id", "mcp_sent")),
                "thread_id": result.get("threadId"),
                "label_ids": result.get("labelIds", []),
                "recipient": recipient,
                "subject": subject,
                "mcp_tool": send_tool.name,
                "mcp_result": result
            }
            
        except Exception as e:
            print(f"MCP email send error: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    async def _refresh_token_internal(self) -> Dict[str, Any]:
        """Internal refresh token method - runs in isolated event loop"""
        try:
            # Get tools and find refresh token tool
            tools = await self.client.get_tools()
            refresh_tool = None
            
            for tool in tools:
                if tool.name == "gmail_refresh_token":
                    refresh_tool = tool
                    break
            
            if not refresh_tool:
                return {"success": False, "error": "gmail_refresh_token tool not found"}
            
            # Prepare refresh data
            refresh_data = {
                "google_refresh_token": self.gmail_credentials["google_refresh_token"],
                "google_client_id": self.gmail_credentials["google_client_id"],
                "google_client_secret": self.gmail_credentials["google_client_secret"]
            }
            
            # Call refresh token tool
            result = await refresh_tool.ainvoke(refresh_data)
            
            # Parse JSON if needed
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    return {"success": False, "error": f"Invalid JSON response: {result}"}
            
            # Update stored access token if successful
            if isinstance(result, dict) and "access_token" in result:
                self.gmail_credentials["google_access_token"] = result["access_token"]
                print("Access token refreshed successfully")
                return {"success": True, "new_token": result["access_token"]}
            
            return {"success": False, "error": "Token refresh failed", "result": result}
            
        except Exception as e:
            print(f"Token refresh error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_recent_emails_internal(self, max_results: int = 5) -> Dict[str, Any]:
        """Internal get recent emails method - runs in isolated event loop"""
        try:
            tools = await self.client.get_tools()
            get_emails_tool = None
            
            for tool in tools:
                if tool.name == "gmail_get_recent_emails":
                    get_emails_tool = tool
                    break
            
            if not get_emails_tool:
                return {"success": False, "error": "gmail_get_recent_emails tool not found"}
            
            # Get recent emails
            email_data = {
                "google_access_token": self.gmail_credentials["google_access_token"],
                "max_results": max_results,
                "unread_only": False
            }
            
            result = await get_emails_tool.ainvoke(email_data)
            
            # Parse JSON if needed
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    return {"success": False, "error": f"Invalid JSON response: {result}"}
            
            return {"success": True, "emails": result}
            
        except Exception as e:
            print(f"Get emails error: {e}")
            return {"success": False, "error": str(e)}