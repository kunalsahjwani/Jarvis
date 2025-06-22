# src/agents/email_sender.py
"""
Email Sender - Now with working MCP Gmail Integration
"""

import os
import shutil
from typing import Dict, Any, Optional
from src.mcp.gmail_mcp_client import GmailMCPClient
from dotenv import load_dotenv

load_dotenv()

class EmailSender:
    """
    Email sender with MCP Gmail integration - Windows compatible
    """
    
    def __init__(self):
        # Check if npx is available
        self.npx_path = shutil.which("npx")
        if self.npx_path:
            self.mcp_client = GmailMCPClient()
            print(f"EmailSender initialized with MCP Gmail integration (npx: {self.npx_path})")
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
        Send email via MCP Gmail integration
        """
        try:
            # Validation first
            if not self._validate_email_data(recipient_email, subject, email_body):
                return {"success": False, "error": "Invalid email data"}
            
            if not self.mcp_client:
                return {"success": False, "error": "MCP not available (npx not found)"}
            
            print(f"Sending email via MCP: {subject} to {recipient_email}")
            
            # Send via MCP Gmail client
            result = await self.mcp_client.send_email(
                recipient=recipient_email,
                subject=subject,
                body=email_body,
                html_body=email_body  # Assuming HTML format
            )
            
            if result["success"]:
                print(f"Email sent successfully via MCP!")
                return {
                    "success": True,
                    "message_id": result["message_id"],
                    "recipient": recipient_email,
                    "subject": subject,
                    "method": "mcp_gmail",
                    "mcp_tool": result.get("mcp_tool", "gmail_send_email")
                }
            else:
                print(f"MCP email send failed: {result.get('error')}")
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