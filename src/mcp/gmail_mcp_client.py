# src/mcp/gmail_mcp_client.py
"""
MCP Gmail Client for Steve Connect - Enhanced with Automatic Token Refresh
Uses dedicated thread with Windows-compatible event loop for MCP operations
ENHANCED: Automatic token refresh - no more manual browser interactions!
"""

import os
import asyncio
import shutil
import concurrent.futures
import threading
import sys
import json
# CHANGE: Added new imports for automatic token refresh functionality
import requests
import time
from typing import Dict, Any, Optional
from langchain_mcp_adapters.client import MultiServerMCPClient
from dotenv import load_dotenv, set_key, find_dotenv  # CHANGE: Added set_key and find_dotenv for .env file updates

load_dotenv()

class GmailMCPClient:
    """
    Professional MCP client with automatic token refresh - NO MORE MANUAL STEPS!
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
            print(f"Gmail MCP Client initialized with automatic token refresh (npx: {self.npx_path})")
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
        
        # CHANGE: Added token management properties for automatic refresh
        self.token_refresh_url = "https://oauth2.googleapis.com/token"
        self.last_token_refresh = 0
        self.token_expiry_buffer = 300  # Refresh 5 minutes before expiry
        
        print(f"Gmail credentials loaded: {bool(self.gmail_credentials['google_access_token'])}")
        print("Automatic token refresh enabled - no more manual steps!")
    
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
        """Send email with automatic token refresh - NO MANUAL INTERVENTION NEEDED!"""
        if not self.is_connected:
            print("Not connected, attempting to connect...")
            connect_result = await self.connect()
            if not connect_result:
                return {"success": False, "error": "Failed to connect to MCP server"}
        
        # CHANGE: Modified to use new auto-refresh method instead of direct send
        if sys.platform == "win32":
            return await self._run_mcp_operation(
                self._send_email_with_auto_refresh, 
                recipient, subject, body, html_body
            )
        else:
            return await self._send_email_with_auto_refresh(recipient, subject, body, html_body)
    
    # CHANGE: NEW METHOD - Send email with automatic token refresh logic
    async def _send_email_with_auto_refresh(self, recipient: str, subject: str, body: str, html_body: str = None) -> Dict[str, Any]:
        """
        Send email with automatic token refresh logic - FULLY AUTOMATED!
        """
        max_retries = 2
        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1}: Sending email to {recipient}")
                
                # CHANGE: Added proactive token refresh check
                if self._should_refresh_token():
                    print("Proactively refreshing token...")
                    refresh_result = await self._refresh_access_token()
                    if not refresh_result["success"]:
                        print(f"Proactive token refresh failed: {refresh_result['error']}")
                        # Continue anyway, maybe the token is still valid
                
                # Try to send email
                result = await self._send_email_internal(recipient, subject, body, html_body)
                
                # If successful, return immediately
                if result["success"]:
                    print("Email sent successfully!")
                    return result
                
                # CHANGE: Added authentication error detection and auto-refresh
                error_msg = result.get("error", "").lower()
                if any(auth_error in error_msg for auth_error in ["401", "403", "unauthorized", "invalid_grant", "token", "auth"]):
                    print(f"Authentication error detected: {result['error']}")
                    
                    if attempt < max_retries - 1:  # Don't refresh on last attempt
                        print("Attempting automatic token refresh...")
                        refresh_result = await self._refresh_access_token()
                        
                        if refresh_result["success"]:
                            print("Token refreshed successfully! Retrying email send...")
                            # Update credentials for next attempt
                            continue
                        else:
                            print(f"Automatic token refresh failed: {refresh_result['error']}")
                            return {
                                "success": False,
                                "error": f"Authentication failed and token refresh failed: {refresh_result['error']}"
                            }
                    else:
                        return {
                            "success": False,
                            "error": f"Authentication failed after token refresh attempts: {result['error']}"
                        }
                else:
                    # Non-auth error, return immediately
                    return result
                    
            except Exception as e:
                print(f"Attempt {attempt + 1} failed with exception: {e}")
                if attempt == max_retries - 1:
                    return {"success": False, "error": f"All attempts failed: {str(e)}"}
        
        return {"success": False, "error": "All retry attempts exhausted"}
    
    # CHANGE: NEW METHOD - Check if we should proactively refresh the token
    def _should_refresh_token(self) -> bool:
        """
        Check if we should proactively refresh the token
        """
        # Refresh if we haven't refreshed in the last hour
        time_since_refresh = time.time() - self.last_token_refresh
        return time_since_refresh > 3000  # 50 minutes
    
    # CHANGE: NEW METHOD - Automatically refresh access token using refresh token
    async def _refresh_access_token(self) -> Dict[str, Any]:
        """
        Automatically refresh access token using refresh token - NO BROWSER NEEDED!
        """
        try:
            print("Starting automatic token refresh...")
            
            if not self.gmail_credentials["google_refresh_token"]:
                return {"success": False, "error": "No refresh token available"}
            
            # Prepare refresh request
            refresh_data = {
                "client_id": self.gmail_credentials["google_client_id"],
                "client_secret": self.gmail_credentials["google_client_secret"],
                "refresh_token": self.gmail_credentials["google_refresh_token"],
                "grant_type": "refresh_token"
            }
            
            print("Making token refresh request to Google...")
            
            # CHANGE: Make refresh request to Google's OAuth2 endpoint
            response = requests.post(
                self.token_refresh_url,
                data=refresh_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                new_access_token = token_data.get("access_token")
                
                if new_access_token:
                    print("New access token received!")
                    
                    # CHANGE: Update credentials in memory
                    self.gmail_credentials["google_access_token"] = new_access_token
                    self.last_token_refresh = time.time()
                    
                    # CHANGE: Update .env file automatically
                    env_path = find_dotenv()
                    if env_path:
                        set_key(env_path, "GOOGLE_ACCESS_TOKEN", new_access_token)
                        print("Updated .env file with new access token")
                    
                    # CHANGE: Update environment variable for current session
                    os.environ["GOOGLE_ACCESS_TOKEN"] = new_access_token
                    
                    print("Token refresh completed successfully - fully automated!")
                    return {
                        "success": True,
                        "new_access_token": new_access_token,
                        "method": "automatic_refresh"
                    }
                else:
                    return {"success": False, "error": "No access token in refresh response"}
            else:
                error_detail = response.text
                print(f"Token refresh failed: {response.status_code} - {error_detail}")
                
                # CHANGE: Check for specific error types to provide better error messages
                if "invalid_grant" in error_detail:
                    return {
                        "success": False,
                        "error": "Refresh token expired or invalid. Please re-run oauth.py setup.",
                        "requires_reauth": True
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Token refresh failed: {response.status_code} - {error_detail}"
                    }
                    
        except requests.RequestException as e:
            print(f"Network error during token refresh: {e}")
            return {"success": False, "error": f"Network error during token refresh: {str(e)}"}
        except Exception as e:
            print(f"Unexpected error during token refresh: {e}")
            return {"success": False, "error": f"Unexpected error during token refresh: {str(e)}"}
    
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
            # CHANGE: Use current access token (might be refreshed)
            current_access_token = self.gmail_credentials["google_access_token"]
            
            # Prepare email data in correct format for headless Gmail MCP server
            email_data = {
                "google_access_token": current_access_token,  # CHANGE: Use current token instead of original
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
    
    # CHANGE: Enhanced get_recent_emails method with automatic token refresh support
    async def get_recent_emails(self, max_results: int = 5) -> Dict[str, Any]:
        """Get recent emails with automatic token refresh"""
        if sys.platform == "win32":
            return await self._run_mcp_operation(self._get_recent_emails_internal, max_results)
        else:
            return await self._get_recent_emails_internal(max_results)
    
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