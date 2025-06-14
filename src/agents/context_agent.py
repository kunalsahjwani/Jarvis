# src/agents/context_agent.py
"""
Context Agent - Manages conversation memory and context across apps
This agent ensures continuity when users move from Ideation -> Vibe Studio -> Design -> Gmail
"""

import json
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
import uuid
from datetime import datetime

from src.database.models import Session, ContextMemory, AppState
from src.database.connection import AsyncSessionLocal

class ContextAgent:
    """
    Manages context and memory across the Steve Connect ecosystem
    """
    
    def __init__(self):
        self.session_contexts = {}  # In-memory cache for active sessions
    
    async def create_session(self, user_id: str) -> str:
        """
        Create a new conversation session
        """
        try:
            async with AsyncSessionLocal() as db:
                # Create new session
                new_session = Session(
                    user_id=user_id,
                    is_active=True
                )
                
                db.add(new_session)
                await db.commit()
                await db.refresh(new_session)
                
                session_id = str(new_session.id)
                
                # Initialize in-memory context
                self.session_contexts[session_id] = {
                    "user_id": user_id,
                    "created_at": datetime.now().isoformat(),
                    "conversation_flow": [],
                    "current_app": None,
                    "app_data": {}
                }
                
                return session_id
                
        except Exception as e:
            print(f"Error creating session: {e}")
            raise
    
    async def get_session_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full context for a session
        """
        try:
            # Check in-memory cache first
            if session_id in self.session_contexts:
                return self.session_contexts[session_id]
            
            # Load from database
            async with AsyncSessionLocal() as db:
                # Get session with all related data
                result = await db.execute(
                    select(Session)
                    .options(
                        selectinload(Session.context_memories),
                        selectinload(Session.app_states)
                    )
                    .where(Session.id == session_id)
                )
                session = result.scalar_one_or_none()
                
                if not session:
                    return None
                
                # Rebuild context from database
                context = {
                    "user_id": session.user_id,
                    "created_at": session.created_at.isoformat(),
                    "conversation_flow": [],
                    "current_app": None,
                    "app_data": {}
                }
                
                # Load context memories
                for memory in session.context_memories:
                    context["app_data"][memory.app_name] = memory.context_data
                    context["conversation_flow"].append({
                        "app": memory.app_name,
                        "timestamp": memory.created_at.isoformat(),
                        "data": memory.context_data
                    })
                
                # Get current app state
                if session.app_states:
                    latest_state = max(session.app_states, key=lambda x: x.updated_at)
                    context["current_app"] = latest_state.current_app
                
                # Cache it
                self.session_contexts[session_id] = context
                
                return context
                
        except Exception as e:
            print(f"Error getting session context: {e}")
            return None
    
    async def save_app_context(self, session_id: str, app_name: str, context_data: Dict[str, Any]):
        """
        Save context data from a specific app
        This is called when user finishes working in an app
        """
        try:
            async with AsyncSessionLocal() as db:
                # Save to database
                context_memory = ContextMemory(
                    session_id=session_id,
                    app_name=app_name,
                    context_data=context_data
                )
                
                db.add(context_memory)
                await db.commit()
                
                # Update in-memory cache
                if session_id in self.session_contexts:
                    self.session_contexts[session_id]["app_data"][app_name] = context_data
                    self.session_contexts[session_id]["conversation_flow"].append({
                        "app": app_name,
                        "timestamp": datetime.now().isoformat(),
                        "data": context_data
                    })
                
                print(f"✅ Saved context for {app_name} in session {session_id}")
                
        except Exception as e:
            print(f"Error saving app context: {e}")
            raise
    
    async def update_app_state(self, session_id: str, current_app: str, previous_app: Optional[str] = None):
        """
        Update which app is currently active
        """
        try:
            async with AsyncSessionLocal() as db:
                # Check if app state exists for this session
                result = await db.execute(
                    select(AppState).where(AppState.session_id == session_id)
                )
                app_state = result.scalar_one_or_none()
                
                if app_state:
                    # Update existing state
                    app_state.previous_app = app_state.current_app
                    app_state.current_app = current_app
                    app_state.updated_at = datetime.now()
                else:
                    # Create new state
                    app_state = AppState(
                        session_id=session_id,
                        current_app=current_app,
                        previous_app=previous_app
                    )
                    db.add(app_state)
                
                await db.commit()
                
                # Update in-memory cache
                if session_id in self.session_contexts:
                    self.session_contexts[session_id]["current_app"] = current_app
                
        except Exception as e:
            print(f"Error updating app state: {e}")
            raise
    
    async def get_context_for_app(self, session_id: str, app_name: str) -> Dict[str, Any]:
        """
        Get relevant context when opening a specific app
        This is the key method that provides continuity between apps
        """
        try:
            context = await self.get_session_context(session_id)
            if not context:
                return {}
            
            # Get direct context for this app
            app_context = context["app_data"].get(app_name, {})
            
            # Get context from previous apps in the workflow
            workflow_context = self._build_workflow_context(context, app_name)
            
            return {
                "app_context": app_context,
                "workflow_context": workflow_context,
                "conversation_flow": context["conversation_flow"],
                "user_id": context["user_id"]
            }
            
        except Exception as e:
            print(f"Error getting context for app {app_name}: {e}")
            return {}
    
    def _build_workflow_context(self, session_context: Dict[str, Any], target_app: str) -> Dict[str, Any]:
        """
        Build context from previous apps in the typical workflow
        Ideation -> Vibe Studio -> Design -> Gmail
        """
        workflow_context = {}
        app_data = session_context["app_data"]
        
        if target_app == "vibe_studio":
            # Vibe Studio needs ideation context
            if "ideation" in app_data:
                workflow_context["idea"] = app_data["ideation"]
                workflow_context["prompt_context"] = f"Based on the user's idea: {app_data['ideation']}"
        
        elif target_app == "design":
            # Design needs both ideation and vibe_studio context
            if "ideation" in app_data:
                workflow_context["idea"] = app_data["ideation"]
            if "vibe_studio" in app_data:
                workflow_context["app_concept"] = app_data["vibe_studio"]
                workflow_context["prompt_context"] = f"Create marketing materials for: {app_data['vibe_studio']}"
        
        elif target_app == "gmail":
            # Gmail needs context from all previous apps
            if "ideation" in app_data:
                workflow_context["idea"] = app_data["ideation"]
            if "vibe_studio" in app_data:
                workflow_context["app_concept"] = app_data["vibe_studio"]
            if "design" in app_data:
                workflow_context["marketing_materials"] = app_data["design"]
            
            # Build email context
            workflow_context["email_context"] = self._build_email_context(app_data)
        
        return workflow_context
    
    def _build_email_context(self, app_data: Dict[str, Any]) -> str:
        """
        Build context string for email drafting
        """
        try:
            parts = []
            
            if "ideation" in app_data:
                idea_info = app_data["ideation"]
                if isinstance(idea_info, dict):
                    category = idea_info.get("category", "")
                    description = idea_info.get("description", "")
                    parts.append(f"Product Category: {category}")
                    parts.append(f"Description: {description}")
                else:
                    parts.append(f"Idea: {idea_info}")
            
            if "vibe_studio" in app_data:
                parts.append(f"App Development: {app_data['vibe_studio']}")
            
            if "design" in app_data:
                parts.append(f"Marketing Materials: {app_data['design']}")
            
            return " | ".join(parts)
            
        except Exception as e:
            print(f"Error building email context: {e}")
            return "New product launch"
    
    async def clear_session(self, session_id: str):
        """
        Clear session data (useful for testing or user logout)
        """
        try:
            # Remove from in-memory cache
            if session_id in self.session_contexts:
                del self.session_contexts[session_id]
            
            # Mark session as inactive in database
            async with AsyncSessionLocal() as db:
                await db.execute(
                    update(Session)
                    .where(Session.id == session_id)
                    .values(is_active=False)
                )
                await db.commit()
                
        except Exception as e:
            print(f"Error clearing session: {e}")
            raise

# TODO: Add these features later:
# - Context compression for long conversations
# - Smart context relevance scoring
# - Context sharing between users (for collaboration)
# - Context backup and restore functionality