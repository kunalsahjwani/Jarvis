# src/agents/memory_retrieval_agent.py
"""
Memory Retrieval Agent - Retrieves relevant user stories for chat context
Intelligent context provider that understands user questions and finds relevant memories
"""

import os
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv
from src.memory.vector_memory_manager import VectorMemoryManager

load_dotenv()

class MemoryRetrievalAgent:
    """
    Intelligent agent that retrieves relevant user stories for chat context
    """
    
    def __init__(self, memory_manager: VectorMemoryManager = None):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.2,  # Lower temperature for consistent retrieval
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            convert_system_message_to_human=True
        )
        
        self.memory_manager = memory_manager or VectorMemoryManager()
        
        # Query patterns for different types of memory retrieval
        self.query_patterns = {
            'current_project': [
                r'what.*(current|my|this).*idea',
                r'what.*(current|my|this).*app',
                r'what.*(current|my|this).*project',
                r'tell me about my (app|idea|project)',
                r'what am i (working on|building)',
            ],
            'recent_work': [
                r'what did i (do|work on|create|build)',
                r'what have i (done|worked on|created|built)',
                r'recent (work|progress|activity)',
                r'what.*(yesterday|today|this week|last week)',
                r'show me my (progress|work|activity)',
            ],
            'specific_app': [
                r'tell me about (\w+)',
                r'what is (\w+)',
                r'(\w+) app',
                r'(\w+) project',
            ],
            'app_features': [
                r'what features.*(\w+)',
                r'what does (\w+) do',
                r'how does (\w+) work',
                r'(\w+) functionality',
            ],
            'workflow_progress': [
                r'what (step|stage|phase)',
                r'where am i in',
                r'what.*(next|should i do)',
                r'(progress|status) of',
            ],
            'marketing_materials': [
                r'what (images|designs|marketing)',
                r'(created|made|designed).*image',
                r'marketing (materials|content)',
                r'(logo|banner|visual)',
            ],
            'emails_campaigns': [
                r'what (emails|campaigns)',
                r'(drafted|sent|created).*email',
                r'email (campaigns|marketing)',
                r'launch (email|campaign)',
            ]
        }
        
        print("Memory Retrieval Agent initialized")
    
    async def get_relevant_context(self, 
                                 user_question: str, 
                                 session_context: Dict[str, Any] = None,
                                 max_context_stories: int = 5) -> Dict[str, Any]:
        """
        Get relevant context for a user question by retrieving appropriate memories
        
        Args:
            user_question: The user's question/message
            session_context: Current session data
            max_context_stories: Maximum number of stories to retrieve
        
        Returns:
            {
                'relevant_stories': [...],
                'context_summary': 'AI-generated summary',
                'retrieval_strategy': 'strategy_used',
                'confidence': 0.0-1.0
            }
        """
        try:
            # Analyze the question to determine retrieval strategy
            analysis = await self._analyze_question(user_question, session_context)
            
            # Retrieve relevant stories based on strategy
            relevant_stories = await self._retrieve_stories(
                question=user_question,
                strategy=analysis['strategy'],
                strategy_params=analysis['params'],
                max_stories=max_context_stories
            )
            
            # Generate context summary if stories were found
            context_summary = ""
            if relevant_stories:
                context_summary = await self._generate_context_summary(
                    user_question, relevant_stories, session_context
                )
            
            return {
                'relevant_stories': relevant_stories,
                'context_summary': context_summary,
                'retrieval_strategy': analysis['strategy'],
                'confidence': analysis['confidence'],
                'stories_found': len(relevant_stories)
            }
            
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return {
                'relevant_stories': [],
                'context_summary': "",
                'retrieval_strategy': 'error',
                'confidence': 0.0,
                'stories_found': 0
            }
    
    async def _analyze_question(self, 
                              question: str, 
                              session_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze user question to determine best retrieval strategy
        """
        question_lower = question.lower()
        
        # Check for time-based queries
        time_patterns = {
            'today': 0,
            'yesterday': 1,
            'this week': 7,
            'last week': 14,
            'this month': 30,
            'recent': 7
        }
        
        for time_phrase, days_back in time_patterns.items():
            if time_phrase in question_lower:
                return {
                    'strategy': 'time_based',
                    'params': {'days_back': days_back},
                    'confidence': 0.9
                }
        
        # Check for current project queries
        for pattern in self.query_patterns['current_project']:
            if re.search(pattern, question_lower):
                return {
                    'strategy': 'current_project',
                    'params': self._extract_current_project_params(session_context),
                    'confidence': 0.95
                }
        
        # Check for specific app mentions
        app_match = self._extract_app_name(question_lower)
        if app_match:
            return {
                'strategy': 'specific_app',
                'params': {'app_name': app_match},
                'confidence': 0.9
            }
        
        # Check for workflow progress queries
        for pattern in self.query_patterns['workflow_progress']:
            if re.search(pattern, question_lower):
                return {
                    'strategy': 'workflow_progress',
                    'params': {},
                    'confidence': 0.8
                }
        
        # Check for marketing/design queries
        for pattern in self.query_patterns['marketing_materials']:
            if re.search(pattern, question_lower):
                return {
                    'strategy': 'app_specific',
                    'params': {'app_name': 'design'},
                    'confidence': 0.85
                }
        
        # Check for email/campaign queries
        for pattern in self.query_patterns['emails_campaigns']:
            if re.search(pattern, question_lower):
                return {
                    'strategy': 'app_specific',
                    'params': {'app_name': 'gmail'},
                    'confidence': 0.85
                }
        
        # Default to semantic search
        return {
            'strategy': 'semantic_search',
            'params': {'query': question},
            'confidence': 0.6
        }
    
    async def _retrieve_stories(self, 
                              question: str,
                              strategy: str, 
                              strategy_params: Dict[str, Any], 
                              max_stories: int) -> List[Dict[str, Any]]:
        """
        Retrieve stories based on the determined strategy
        """
        try:
            if strategy == 'time_based':
                return await self.memory_manager.search_by_timeframe(
                    days_back=strategy_params.get('days_back', 7),
                    top_k=max_stories
                )
            
            elif strategy == 'current_project':
                project_name = strategy_params.get('project_name')
                if project_name:
                    return await self.memory_manager.search_by_project(
                        project_name=project_name,
                        top_k=max_stories
                    )
                else:
                    # Fallback to recent stories
                    return await self.memory_manager.search_by_timeframe(
                        days_back=7,
                        top_k=max_stories
                    )
            
            elif strategy == 'specific_app':
                app_name = strategy_params.get('app_name')
                return await self.memory_manager.search_stories(
                    query=f"app {app_name}",
                    top_k=max_stories,
                    filters={'project_name': app_name} if app_name else None
                )
            
            elif strategy == 'app_specific':
                app_name = strategy_params.get('app_name')
                return await self.memory_manager.search_stories(
                    query=question,
                    top_k=max_stories,
                    filters={'app_name': app_name} if app_name else None
                )
            
            elif strategy == 'workflow_progress':
                # Get recent stories from all apps to show progress
                return await self.memory_manager.search_by_timeframe(
                    days_back=14,
                    top_k=max_stories * 2  # Get more to show full workflow
                )
            
            else:  # semantic_search
                return await self.memory_manager.search_stories(
                    query=question,
                    top_k=max_stories
                )
        
        except Exception as e:
            print(f"Error in story retrieval: {e}")
            return []
    
    def _extract_current_project_params(self, session_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Extract current project information from session context
        """
        if not session_context:
            return {}
        
        app_data = session_context.get('app_data', {})
        ideation_data = app_data.get('ideation', {})
        
        return {
            'project_name': ideation_data.get('name', ''),
            'project_category': ideation_data.get('category', ''),
            'project_description': ideation_data.get('description', '')
        }
    
    def _extract_app_name(self, question: str) -> Optional[str]:
        """
        Extract specific app names mentioned in the question
        """
        # Common app names in your system
        app_names = ['aktasks', 'guide genie', 'taskmaster', 'fittracker', 'marketbasket']
        
        for app_name in app_names:
            if app_name.lower() in question:
                return app_name
        
        # Try to extract quoted or capitalized app names
        import re
        quoted_match = re.search(r'["\']([^"\']+)["\']', question)
        if quoted_match:
            return quoted_match.group(1)
        
        # Look for capitalized words that might be app names
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)*\b', question)
        if capitalized:
            return capitalized[0]
        
        return None
    
    async def _generate_context_summary(self, 
                                      user_question: str,
                                      relevant_stories: List[Dict[str, Any]],
                                      session_context: Dict[str, Any] = None) -> str:
        """
        Generate a concise summary of the relevant context for the chat agent
        """
        try:
            if not relevant_stories:
                return ""
            
            # Prepare stories for AI summarization
            stories_text = "\n\n".join([
                f"Story {i+1}: {story['story_text']}" 
                for i, story in enumerate(relevant_stories)
            ])
            
            system_prompt = f"""
You are a context summarizer for an AI assistant. Your job is to create a concise, helpful summary of the user's project history that directly answers their question.

USER QUESTION: "{user_question}"

RELEVANT USER STORIES:
{stories_text}

Create a summary that:
1. Directly answers the user's question using the story information
2. Mentions specific app names, features, and progress details
3. Maintains chronological order when relevant
4. Is concise but informative (2-4 sentences max)
5. Uses natural language, not bullet points

If the user asked about their current project, focus on the most recent app details.
If they asked about progress, highlight what they've accomplished.
If they asked about specific features, mention those details.

EXAMPLE GOOD SUMMARY:
"Based on your recent work, you've been developing Aktasks, a task management app that prioritizes user tasks intelligently. You successfully built the Streamlit application with input boxes for tasks and dates, created marketing images showing a clean professional interface, and drafted launch emails targeting productivity-focused users."
"""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content="Generate a context summary based on the user stories provided.")
            ]
            
            response = await self.llm.ainvoke(messages)
            return response.content.strip()
            
        except Exception as e:
            print(f"Error generating context summary: {e}")
            # Fallback to simple text join
            return f"Found {len(relevant_stories)} relevant activities in your project history."
    
    async def get_project_timeline(self, 
                                 project_name: str, 
                                 max_stories: int = 10) -> Dict[str, Any]:
        """
        Get a chronological timeline of activities for a specific project
        """
        try:
            stories = await self.memory_manager.search_by_project(
                project_name=project_name,
                top_k=max_stories
            )
            
            if not stories:
                return {
                    'project_name': project_name,
                    'timeline': [],
                    'total_activities': 0,
                    'date_range': 'No activities found'
                }
            
            # Sort by timestamp
            sorted_stories = sorted(
                stories, 
                key=lambda x: x['metadata'].get('timestamp', ''),
                reverse=False  # Oldest first for timeline
            )
            
            # Extract date range
            timestamps = [s['metadata'].get('timestamp', '') for s in sorted_stories if s['metadata'].get('timestamp')]
            date_range = 'Unknown dates'
            if timestamps:
                start_date = timestamps[0][:10]
                end_date = timestamps[-1][:10]
                date_range = f"{start_date} to {end_date}"
            
            return {
                'project_name': project_name,
                'timeline': sorted_stories,
                'total_activities': len(sorted_stories),
                'date_range': date_range
            }
            
        except Exception as e:
            print(f"Error getting project timeline: {e}")
            return {
                'project_name': project_name,
                'timeline': [],
                'total_activities': 0,
                'date_range': 'Error retrieving timeline'
            }
    
    async def answer_direct_question(self, question: str) -> str:
        """
        Directly answer a question using memory context (useful for testing)
        """
        context = await self.get_relevant_context(question)
        
        if context['context_summary']:
            return context['context_summary']
        elif context['relevant_stories']:
            return f"I found {len(context['relevant_stories'])} relevant activities, but couldn't generate a summary."
        else:
            return "I don't have any relevant information about that in your project history."