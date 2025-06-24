# src/agents/email_agent.py 
"""
Email Agent - Powers Gmail integration for Steve Connect
Generates marketing emails and launch campaigns based on app context
Uses Gemini Pro for intelligent email content generation
"""

import os
import re
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv
from src.agents.email_sender import EmailSender

load_dotenv()

class EmailAgent:
    """
    AI agent for generating marketing emails and launch campaigns
    """
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.4,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            convert_system_message_to_human=True
        )
        
        self.email_sender = EmailSender()
        print("EmailAgent initialized with mcp gmail integration")
    
    async def generate_launch_email(self, 
                                  app_context: Dict[str, Any], 
                                  target_audience: str = "general",
                                  email_type: str = "launch") -> Dict[str, Any]:
        """
        Generate a complete marketing email for app launch
        """
        try:
            app_name = app_context.get("app_name", "Your New App")
            app_category = app_context.get("app_category", "productivity")
            app_description = app_context.get("app_description", "An amazing application")
            
            print(f"Generating {email_type} email for {app_name}")
            
            # Generate email components using generate subject line and generate email body
            subject_line = await self._generate_subject_line(app_name, app_category, email_type)
            email_body = await self._generate_email_body(app_context, target_audience, email_type)
            
            # Compile the complete email qith the subject line
            complete_email = self._compile_email(subject_line, email_body, app_context)
            
            return {
                "success": True,
                "email_type": email_type,
                "subject_line": subject_line,
                "email_body": email_body,
                "complete_email": complete_email,
                "target_audience": target_audience,
                "app_context": app_name
            }
            
        except Exception as e:
            print(f"Error generating launch email: {e}")
            return {
                "success": False,
                "error": str(e),
                "app_name": app_context.get("app_name", "Unknown")
            }
                #generating subject line by using enhanced clean prompts
    async def _generate_subject_line(self, app_name: str, app_category: str, email_type: str) -> str:
        """
        Generate compelling subject line for the email
        """
        try:
            system_prompt = f"""
            You are an expert email marketer. Generate ONLY a compelling email subject line.
            
            App Details:
            - Name: {app_name}
            - Category: {app_category}
            - Email Type: {email_type}
            
            CRITICAL INSTRUCTIONS:
            - Return ONLY the subject line text, nothing else
            - NO explanatory text like "Here's a compelling subject line"
            - NO quotation marks
            - NO introductory phrases
            - Just the actual subject line that would appear in an email
            - Keep under 50 characters for mobile optimization
            - Make it action-oriented and benefit-focused
            - Create urgency or curiosity without being spammy
            - Avoid spam trigger words (FREE, URGENT, !!!)
            
            Example good responses:
            "Launch Your Dream App Today"
            "Stop Wasting Time - Try TaskMaster Now"
            "Your Perfect Workout Buddy is Here"
            
            Example BAD responses:
            "Here's a compelling subject line for your app:"
            "A good subject line would be:"
            """
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Generate subject line for {app_name} {email_type} email")
            ]
            
            response = await self.llm.ainvoke(messages)
            raw_subject = response.content.strip()
            
            # Clean up the response to get raw subject
            subject_line = self._clean_subject_line(raw_subject)
            
            # Ensure it's not too long, just a check so that it doesnt get messsy
            if len(subject_line) > 50:
                subject_line = subject_line[:47] + "..."
            
            # Final validation - if it still contains instructional text, use fallback, so that something gets generated
            if self._contains_instructional_text(subject_line):
                subject_line = f"Introducing {app_name}"
                if len(subject_line) > 50:
                    subject_line = f"Try {app_name} Today"
            
            return subject_line
            
        except Exception as e:
            print(f"Error generating subject line: {e}")
            return f"Introducing {app_name}"
    
    def _clean_subject_line(self, raw_subject: str) -> str:
        """
        Clean the subject line of any instructional text
        """
        # Remove common instructional phrases
        instructional_patterns = [
            r"here's?\s+a?\s+compelling\s+subject\s+line.*?:?\s*",
            r"a?\s+good\s+subject\s+line\s+would\s+be.*?:?\s*",
            r"subject\s+line.*?:?\s*",
            r"here's?\s+.*?:?\s*",
            r"^.*?:\s*",  # Remove anything before a colon
        ]
        
        cleaned = raw_subject
        for pattern in instructional_patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        
        # Remove quotes and extra whitespace (just some processing to display clean data)
        cleaned = cleaned.strip().replace('"', '').replace("'", "")
        
        # If multiple lines, take the first non-instructional line
        lines = cleaned.split('\n')
        for line in lines:
            line = line.strip()
            if line and not self._contains_instructional_text(line):
                cleaned = line
                break
        
        return cleaned
    
    def _contains_instructional_text(self, text: str) -> bool:
        """
        Check if text contains instructional phrases
        """
        instructional_words = [
            'here\'s', 'heres', 'compelling', 'subject line', 
            'good subject', 'would be', 'how about', 'try this',
            'example', 'suggestion', 'option'
        ]
        
        text_lower = text.lower()
        return any(word in text_lower for word in instructional_words)
    # email body function to generate the actual email body using system and user prompt
    async def _generate_email_body(self, app_context: Dict[str, Any], target_audience: str, email_type: str) -> str:
        """
        Generate the main email body content
        """
        try:
            app_name = app_context.get("app_name", "Your App")
            app_category = app_context.get("app_category", "productivity")
            app_description = app_context.get("app_description", "An amazing application")
            
            system_prompt = f"""
            Generate a compelling email body for a {email_type} email campaign.
            
            App Details:
            - Name: {app_name}
            - Category: {app_category}
            - Description: {app_description}
            - Target Audience: {target_audience}
            
            Email Structure:
            1. Personal greeting
            2. Hook - capture attention immediately
            3. Problem/Solution - what problem does the app solve?
            4. Key benefits (3-4 bullet points)
            5. Clear next steps
            6. Professional closing
            
            Writing Guidelines:
            - Use conversational, friendly tone
            - Keep paragraphs short (2-3 sentences max)
            - Focus on benefits, not just features
            - Make it scannable with bullet points
            - Keep total length under 200 words
            
            Generate engaging, persuasive email body content.
            """
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Create email body for {app_name} targeting {target_audience}")
            ]
            
            response = await self.llm.ainvoke(messages)
            return response.content.strip()
            
        except Exception as e:
            print(f"Error generating email body: {e}")
            return f"""
Hi there!

We're excited to introduce {app_context.get("app_name", "Your App")}, our new solution designed to make your life easier.

Ready to get started?

Best regards,
The Team
"""
    # compile email makes it look good when displaying, shows clean design of the email, have good alignment rather than plain text given by the llm
    def _compile_email(self, subject: str, body: str, app_context: Dict[str, Any]) -> str:
        """
        Compile the complete email with HTML formatting
        """
        app_name = app_context.get("app_name", "Your App")
        
        html_email = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    
    <!-- Header -->
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #2c3e50; margin-bottom: 10px;">{app_name}</h1>
        <hr style="border: none; height: 2px; background: linear-gradient(to right, #3498db, #2ecc71); margin: 20px 0;">
    </div>
    
    <!-- Main Content -->
    <div style="background: #f8f9fa; padding: 30px; border-radius: 10px; margin-bottom: 30px;">
        {self._format_email_body(body)}
    </div>
    
    <!-- Footer -->
    <div style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 14px;">
        <p>Thanks for your interest in {app_name}!</p>
        <p style="margin-top: 20px;">
            <a href="#" style="color: #3498db; text-decoration: none;">Unsubscribe</a> | 
            <a href="#" style="color: #3498db; text-decoration: none;">Update Preferences</a>
        </p>
        <p style="margin-top: 15px; font-size: 12px; color: #999;">
            Generated by Steve Connect | © 2024
        </p>
    </div>
    
</body>
</html>
"""
        
        return html_email
    
    def _format_email_body(self, body: str) -> str:
        """
        Format email body with HTML styling
        """
        # Convert line breaks to HTML
        formatted_body = body.replace('\n\n', '</p><p style="margin-bottom: 15px;">')
        formatted_body = formatted_body.replace('\n', '<br>')
        
        # Wrap in paragraph tags
        formatted_body = f'<p style="margin-bottom: 15px;">{formatted_body}</p>'
        
        # Style bullet points if present
        formatted_body = re.sub(r'• (.*?)(?=<br>|</p>)', r'<li style="margin-bottom: 8px;">\1</li>', formatted_body)
        if '<li' in formatted_body:
            formatted_body = f'<ul style="padding-left: 20px;">{formatted_body}</ul>'
        
        return formatted_body