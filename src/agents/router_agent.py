# src/agents/router_agent.py - Quick fix for SystemMessage issue
"""
Router Agent - The main orchestrator for Steve Connect
Uses Gemini Pro for intelligent routing decisions
"""

import os
from typing import Dict, Any, Optional, List
from enum import Enum
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()

class AppType(str, Enum):
    """Available apps in Steve OS ecosystem"""
    IDEATION = "ideation"
    VIBE_STUDIO = "vibe_studio" 
    DESIGN = "design"
    GMAIL = "gmail"
    CHAT = "chat"

class RouterAgent:
    """
    Intelligent router agent using Gemini Pro for smart decision making
    """
    
    # Update all agents to use the newest Gemini model
# src/agents/router_agent.py
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",  # 🔧 Latest and greatest!
            temperature=0.2,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            convert_system_message_to_human=True
        )
    
    # ... rest of the code stays exactly the same
    async def route_message(self, 
                          user_message: str, 
                          conversation_history: List[Dict[str, str]] = None,
                          current_app: str = None,
                          context_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Intelligent routing using Gemini Pro
        """
        try:
            print(f"🤖 Router processing: {user_message}")
            print(f"📱 Current app: {current_app}")
            print(f"📜 Context: {context_data}")
            
            # Use AI to make intelligent routing decision
            routing_decision = await self._ai_routing_decision(
                user_message, 
                conversation_history or [], 
                current_app,
                context_data or {}
            )
            
            print(f"🎯 AI Decision: {routing_decision}")
            
            return routing_decision
            
        except Exception as e:
            print(f"❌ Router agent error: {e}")
            return {
                "response": "I'm here to help! What would you like to work on?",
                "action": "continue_chat", 
                "app_to_open": AppType.CHAT,
                "confidence": 0.0,
                "context_data": {}
            }
    
    async def _ai_routing_decision(self, user_message: str, conversation_history: List, current_app: str, context_data: Dict) -> Dict[str, Any]:
        """
        Use Gemini Pro to make intelligent routing decisions
        """
        try:
            # Build context about the conversation
            context_summary = self._build_context_summary(conversation_history, current_app, context_data)
            
            system_prompt = f"""
You are Steve, an intelligent AI assistant that helps users build apps through a 4-step workflow:
1. IDEATION: Brainstorm and plan app ideas
2. VIBE_STUDIO: Generate actual Streamlit code 
3. DESIGN: Create marketing images and visuals
4. GMAIL: Draft launch emails

CURRENT CONTEXT:
{context_summary}

ROUTING RULES:
- If user wants to "create", "build", "make" a NEW app → Route to IDEATION
- If user has completed ideation and wants to "build it", "start coding", "develop" → Route to VIBE_STUDIO  
- If user has an app and wants "marketing", "visuals", "images", "design" → Route to DESIGN
- If user wants to "launch", "email", "promote", "contact users" → Route to GMAIL
- If user is just chatting or asking questions → Continue conversation

USER MESSAGE: "{user_message}"

Respond with ONLY this JSON format:
{{
    "action": "open_app" or "continue_chat",
    "app_to_open": "ideation" or "vibe_studio" or "design" or "gmail" or "chat",
    "response": "Your helpful response to the user",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of your decision"
}}
"""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # Parse the AI response
            return self._parse_ai_response(response.content, user_message)
            
        except Exception as e:
            print(f"AI routing error: {e}")
            return self._fallback_response(user_message)
    
    def _build_context_summary(self, conversation_history: List, current_app: str, context_data: Dict) -> str:
        """
        Build a summary of the current conversation context
        """
        summary_parts = []
        
        if current_app:
            summary_parts.append(f"Currently in: {current_app} app")
        
        if context_data.get("enhanced_knowledge"):
            summary_parts.append("Has relevant knowledge from previous interactions")
        
        # Check if user has completed previous steps
        workflow_status = []
        if "ideation" in str(context_data).lower():
            workflow_status.append("✅ Ideation completed")
        if "vibe_studio" in str(context_data).lower():
            workflow_status.append("✅ Code generated")
        if "design" in str(context_data).lower():
            workflow_status.append("✅ Visuals created")
        
        if workflow_status:
            summary_parts.append(f"Workflow progress: {', '.join(workflow_status)}")
        
        # Add recent conversation context
        if conversation_history:
            recent_messages = conversation_history[-3:]  # Last 3 messages
            summary_parts.append(f"Recent conversation: {recent_messages}")
        
        return " | ".join(summary_parts) if summary_parts else "New conversation"
    
    def _parse_ai_response(self, ai_response: str, user_message: str) -> Dict[str, Any]:
        """
        Parse the AI response and extract routing decision
        """
        try:
            # Try to extract JSON from the response
            import json
            import re
            
            # Look for JSON in the response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                response_data = json.loads(json_match.group())
                
                return {
                    "response": response_data.get("response", "Let me help you with that!"),
                    "action": response_data.get("action", "continue_chat"),
                    "app_to_open": response_data.get("app_to_open", "chat"),
                    "confidence": float(response_data.get("confidence", 0.8)),
                    "context_data": {"reasoning": response_data.get("reasoning", "")}
                }
            
            # Fallback if JSON parsing fails
            return self._fallback_response(user_message)
            
        except Exception as e:
            print(f"Error parsing AI response: {e}")
            return self._fallback_response(user_message)
    
    def _fallback_response(self, user_message: str) -> Dict[str, Any]:
        """
        Fallback routing when AI fails
        """
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ["create", "new", "idea", "build app"]):
            return {
                "response": "Great! Let me open the Ideation app to help you brainstorm your ideas. 🚀",
                "action": "open_app",
                "app_to_open": AppType.IDEATION,
                "confidence": 0.7,
                "context_data": {}
            }
        elif any(word in message_lower for word in ["build it", "start coding", "develop", "vibe studio"]):
            return {
                "response": "Perfect! Opening Vibe Studio to generate your app code. 💻",
                "action": "open_app", 
                "app_to_open": AppType.VIBE_STUDIO,
                "confidence": 0.7,
                "context_data": {}
            }
        elif any(word in message_lower for word in ["design", "image", "visual", "marketing"]):
            return {
                "response": "Excellent! Opening the Design app to create visuals. 🎨",
                "action": "open_app",
                "app_to_open": AppType.DESIGN,
                "confidence": 0.7,
                "context_data": {}
            }
        else:
            return {
                "response": "I'm here to help you create amazing apps! What would you like to work on?",
                "action": "continue_chat",
                "app_to_open": AppType.CHAT,
                "confidence": 0.5,
                "context_data": {}
            }