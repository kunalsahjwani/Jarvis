# src/agents/story_writer_agent.py
"""
Story Writer Agent - Converts app actions into narrative user stories
Transforms raw API events into coherent, searchable user journey documentation
"""

import os
from datetime import datetime
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv
import json

load_dotenv()

class StoryWriterAgent:
    """
    Converts app actions and user interactions into narrative user stories
    """
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.4,  # Slightly creative for natural storytelling
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            convert_system_message_to_human=True
        )
        
        print("Story Writer Agent initialized")
    
    async def write_story(self, 
                         event_data: Dict[str, Any], 
                         session_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Convert an app action/event into a narrative user story
        
        Args:
            event_data: {
                'app_name': 'vibe_studio',
                'action': 'generate_app',
                'timestamp': '2024-12-22T15:30:00',
                'user_id': 'user123',
                'session_id': 'session456',
                'data': {...action_specific_data...}
            }
            session_context: Current session context for additional details
        
        Returns:
            {
                'story_text': 'Narrative story text',
                'metadata': {...},
                'story_id': 'unique_id'
            }
        """
        try:
            # Extract event details
            app_name = event_data.get('app_name', 'unknown')
            action = event_data.get('action', 'unknown_action')
            timestamp = event_data.get('timestamp', datetime.now().isoformat())
            action_data = event_data.get('data', {})
            
            # Generate narrative story
            story_text = await self._generate_narrative(
                app_name=app_name,
                action=action,
                timestamp=timestamp,
                action_data=action_data,
                session_context=session_context or {}
            )
            
            # Create metadata for vector storage
            metadata = self._create_metadata(event_data, session_context)
            
            # Generate unique story ID
            story_id = f"story_{event_data.get('session_id', 'unknown')}_{int(datetime.now().timestamp())}"
            
            return {
                'story_text': story_text,
                'metadata': metadata,
                'story_id': story_id,
                'success': True
            }
            
        except Exception as e:
            print(f"Error writing story: {e}")
            return {
                'success': False,
                'error': str(e),
                'story_text': '',
                'metadata': {},
                'story_id': ''
            }
    
    async def _generate_narrative(self, 
                                app_name: str, 
                                action: str, 
                                timestamp: str, 
                                action_data: Dict[str, Any],
                                session_context: Dict[str, Any]) -> str:
        """
        Generate natural narrative text from structured event data
        """
        try:
            # Extract key context for storytelling
            app_context = session_context.get('app_data', {})
            ideation_data = app_context.get('ideation', {})
            app_idea_name = ideation_data.get('name', 'their app')
            app_category = ideation_data.get('category', 'application')
            
            # Format timestamp for human reading
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            formatted_time = dt.strftime("%B %d, %Y at %I:%M %p")
            
            system_prompt = f"""
You are a skilled technical writer who creates narrative user stories from app development actions.

Your task is to convert structured event data into natural, engaging narratives that capture:
1. What the user did
2. When they did it
3. What they were working on (app/project details)
4. What the outcome was
5. Any relevant context or decisions made

Write in third person, past tense, as if documenting a user journey.
Be specific about app names, features, and technical details when available.
Keep stories concise but informative (2-4 sentences).

WRITING STYLE:
- Natural, flowing narrative (not bullet points)
- Include specific app names and technical details
- Mention time context naturally
- Focus on user intent and outcomes
- Professional but engaging tone

EXAMPLE GOOD STORY:
"On December 22, 2024 at 3:15 PM, the user worked on their task management app called 'Aktasks' in the Vibe Studio. They requested a Streamlit application with two input boxes for entering tasks and due dates, emphasizing a clean priority-based sorting system. The code generation was successful, producing a functional app with modern UI components and proper task organization features."

APP CONTEXT:
- Current App: {app_name}
- Action: {action}
- Time: {formatted_time}
- App Being Developed: {app_idea_name} ({app_category})

ACTION DATA:
{json.dumps(action_data, indent=2)}
"""
            
            # Create specific prompt based on app and action
            human_prompt = self._create_action_specific_prompt(app_name, action, action_data, app_idea_name)
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            return response.content.strip()
            
        except Exception as e:
            print(f"Error generating narrative: {e}")
            # Fallback to simple template
            return self._create_fallback_story(app_name, action, timestamp, action_data)
    
    def _create_action_specific_prompt(self, 
                                     app_name: str, 
                                     action: str, 
                                     action_data: Dict[str, Any],
                                     app_idea_name: str) -> str:
        """
        Create tailored prompts based on specific app actions
        """
        prompts = {
            'ideation': {
                'submit_data': f"Write a story about the user developing their initial app concept for {app_idea_name}. Include the app category, description, and their creative process."
            },
            'vibe_studio': {
                'generate_app': f"Write a story about the user building their {app_idea_name} application in Vibe Studio. Include the specific features they requested and the technical approach taken.",
                'download_project': f"Write a story about the user downloading their completed {app_idea_name} project files to continue development locally."
            },
            'design': {
                'generate_image': f"Write a story about the user creating marketing materials for {app_idea_name}. Include the type of image created and the visual elements they requested.",
                'create_logo': f"Write a story about the user designing a logo for their {app_idea_name} application."
            },
            'gmail': {
                'draft_email': f"Write a story about the user preparing a launch campaign for {app_idea_name}. Include the email type and target audience.",
                'send_email': f"Write a story about the user sending their {app_idea_name} launch email to their audience."
            }
        }
        
        # Get specific prompt or use generic one
        app_prompts = prompts.get(app_name, {})
        specific_prompt = app_prompts.get(action, f"Write a story about the user working with {app_idea_name} in the {app_name} app, performing the action: {action}")
        
        return f"{specific_prompt}\n\nUse the provided action data to add specific technical details and context."
    
    def _create_fallback_story(self, 
                             app_name: str, 
                             action: str, 
                             timestamp: str, 
                             action_data: Dict[str, Any]) -> str:
        """
        Create a simple fallback story when AI generation fails
        """
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        formatted_time = dt.strftime("%B %d, %Y at %I:%M %p")
        
        return f"On {formatted_time}, the user performed {action} in the {app_name} application. The action completed successfully with the provided configuration."
    
    def _create_metadata(self, 
                        event_data: Dict[str, Any], 
                        session_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create metadata for vector storage and retrieval
        """
        app_context = session_context.get('app_data', {}) if session_context else {}
        ideation_data = app_context.get('ideation', {})
        
        return {
            'app_name': event_data.get('app_name', 'unknown'),
            'action': event_data.get('action', 'unknown'),
            'timestamp': event_data.get('timestamp', datetime.now().isoformat()),
            'session_id': event_data.get('session_id', 'unknown'),
            'user_id': event_data.get('user_id', 'unknown'),
            'project_name': ideation_data.get('name', 'unknown_project'),
            'project_category': ideation_data.get('category', 'unknown'),
            'action_type': self._classify_action_type(event_data.get('action', '')),
            'day_of_week': datetime.now().strftime('%A'),
            'hour_of_day': datetime.now().hour
        }
    
    def _classify_action_type(self, action: str) -> str:
        """
        Classify actions into broader categories for better retrieval
        """
        action_types = {
            'creation': ['generate', 'create', 'build', 'develop', 'draft'],
            'modification': ['edit', 'update', 'modify', 'change'],
            'sharing': ['send', 'share', 'publish', 'deploy'],
            'analysis': ['analyze', 'review', 'check', 'test'],
            'planning': ['ideate', 'plan', 'design', 'conceptualize']
        }
        
        action_lower = action.lower()
        for action_type, keywords in action_types.items():
            if any(keyword in action_lower for keyword in keywords):
                return action_type
        
        return 'general'
    
    async def write_multiple_stories(self, events: List[Dict[str, Any]], session_context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Write stories for multiple events (useful for batch processing)
        """
        stories = []
        for event in events:
            story = await self.write_story(event, session_context)
            stories.append(story)
        
        return stories