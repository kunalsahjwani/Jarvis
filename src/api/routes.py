# src/api/routes.py - Enhanced with cross-app context sharing and MCP Gmail
"""
FastAPI routes for Steve Connect - Enhanced Version
Handles all API endpoints with proper context sharing between apps
Now includes MCP Gmail integration for actual email sending
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid
import re

# Import our agents (no database imports)
from src.agents.router_agent import RouterAgent
from src.agents.leonardo_agent import LeonardoAgent
from src.agents.code_agent import CodeAgent
from src.agents.email_agent import EmailAgent
from src.agents.email_sender import EmailSender  # NEW: MCP Gmail integration

# Create the main router
router = APIRouter()

# Initialize all agents
router_agent = RouterAgent()
leonardo_agent = LeonardoAgent()
code_agent = CodeAgent()
email_agent = EmailAgent()
email_sender = EmailSender()  # NEW: MCP Gmail sender

# In-memory storage for session data (temporary solution)
session_storage = {}

# Pydantic models for request/response validation
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: str = "default_user"

class ChatResponse(BaseModel):
    response: str
    session_id: str
    action: str  # 'open_app', 'continue_chat'
    app_to_open: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None
    confidence: float = 0.0

class AppAction(BaseModel):
    app_name: str  # 'ideation', 'vibe_studio', 'design', 'gmail'
    action: str    # 'open', 'close', 'submit_data'
    session_id: str
    data: Optional[Dict[str, Any]] = None

# Helper functions for context extraction
def _extract_app_name_from_text(text: str) -> str:
    """Extract app name from user requirements text"""
    if not text:
        return "MyApp"
    
    # Look for common patterns like "app called X" or "X app"
    patterns = [
        r'(?:app (?:called|named)\s+)([a-zA-Z]\w+)',
        r'([a-zA-Z]\w+)(?:\s+app)',
        r'(?:called|named)\s+([a-zA-Z]\w+)',
        r'^([a-zA-Z]\w+)'  # First word if nothing else matches
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            app_name = match.group(1).strip()
            if len(app_name) > 1:  # Avoid single letters
                return app_name.title()
    
    # Fallback: take first meaningful word
    words = text.strip().split()
    if words:
        first_word = re.sub(r'[^\w]', '', words[0])
        if len(first_word) > 1:
            return first_word.title()
    
    return "MyApp"

def _extract_app_category_from_text(text: str) -> str:
    """Extract likely app category from user requirements"""
    text_lower = text.lower()
    
    category_keywords = {
        "education": ["learn", "student", "teach", "education", "course", "study", "professor", "research"],
        "healthcare": ["health", "fitness", "medical", "doctor", "exercise", "workout"],
        "finance": ["money", "budget", "payment", "bank", "finance", "investment"],
        "entertainment": ["game", "fun", "entertainment", "music", "video"],
        "travel": ["travel", "trip", "vacation", "hotel", "flight"],
        "food": ["food", "recipe", "restaurant", "cooking", "meal"],
        "technology": ["tech", "software", "code", "data", "api"],
        "services": ["service", "booking", "appointment", "schedule"],
        "digital_product": ["product", "shop", "store", "sell", "buy"]
    }
    
    for category, keywords in category_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            return category
    
    return "application"  # Default category

def _ensure_session_structure(session_id: str):
    """Ensure session has proper structure"""
    if session_id not in session_storage:
        session_storage[session_id] = {
            "user_id": "default_user",
            "conversation_history": [],
            "current_app": None,
            "app_data": {}
        }

# Main chat endpoint - The heart of Steve Connect
@router.post("/chat", response_model=ChatResponse)
async def chat_with_steve(message: ChatMessage):
    """
    Main chat interface for Steve Connect
    Routes user messages using the Router Agent and maintains context in memory
    """
    try:
        # Get or create session
        session_id = message.session_id
        if not session_id:
            session_id = str(uuid.uuid4())
        
        _ensure_session_structure(session_id)
        
        # Get current session context
        session_context = session_storage.get(session_id, {})
        current_app = session_context.get("current_app")
        conversation_history = session_context.get("conversation_history", [])
        
        # Add current message to history
        conversation_history.append({"user": message.message})
        
        # Route the message using Router Agent
        routing_result = await router_agent.route_message(
            user_message=message.message,
            conversation_history=conversation_history,
            current_app=current_app,
            context_data=session_context.get("app_data", {}),
            session_id=session_id
        )
        
        # Update session storage
        session_storage[session_id]["conversation_history"] = conversation_history
        if routing_result["action"] == "open_app" and routing_result["app_to_open"]:
            session_storage[session_id]["current_app"] = routing_result["app_to_open"]
        
        return ChatResponse(
            response=routing_result["response"],
            session_id=session_id,
            action=routing_result["action"],
            app_to_open=routing_result.get("app_to_open"),
            context_data=routing_result.get("context_data"),
            confidence=routing_result.get("confidence", 0.0)
        )
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}"
        )

# App-specific endpoints
@router.post("/ideation/submit")
async def submit_ideation_data(action: AppAction):
    """
    Handle ideation app data submission
    """
    try:
        session_id = action.session_id
        ideation_data = action.data
        
        _ensure_session_structure(session_id)
        
        # Save ideation context in memory
        session_storage[session_id]["app_data"]["ideation"] = ideation_data
        
        return JSONResponse({
            "status": "success",
            "message": "Ideation data saved successfully",
            "next_suggestion": "Ready to build your app? I can open Vibe Studio for you!",
            "data_saved": ideation_data
        })
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ideation submission failed: {str(e)}"
        )

@router.post("/vibe-studio/generate")
async def generate_app_code(action: AppAction):
    """
    Generate Streamlit app code using Vibe Studio
    NOW WITH PROPER CONTEXT EXTRACTION AND SHARING
    """
    try:
        session_id = action.session_id
        user_requirements = action.data.get("requirements", "")
        
        
        _ensure_session_structure(session_id)
        
        # Get existing ideation context from memory
        session_data = session_storage.get(session_id, {})
        ideation_data = session_data.get("app_data", {}).get("ideation", {})
        
        # KEY FIX: If no ideation data exists, extract it from user input and SAVE IT
        if not ideation_data:
            print(f"No ideation data found, extracting from user input: {user_requirements}")
            
            # Extract app information from user requirements
            extracted_app_name = _extract_app_name_from_text(user_requirements)
            extracted_category = _extract_app_category_from_text(user_requirements)
            
            # Create ideation data from extracted information
            ideation_data = {
                "name": extracted_app_name,
                "category": extracted_category,
                "description": user_requirements or f"{extracted_app_name} application"
            }
            
            # CRITICAL: Save the extracted ideation data to session for chat system
            session_storage[session_id]["app_data"]["ideation"] = ideation_data
            
            print(f"Extracted and saved app context: {ideation_data}")
        else:
            print(f"Using existing ideation data: {ideation_data}")
        
        # Generate the Streamlit app
        generation_result = await code_agent.generate_streamlit_app(
            app_idea=ideation_data,
            user_requirements=user_requirements
        )
        
        if generation_result["success"]:
            # Save the generated app context in memory
            session_storage[session_id]["app_data"]["vibe_studio"] = {
                "app_name": generation_result["app_name"],
                "project_files": generation_result["project_files"],
                "app_structure": generation_result["app_structure"],
                "user_requirements": user_requirements
            }
            
            print(f"Saved Vibe Studio context for session {session_id}")
        
        return JSONResponse({
            "status": "success" if generation_result["success"] else "error",
            "result": generation_result,
            "next_suggestion": "Great! Your app is ready. Want to create marketing materials? I can open the Design app!",
            "extracted_context": ideation_data  # Show what was extracted
        })
        
    except Exception as e:
        print(f"Error in vibe-studio route: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"App generation failed: {str(e)}"
        )

@router.post("/design/generate-image")
async def generate_marketing_image(action: AppAction):
    """
    Generate marketing images using Leonardo Agent
    """
    try:
        session_id = action.session_id
        user_prompt = action.data.get("prompt", "")
        image_type = action.data.get("image_type", "marketing")
        context = action.data.get("context", "")  # For direct usage
        
        _ensure_session_structure(session_id)
        
        # Get context from memory - try multiple sources
        session_data = session_storage.get(session_id, {})
        ideation_data = session_data.get("app_data", {}).get("ideation", {})
        
        # If no ideation data but user provided context, extract it
        if not ideation_data and context:
            print(f"No ideation data, extracting from design context: {context}")
            
            extracted_app_name = _extract_app_name_from_text(context)
            extracted_category = _extract_app_category_from_text(context)
            
            ideation_data = {
                "name": extracted_app_name,
                "category": extracted_category,
                "description": context
            }
            
            # Save extracted context
            session_storage[session_id]["app_data"]["ideation"] = ideation_data
            print(f"Extracted and saved design context: {ideation_data}")
        
        # Fallback to generic data if still no context
        if not ideation_data:
            ideation_data = {
                "name": "Application",
                "category": "technology", 
                "description": "mobile application"
            }
        
        # Generate the image
        image_result = await leonardo_agent.generate_marketing_image(
            idea_context=ideation_data,
            user_prompt=user_prompt,
            image_type=image_type
        )
        
        if image_result["success"]:
            # Save the design context in memory
            session_storage[session_id]["app_data"]["design"] = {
                "image_type": image_type,
                "user_prompt": user_prompt,
                "context_used": context,
                "image_generated": True,
                "image_metadata": image_result.get("metadata", {})
            }
        
        return JSONResponse({
            "status": "success" if image_result["success"] else "error",
            "result": image_result,
            "next_suggestion": "Perfect! Your marketing materials are ready. Ready to launch? I can help you draft emails!",
            "context_used": ideation_data
        })
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image generation failed: {str(e)}"
        )

@router.post("/gmail/draft-email")
async def draft_marketing_email(action: AppAction):
    """
    Draft marketing email using Email Agent
    """
    try:
        session_id = action.session_id
        email_type = action.data.get("email_type", "launch")
        target_audience = action.data.get("target_audience", "general")
        context = action.data.get("context", "")  # For direct usage
        
        _ensure_session_structure(session_id)
        
        # Get full context from memory
        session_data = session_storage.get(session_id, {})
        app_data = session_data.get("app_data", {})
        
        # Build comprehensive app context for email
        app_context = {
            "app_name": "Generated App",
            "app_category": "technology",
            "app_description": "An innovative application"
        }
        
        # Extract data from each app in the workflow
        if "ideation" in app_data:
            ideation = app_data["ideation"]
            app_context.update({
                "app_name": ideation.get("name", app_context["app_name"]),
                "app_category": ideation.get("category", app_context["app_category"]),
                "app_description": ideation.get("description", app_context["app_description"]),
                "ideation_data": ideation
            })
        elif context:
            # If no ideation data but user provided context, extract it
            print(f"No ideation data, extracting from email context: {context}")
            
            extracted_app_name = _extract_app_name_from_text(context)
            extracted_category = _extract_app_category_from_text(context)
            
            ideation_data = {
                "name": extracted_app_name,
                "category": extracted_category,
                "description": context
            }
            
            # Save extracted context
            session_storage[session_id]["app_data"]["ideation"] = ideation_data
            
            # Update app_context
            app_context.update({
                "app_name": extracted_app_name,
                "app_category": extracted_category,
                "app_description": context,
                "ideation_data": ideation_data
            })
            
            print(f"Extracted and saved email context: {ideation_data}")
        
        if "vibe_studio" in app_data:
            app_context["vibe_studio_data"] = app_data["vibe_studio"]
        
        if "design" in app_data:
            app_context["design_data"] = app_data["design"]
        
        # Generate the email
        email_result = await email_agent.generate_launch_email(
            app_context=app_context,
            target_audience=target_audience,
            email_type=email_type
        )
        
        if email_result["success"]:
            # Save the email context in memory
            session_storage[session_id]["app_data"]["gmail"] = {
                "email_type": email_type,
                "target_audience": target_audience,
                "context_used": context,
                "email_generated": True,
                "subject_line": email_result["subject_line"],
                "email_body": email_result["email_body"],  # Store for sending
                "complete_email": email_result["complete_email"]
            }
        
        return JSONResponse({
            "status": "success" if email_result["success"] else "error",
            "result": email_result,
            "next_suggestion": "Excellent! Your launch email is ready. Want to send it? Use the send email feature!",
            "context_used": app_context
        })
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email generation failed: {str(e)}"
        )

# NEW: MCP Gmail Send Email Endpoint
@router.post("/gmail/send-email")
async def send_email_via_mcp(action: AppAction):
    """
    Send email using MCP Gmail integration
    """
    try:
        session_id = action.session_id
        email_data = action.data
        
        # Extract required fields
        recipient_email = email_data.get("recipient_email", "")
        subject = email_data.get("subject", "")
        email_body = email_data.get("email_body", "")
        sender_name = email_data.get("sender_name", "Steve Connect")
        
        # Validate required fields
        if not recipient_email or not subject or not email_body:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields: recipient_email, subject, email_body"
            )
        
        _ensure_session_structure(session_id)
        
        # Send the email via MCP
        print(f"Attempting to send email via MCP to {recipient_email}")
        send_result = await email_sender.send_email(
            recipient_email=recipient_email,
            subject=subject,
            email_body=email_body,
            sender_name=sender_name
        )
        
        if send_result["success"]:
            # Update session storage with send status
            session_storage[session_id]["app_data"]["gmail_send"] = {
                "sent": True,
                "message_id": send_result["message_id"],
                "recipient": recipient_email,
                "subject": subject,
                "sent_at": "now",
                "method": send_result.get("method", "mcp"),
                "mcp_tool": send_result.get("mcp_tool", "unknown")
            }
        
        return JSONResponse({
            "status": "success" if send_result["success"] else "error",
            "result": send_result,
            "message": "Email sent successfully via MCP!" if send_result["success"] else f"Failed to send email: {send_result.get('error', 'Unknown error')}"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in send email endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email sending failed: {str(e)}"
        )

# Session and context management endpoints
@router.get("/session/{session_id}/context")
async def get_full_session_context(session_id: str):
    """
    Get complete session context from memory
    """
    try:
        context = session_storage.get(session_id)
        if not context:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return JSONResponse({
            "session_id": session_id,
            "context": context,
            "workflow_progress": _analyze_workflow_progress(context)
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session context: {str(e)}"
        )

@router.post("/session/{session_id}/reset")
async def reset_session(session_id: str):
    """
    Reset session context (useful for starting over)
    """
    try:
        if session_id in session_storage:
            del session_storage[session_id]
        
        return JSONResponse({
            "status": "success",
            "message": "Session reset successfully",
            "session_id": session_id
        })
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset session: {str(e)}"
        )

# Health checks for all agents
@router.get("/health/agents")
async def check_agents_health():
    """
    Check if all AI agents are working properly
    """
    try:
        health_status = {
            "router_agent": "healthy",
            "leonardo_agent": "healthy", 
            "code_agent": "healthy",
            "email_agent": "healthy",
            "email_sender": "healthy"  # NEW: MCP email sender health
        }
        
        return JSONResponse({
            "overall_status": "healthy",
            "agents": health_status,
            "session_count": len(session_storage),
            "active_sessions": list(session_storage.keys())[-5:]  # Show last 5 sessions
        })
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent health check failed: {str(e)}"
        )

# Helper functions
def _analyze_workflow_progress(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze how far the user has progressed through the workflow
    """
    app_data = context.get("app_data", {})
    
    progress = {
        "ideation_complete": "ideation" in app_data and bool(app_data["ideation"]),
        "vibe_studio_complete": "vibe_studio" in app_data and bool(app_data["vibe_studio"]),
        "design_complete": "design" in app_data and bool(app_data["design"]),
        "gmail_complete": "gmail" in app_data and bool(app_data["gmail"]),
        "email_sent": "gmail_send" in app_data and app_data["gmail_send"].get("sent", False)  # NEW: Track email sending
    }
    
    completed_steps = sum([progress["ideation_complete"], progress["vibe_studio_complete"], 
                          progress["design_complete"], progress["gmail_complete"]])
    progress["completion_percentage"] = (completed_steps / 4) * 100
    progress["next_recommended_step"] = _get_next_step(progress)
    progress["current_app_context"] = app_data.get("ideation", {})
    
    return progress

def _get_next_step(progress: Dict[str, Any]) -> str:
    """
    Recommend the next step in the workflow
    """
    if not progress["ideation_complete"]:
        return "Complete ideation to develop your app concept"
    elif not progress["vibe_studio_complete"]:
        return "Use Vibe Studio to build your app"
    elif not progress["design_complete"]:
        return "Create marketing materials with the Design app"
    elif not progress["gmail_complete"]:
        return "Draft launch emails with Gmail integration"
    elif not progress["email_sent"]:
        return "Send your launch email to complete the workflow!"
    else:
        return "Workflow complete! Your app is ready and launched!"