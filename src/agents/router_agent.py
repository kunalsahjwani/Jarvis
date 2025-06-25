# src/agents/router_agent.py - Fully AI-Driven Version that understands intent, USES A LOTTT of prompt engineering
"""
Router Agent - Fully AI-Driven with Minimal Hardcoding
Uses Gemini Pro for all routing decisions and intent understanding
"""

import os
from typing import Dict, Any, Optional, List
from enum import Enum
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from dotenv import load_dotenv
import json
import re

# Simple logging
from src.utils.logger import get_logger
logger = get_logger("router")

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
    Fully AI-driven intelligent router agent
    """
    
    def __init__(self):
        logger.info("Initializing Router Agent")
        
        try:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0.3,  # Slightly higher for more natural responses, can tweak and test
                google_api_key=os.getenv("GOOGLE_API_KEY"),
                convert_system_message_to_human=True
            )
            logger.info("Router Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Router Agent: {str(e)}")
            raise
        
        # Minimal hardcoded data - just app descriptions for AI context, basically letting our router know what each app does
        self.ecosystem_description = """
        Steve Connect Ecosystem:
        - IDEATION: Brainstorm and plan app concepts across any category
        - VIBE_STUDIO: Generate actual Streamlit code and applications  
        - DESIGN: Create marketing images, logos, and visual content
        - GMAIL: Draft launch emails and marketing campaigns
        
        Typical workflow: Ideation → Vibe Studio → Design → Gmail (but flexible based on user needs)
        """
        
        # Session-based context tracking (only for memory)
        self.session_contexts = {}
    
    async def route_message(self, 
                          user_message: str, 
                          conversation_history: List[Dict[str, str]] = None,
                          current_app: str = None,
                          context_data: Dict[str, Any] = None,
                          session_id: str = None) -> Dict[str, Any]:
        """
        Fully AI-driven routin
        """
        logger.info(f"Processing routing request: '{user_message[:50]}...'")
        
        try:
            # Initialize session context if needed
            if session_id and session_id not in self.session_contexts:
                self.session_contexts[session_id] = {}
            
            # Let AI handle everything - build comprehensive context
            full_context = self._build_ai_context(
                user_message, 
                conversation_history or [], 
                current_app, 
                context_data or {},
                session_id
            )
            
            # Single AI call handles all routing logic to make it easy
            routing_decision = await self._ai_comprehensive_routing(full_context)
            
            # Store any AI insights for next interaction so that i have context
            if session_id:
                self.session_contexts[session_id]["last_ai_decision"] = routing_decision
            
            logger.info(f"Routing decision: {routing_decision['action']} -> {routing_decision.get('app_to_open', 'chat')}")
            
            return routing_decision
            
        except Exception as e:
            logger.error(f"AI Router error: {str(e)}")
            # 
            return await self._ai_error_recovery(user_message, str(e))
    
    def _build_ai_context(self, user_message: str, conversation_history: List, 
                         current_app: str, context_data: Dict, session_id: str) -> Dict[str, Any]:
        """
        Build comprehensive context for AI to analyze
        """
        # Check for memory context in context_data
        memory_context = context_data.get('memory_context', {})
        has_memory_context = memory_context.get('has_context', False)
        
        return {
            "user_message": user_message,
            "conversation_history": conversation_history[-5:] if conversation_history else [],  # Last 5 for context
            "current_app": current_app,
            "context_data": context_data,
            "session_id": session_id,
            "ecosystem_info": self.ecosystem_description,
            "previous_ai_decision": self.session_contexts.get(session_id, {}).get("last_ai_decision"),
            "memory_context": memory_context
        }
    
    async def _ai_comprehensive_routing(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Single AI call that handles all routing intelligence
        """
        try:
            # Extract memory context summary for AI prompt
            memory_context = context.get('memory_context', {})
            memory_summary = ""
            if memory_context.get('has_context', False):
                memory_summary = f"\nRELEVANT USER HISTORY:\n{memory_context.get('context_summary', 'No summary available')}"
            
            system_prompt = f"""
You are Steve, an advanced AI assistant for the Steve Connect ecosystem. You have COMPLETE INTELLIGENCE to:

1. Understand user intent (no keyword matching - pure language understanding)
2. Track conversation context and workflow state
3. Make smart routing decisions
4. Generate natural, contextual responses
5. Handle confirmations, questions, and complex requests

ECOSYSTEM INFO:
{context['ecosystem_info']}

CURRENT SITUATION:
- User Message: "{context['user_message']}"
- Current App: {context['current_app']}
- Conversation History: {context['conversation_history']}
- App Data/Progress: {context['context_data']}
- Previous Decision: {context.get('previous_ai_decision')}
{memory_summary}

CRITICAL INTELLIGENCE RULES:
 Understanding "yes/ok/sure/lets move on" means user agrees with your last suggestion
 When user says ambiguous "yes" or "move on", use WORKFLOW LOGIC:
  - After Ideation completed → Open Vibe Studio
  - After Vibe Studio completed → Open Design app  
  - After Design completed → Open Gmail
 NEVER ask the same question repeatedly - if user is ambiguous, make smart default choice
 When user asks about "my idea/app" reference their specific app details from context
 BREAK REPETITIVE LOOPS - if you've asked a question 2+ times, just take action
 Default to NEXT WORKFLOW STEP when user confirms but is unclear

ANTI-PATTERNS TO AVOID:
 Asking "Would you like X or Y?" repeatedly when user already said "yes"
 Getting stuck in conversation loops
 Being indecisive when user gives clear intent to "move forward"
 Asking for clarification on obvious workflow progressions

ROUTING OPTIONS:
- "open_app" + app_name: Open specific app (ideation/vibe_studio/design/gmail)
- "continue_chat": Keep conversation going with helpful response

WORKFLOW INTELLIGENCE:
If user completed Vibe Studio and says "move on/yes/sure" → Default to Design app
If user completed Design and says "move on/yes/sure" → Default to Gmail  
If user completed Ideation and says "move on/yes/sure" → Default to Vibe Studio

RESPONSE FORMAT (JSON only):
{{
    "action": "open_app" | "continue_chat",
    "app_to_open": "ideation" | "vibe_studio" | "design" | "gmail" | "chat",
    "response": "Your intelligent, decisive response that takes action",
    "confidence": 0.0-1.0,
    "reasoning": "Your thought process - why you chose this action",
    "context_understanding": "What you understand about user's current situation"
}}
"""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Route this intelligently: {context['user_message']}")
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # Parse AI response
            return await self._parse_ai_response(response.content, context['user_message'])
            
        except Exception as e:
            logger.error(f"AI routing error: {str(e)}")
            return await self._ai_error_recovery(context['user_message'], str(e))
    
    async def _parse_ai_response(self, ai_response: str, user_message: str) -> Dict[str, Any]:
        """
        Parse AI response with error handling
        """
        try:
            # Extract JSON from AI response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                response_data = json.loads(json_match.group())
                
                # Validate required fields
                required_fields = ["action", "response"]
                if all(field in response_data for field in required_fields):
                    return {
                        "response": response_data["response"],
                        "action": response_data["action"],
                        "app_to_open": response_data.get("app_to_open", "chat"),
                        "confidence": float(response_data.get("confidence", 0.8)),
                        "context_data": {
                            "reasoning": response_data.get("reasoning", ""),
                            "ai_understanding": response_data.get("context_understanding", ""),
                            "method": "ai_driven"
                        }
                    }
            
            # If JSON parsing fails, try AI recovery
            return await self._ai_error_recovery(user_message, "JSON parsing failed")
            
        except json.JSONDecodeError as e:
            return await self._ai_error_recovery(user_message, f"JSON decode error: {e}")
        except Exception as e:
            return await self._ai_error_recovery(user_message, f"Parse error: {e}")
    
    async def _ai_error_recovery(self, user_message: str, error_details: str) -> Dict[str, Any]:
        """
        AI-driven error recovery instead of hardcoded fallbacks
        """
        logger.error(f"AI error recovery triggered: {error_details}")
        
        try:
            recovery_prompt = f"""
The main routing AI encountered an error: {error_details}

User message was: "{user_message}"

As backup AI, provide a helpful response and basic routing decision.
Be helpful and acknowledge you're here to assist with app creation.

Respond with simple JSON:
{{
    "response": "Helpful response to user",
    "action": "continue_chat",
    "app_to_open": "chat"
}}
"""
            
            messages = [
                SystemMessage(content=recovery_prompt),
                HumanMessage(content=user_message)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # Simple JSON extraction for recovery
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                recovery_data = json.loads(json_match.group())
                return {
                    "response": recovery_data.get("response", "I'm here to help! What would you like to work on?"),
                    "action": "continue_chat",
                    "app_to_open": "chat",
                    "confidence": 0.6,
                    "context_data": {"method": "ai_recovery", "error": error_details}
                }
            
        except Exception as recovery_error:
            logger.error(f"AI recovery also failed: {str(recovery_error)}")
        
        # Last resort fallback, hope this never happens lol!
        return {
            "response": "I'm Steve, your AI assistant! I'm here to help you create amazing apps. What would you like to build?",
            "action": "continue_chat",
            "app_to_open": "chat",
            "confidence": 0.5,
            "context_data": {"method": "emergency_fallback"}
        }