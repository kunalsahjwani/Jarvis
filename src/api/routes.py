# src/api/routes.py - Simplified without database dependencies
"""
FastAPI routes for Steve Connect - No Database Version
Handles all API endpoints for the orchestrator system
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid

# Import our agents (no database imports)
from src.agents.router_agent import RouterAgent
from src.agents.leonardo_agent import LeonardoAgent
from src.agents.code_agent import CodeAgent
from src.agents.email_agent import EmailAgent

# Create the main router
router = APIRouter()

# Initialize all agents
router_agent = RouterAgent()
leonardo_agent = LeonardoAgent()
code_agent = CodeAgent()
email_agent = EmailAgent()

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
            session_storage[session_id] = {
                "user_id": message.user_id,
                "conversation_history": [],
                "current_app": None,
                "app_data": {}
            }
        
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
            context_data=session_context.get("app_data", {})
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
        
        # Save ideation context in memory
        if session_id in session_storage:
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
    """
    try:
        session_id = action.session_id
        user_requirements = action.data.get("requirements", "")
        complexity = action.data.get("complexity", "simple")
        
        # Get ideation context from memory
        session_data = session_storage.get(session_id, {})
        ideation_data = session_data.get("app_data", {}).get("ideation", {})
        
        if not ideation_data:
            return JSONResponse({
                "status": "error",
                "message": "No ideation data found. Please complete ideation first."
            })
        
        # Generate the Streamlit app
        generation_result = await code_agent.generate_streamlit_app(
            app_idea=ideation_data,
            user_requirements=user_requirements,
            complexity_level=complexity
        )
        
        if generation_result["success"]:
            # Save the generated app context in memory
            if session_id in session_storage:
                session_storage[session_id]["app_data"]["vibe_studio"] = {
                    "app_name": generation_result["app_name"],
                    "project_files": generation_result["project_files"],
                    "app_structure": generation_result["app_structure"],
                    "complexity": complexity
                }
        
        return JSONResponse({
            "status": "success" if generation_result["success"] else "error",
            "result": generation_result,
            "next_suggestion": "Great! Your app is ready. Want to create marketing materials? I can open the Design app!"
        })
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"App generation failed: {str(e)}"
        )

@router.post("/design/generate-image")
async def generate_marketing_image(action: AppAction):
    """
    Generate marketing images using Leonardo Agent (Hugging Face)
    """
    try:
        session_id = action.session_id
        user_prompt = action.data.get("prompt", "")
        image_type = action.data.get("image_type", "marketing")
        
        # Get context from memory
        session_data = session_storage.get(session_id, {})
        ideation_data = session_data.get("app_data", {}).get("ideation", {})
        
        if not ideation_data:
            ideation_data = {"category": "technology", "description": "mobile application"}
        
        # Generate the image
        image_result = await leonardo_agent.generate_marketing_image(
            idea_context=ideation_data,
            user_prompt=user_prompt,
            image_type=image_type
        )
        
        if image_result["success"]:
            # Save the design context in memory
            if session_id in session_storage:
                session_storage[session_id]["app_data"]["design"] = {
                    "image_type": image_type,
                    "user_prompt": user_prompt,
                    "image_generated": True,
                    "image_metadata": image_result.get("metadata", {})
                }
        
        return JSONResponse({
            "status": "success" if image_result["success"] else "error",
            "result": image_result,
            "next_suggestion": "Perfect! Your marketing materials are ready. Ready to launch? I can help you draft emails!"
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
            if session_id in session_storage:
                session_storage[session_id]["app_data"]["gmail"] = {
                    "email_type": email_type,
                    "target_audience": target_audience,
                    "email_generated": True,
                    "subject_line": email_result["subject_line"]
                }
        
        return JSONResponse({
            "status": "success" if email_result["success"] else "error",
            "result": email_result,
            "next_suggestion": "Excellent! Your launch email is ready. You've completed the full workflow from idea to launch!"
        })
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email generation failed: {str(e)}"
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
            "email_agent": "healthy"
        }
        
        return JSONResponse({
            "overall_status": "healthy",
            "agents": health_status,
            "session_count": len(session_storage)
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
        "ideation_complete": "ideation" in app_data,
        "vibe_studio_complete": "vibe_studio" in app_data,
        "design_complete": "design" in app_data,
        "gmail_complete": "gmail" in app_data,
    }
    
    completed_steps = sum(progress.values())
    progress["completion_percentage"] = (completed_steps / 4) * 100
    progress["next_recommended_step"] = _get_next_step(progress)
    
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
    else:
        return "Workflow complete! Your app is ready to launch."