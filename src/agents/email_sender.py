# src/agents/email_sender.py
"""
Email Sender - Enhanced with Automatic Token Refresh Support
Works seamlessly with enhanced MCP Gmail client for fully automated email sending
uses mcp server from the famous marketplace glama
"""

import os
import shutil
from typing import Dict, Any, Optional
from src.mcp.gmail_mcp_client import GmailMCPClient
from dotenv import load_dotenv

load_dotenv()

class EmailSender:
    """
    Email sender with enhanced MCP Gmail integration
    """
    
    def __init__(self):
        # Check if npx is available
        self.npx_path = shutil.which("npx")
        if self.npx_path:
            self.mcp_client = GmailMCPClient()
            # CHANGE: Updated initialization message to reflect automatic token refresh
            print(f"EmailSender initialized with automatic token refresh (npx: {self.npx_path})")
            print("No more manual token management needed!")
        else:
            self.mcp_client = None
            print("EmailSender initialized - WARNING: npx not found, MCP disabled")
        
        self.is_connected = False
    
    async def send_email(self, 
                        recipient_email: str,
                        subject: str, 
                        email_body: str,
                        sender_name: str = "Steve Connect") -> Dict[str, Any]:
        """
        Send email via MCP Gmail integration with automatic token refresh
        """
        try:
            # Validation first
            if not self._validate_email_data(recipient_email, subject, email_body):
                return {"success": False, "error": "Invalid email data"}
            
            if not self.mcp_client:
                return {"success": False, "error": "MCP not available (npx not found)"}
            
            # CHANGE: Updated logging to reflect automatic token management, just using print statements for now
            print(f"Sending email: '{subject}' to {recipient_email}")
            print("Automatic token management enabled...")
            
            # Send via enhanced MCP Gmail client (handles token refresh automatically good for rate limits set by google to not use oauth.py again and again)
            result = await self.mcp_client.send_email(
                recipient=recipient_email,
                subject=subject,
                body=email_body,
                html_body=email_body  # Assuming HTML format
            )
            
            if result["success"]:
                print(f"Email sent successfully!")
                return {
                    "success": True,
                    "message_id": result["message_id"],
                    "recipient": recipient_email,
                    "subject": subject,
                    "method": "mcp_gmail_auto_refresh",
                    "mcp_tool": result.get("mcp_tool", "gmail_send_email")
                }
            else:
                print(f"Email send failed: {result.get('error')}")
                
                # handling for reauth requirement
                if result.get("requires_reauth"):
                    return {
                        "success": False,
                        "error": "Refresh token expired. Please re-run oauth.py to get new tokens.",
                        "requires_reauth": True
                    }
                else:
                    return result
            
        except Exception as e:
            print(f"Email sending error: {e}")
            return {
                "success": False,
                "error": str(e),
                "recipient": recipient_email
            }
    
    def _validate_email_data(self, recipient: str, subject: str, body: str) -> bool:
        """Validate email data before sending"""
        if not recipient or "@" not in recipient:
            return False
        if not subject or len(subject.strip()) == 0:
            return False
        if not body or len(body.strip()) == 0:
            return False
        return True
    
    # will use token status checking functionality
    async def check_token_status(self) -> Dict[str, Any]:
        """
        Check current token status and refresh if needed
        Useful for debugging or manual token management
        """
        if not self.mcp_client:
            return {"success": False, "error": "MCP client not available"}
        
        try:
            # will Try using simple operation to test token validity, to make everything work
            result = await self.mcp_client.get_recent_emails(max_results=1)
            
            if result["success"]:
                return {
                    "success": True,
                    "status": "Token is valid",
                    "last_refresh": getattr(self.mcp_client, 'last_token_refresh', 0)
                }
            else:
                return {
                    "success": False,
                    "status": "Token may be expired",
                    "error": result.get("error", "Unknown error")
                }
        except Exception as e:
            return {
                "success": False,
                "status": "Error checking token",
                "error": str(e)
            }