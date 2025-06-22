# src/agents/email_agent.py - Simplified without emojis
"""
Email Agent - Powers Gmail integration for Steve Connect
Generates marketing emails and launch campaigns based on app context
Uses Gemini Pro for intelligent email content generation
"""

import os
import re
from typing import Dict, Any, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv
from datetime import datetime


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
        
        # Email templates and structures
        self.email_types = {
            "launch": "Product launch announcement",
            "update": "Feature update notification", 
            "promotion": "Promotional campaign",
            "newsletter": "Regular newsletter",
            "welcome": "Welcome new users",
            "feedback": "Request user feedback"
        }
    
    async def generate_launch_email(self, 
                                  app_context: Dict[str, Any], 
                                  target_audience: str = "general",
                                  email_type: str = "launch") -> Dict[str, Any]:
        """
        Generate a complete marketing email for app launch
        """
        try:
            # Extract context from the full app development workflow
            app_name = app_context.get("app_name", "Your New App")
            app_category = app_context.get("app_category", "productivity")
            app_description = app_context.get("app_description", "An amazing application")
            
            # Get context from previous apps in the workflow
            ideation_context = app_context.get("ideation_data", {})
            vibe_studio_context = app_context.get("vibe_studio_data", {})
            design_context = app_context.get("design_data", {})
            
            print(f"Generating {email_type} email for {app_name}")
            
            # Generate email components
            subject_line = await self._generate_subject_line(app_name, app_category, email_type)
            email_body = await self._generate_email_body(app_context, target_audience, email_type)
            call_to_action = await self._generate_cta(app_name, app_category, email_type)
            
            # Compile the complete email
            complete_email = self._compile_email(subject_line, email_body, call_to_action, app_context)
            
            return {
                "success": True,
                "email_type": email_type,
                "subject_line": subject_line,
                "email_body": email_body,
                "call_to_action": call_to_action,
                "complete_email": complete_email,
                "target_audience": target_audience,
                "app_context": app_name,
                "email_metrics": self._predict_email_metrics(subject_line, email_body),
                "send_recommendations": self._get_send_recommendations(email_type, target_audience)
            }
            
        except Exception as e:
            print(f"Error generating launch email: {e}")
            return {
                "success": False,
                "error": str(e),
                "app_name": app_context.get("app_name", "Unknown")
            }
    
    async def _generate_subject_line(self, app_name: str, app_category: str, email_type: str) -> str:
        """
        Generate compelling subject line for the email
        """
        try:
            system_prompt = f"""
            Generate a compelling email subject line for a {email_type} email.
            
            App Details:
            - Name: {app_name}
            - Category: {app_category}
            - Email Type: {email_type}
            
            Subject Line Guidelines:
            1. Keep it under 50 characters for mobile optimization
            2. Create urgency or curiosity without being spammy
            3. Include the app name if it fits naturally
            4. Make it action-oriented and benefit-focused
            5. Avoid spam trigger words (FREE, URGENT, !!!)
            6. Be specific and clear about the value proposition
            
            Generate 1 optimal subject line that maximizes open rates.
            """
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Create subject line for {app_name} {email_type} email")
            ]
            
            response = await self.llm.ainvoke(messages)
            subject_line = response.content.strip().replace('"', '')
            
            # Ensure it's not too long
            if len(subject_line) > 50:
                subject_line = subject_line[:47] + "..."
            
            return subject_line
            
        except Exception as e:
            print(f"Error generating subject line: {e}")
            return f"Introducing {app_name} - Your New {app_category.title()} Solution"
    
    async def _generate_email_body(self, app_context: Dict[str, Any], target_audience: str, email_type: str) -> str:
        """
        Generate the main email body content
        """
        try:
            app_name = app_context.get("app_name", "Your App")
            app_category = app_context.get("app_category", "productivity")
            app_description = app_context.get("app_description", "An amazing application")
            
            # Build context from the workflow
            workflow_context = self._build_email_context(app_context)
            
            system_prompt = f"""
            Generate a compelling email body for a {email_type} email campaign.
            
            App Details:
            - Name: {app_name}
            - Category: {app_category}
            - Description: {app_description}
            - Target Audience: {target_audience}
            
            Workflow Context:
            {workflow_context}
            
            Email Structure:
            1. Personal greeting
            2. Hook - capture attention immediately
            3. Problem/Solution - what problem does the app solve?
            4. Key benefits (3-4 bullet points)
            5. Social proof or credibility (if applicable)
            6. Clear next steps
            7. Professional closing
            
            Writing Guidelines:
            - Use conversational, friendly tone
            - Keep paragraphs short (2-3 sentences max)
            - Focus on benefits, not just features
            - Include emotional triggers appropriate for {target_audience}
            - Make it scannable with bullet points
            - Avoid jargon unless technical audience
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
            return self._get_fallback_email_body(app_context)
    
    async def _generate_cta(self, app_name: str, app_category: str, email_type: str) -> str:
        """
        Generate compelling call-to-action
        """
        try:
            system_prompt = f"""
            Generate a compelling call-to-action (CTA) for a {email_type} email.
            
            App: {app_name} ({app_category})
            Email Type: {email_type}
            
            CTA Guidelines:
            1. Use action verbs (Try, Get, Start, Discover, etc.)
            2. Create urgency without being pushy
            3. Be specific about what happens next
            4. Keep it under 5 words if possible
            5. Make it benefit-focused
            6. Match the email type and audience
            
            Generate 1 optimal CTA button text.
            """
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Create CTA for {app_name} {email_type}")
            ]
            
            response = await self.llm.ainvoke(messages)
            return response.content.strip().replace('"', '')
            
        except Exception as e:
            print(f"Error generating CTA: {e}")
            cta_options = {
                "launch": "Try It Now",
                "update": "Explore Updates", 
                "promotion": "Get Started",
                "newsletter": "Learn More",
                "welcome": "Start Now",
                "feedback": "Share Feedback"
            }
            return cta_options.get(email_type, "Get Started")
    
    def _build_email_context(self, app_context: Dict[str, Any]) -> str:
        """
        Build context string from the app development workflow
        """
        try:
            context_parts = []
            
            # Ideation context
            if "ideation_data" in app_context:
                ideation = app_context["ideation_data"]
                if isinstance(ideation, dict):
                    category = ideation.get("category", "")
                    description = ideation.get("description", "")
                    context_parts.append(f"Original Idea: {category} - {description}")
                else:
                    context_parts.append(f"Original Idea: {ideation}")
            
            # Vibe Studio context (app development)
            if "vibe_studio_data" in app_context:
                vibe_data = app_context["vibe_studio_data"]
                context_parts.append(f"App Features: Built with modern technology stack")
                if isinstance(vibe_data, dict):
                    features = vibe_data.get("features", [])
                    if features:
                        context_parts.append(f"Key Features: {', '.join(features[:3])}")
            
            # Design context (marketing materials)
            if "design_data" in app_context:
                design_data = app_context["design_data"]
                context_parts.append("Professional marketing materials created")
                if isinstance(design_data, dict):
                    style = design_data.get("style", "")
                    if style:
                        context_parts.append(f"Visual Style: {style}")
            
            return " | ".join(context_parts) if context_parts else "New innovative application ready for launch"
            
        except Exception as e:
            print(f"Error building email context: {e}")
            return "Exciting new application ready for launch"
    
    def _compile_email(self, subject: str, body: str, cta: str, app_context: Dict[str, Any]) -> str:
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
    
    <!-- Call to Action -->
    <div style="text-align: center; margin: 30px 0;">
        <a href="#" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; font-size: 16px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">{cta}</a>
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
        formatted_body = body.replace('\n', '<br>')
        
        # Wrap in paragraph tags
        formatted_body = f'<p style="margin-bottom: 15px;">{formatted_body}</p>'
        
        # Style bullet points if present
        formatted_body = re.sub(r'• (.*?)(?=<br>|</p>)', r'<li style="margin-bottom: 8px;">\1</li>', formatted_body)
        if '<li' in formatted_body:
            formatted_body = f'<ul style="padding-left: 20px;">{formatted_body}</ul>'
        
        return formatted_body
    
    def _predict_email_metrics(self, subject: str, body: str) -> Dict[str, Any]:
        """
        Predict email performance metrics based on content analysis
        """
        # Simple heuristic-based predictions
        subject_length = len(subject)
        body_length = len(body)
        
        # Predict open rate based on subject line
        if 20 <= subject_length <= 50:
            predicted_open_rate = "22-28%"
        elif subject_length < 20:
            predicted_open_rate = "18-24%"
        else:
            predicted_open_rate = "15-22%"
        
        # Predict click rate based on body length and CTA presence
        if 100 <= body_length <= 200:
            predicted_click_rate = "3-5%"
        elif body_length < 100:
            predicted_click_rate = "2-4%"
        else:
            predicted_click_rate = "1-3%"
        
        return {
            "predicted_open_rate": predicted_open_rate,
            "predicted_click_rate": predicted_click_rate,
            "subject_length": subject_length,
            "body_length": body_length,
            "mobile_optimized": subject_length <= 50,
            "spam_score": "Low" if not any(word in subject.upper() for word in ["FREE", "URGENT", "!!!"]) else "Medium"
        }
    
    def _get_send_recommendations(self, email_type: str, target_audience: str) -> List[str]:
        """
        Get recommendations for when and how to send the email
        """
        base_recommendations = [
            "Best send time: Tuesday-Thursday, 10 AM - 2 PM",
            "Ensure mobile optimization (60% of emails opened on mobile)",
            "A/B test subject lines with small segments first",
            "Monitor open rates and click-through rates",
        ]
        
        type_specific = {
            "launch": [
                "Send launch sequence: Teaser → Launch → Follow-up",
                "Consider social media coordination",
                "Segment audience by engagement level"
            ],
            "update": [
                "Highlight most impactful new features",
                "Include screenshots or GIFs of changes",
                "Ask for user feedback"
            ],
            "promotion": [
                "Create urgency with limited-time offers",
                "Highlight exclusive benefits for subscribers",
                "Include clear terms and conditions"
            ]
        }
        
        return base_recommendations + type_specific.get(email_type, [])
    
    def _get_fallback_email_body(self, app_context: Dict[str, Any]) -> str:
        """
        Fallback email body if generation fails
        """
        app_name = app_context.get("app_name", "Your App")
        app_category = app_context.get("app_category", "productivity")
        
        return f"""
Hi there!

We're excited to introduce {app_name}, our new {app_category} solution that's designed to make your life easier.

Key benefits:
- Intuitive and user-friendly interface
- Powerful features tailored for {app_category}
- Built with the latest technology
- Available on all your devices

We've put a lot of thought and care into creating something special, and we can't wait for you to try it.

Ready to get started?

Best regards,
The {app_name} Team
"""

    async def generate_email_variations(self, base_email: Dict[str, Any], variation_count: int = 3) -> List[Dict[str, Any]]:
        """
        Generate multiple variations of an email for A/B testing
        """
        variations = []
        
        try:
            for i in range(variation_count):
                # Generate variation with slightly different approach
                variation_prompt = f"Create variation {i+1} of the email with different tone/approach"
                # TODO: Implement variation generation logic
                
                variations.append({
                    "variation_id": f"v{i+1}",
                    "subject_line": base_email["subject_line"],  # TODO: Generate variations
                    "email_body": base_email["email_body"],      # TODO: Generate variations
                    "approach": f"Variation {i+1}"
                })
            
            return variations
            
        except Exception as e:
            print(f"Error generating email variations: {e}")
            return [base_email]