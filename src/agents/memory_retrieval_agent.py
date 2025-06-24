# src/agents/memory_retrieval_agent.py
"""
Simple Regex-Free Memory Retrieval Agent
Removed all hardcoded patterns - just uses semantic search for everything
Much shorter and simpler than the original i had a fall back regex before for pattern matching
"""

import os
from datetime import datetime
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv
from src.memory.vector_memory_manager import VectorMemoryManager

load_dotenv()

class MemoryRetrievalAgent:
    """
    Simple memory retrieval agent
    Just semantic search for everything
    """
    
    def __init__(self, memory_manager: VectorMemoryManager = None):
        # honestly this is way cleaner than the regex mess we had before
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.2,  # keeping it low so responses stay consistent
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            convert_system_message_to_human=True
        )
        
        self.memory_manager = memory_manager or VectorMemoryManager()
        print("Simple Regex-Free Memory Retrieval Agent initialized")
    
    async def get_relevant_context(self, 
                                 user_question: str, 
                                 session_context: Dict[str, Any] = None,
                                 max_context_stories: int = 5) -> Dict[str, Any]:
        """
        Simple approach: just use semantic search for everything
        """
        try:
            # turns out the vector embeddings are smart
            relevant_stories = await self.memory_manager.search_stories(
                query=user_question,
                top_k=max_context_stories
            )
            
            # only generate summary if we actually found something useful
            context_summary = ""
            if relevant_stories:
                context_summary = await self._generate_summary(
                    user_question, relevant_stories, session_context
                )
            
            return {
                'relevant_stories': relevant_stories,
                'context_summary': context_summary,
                'retrieval_strategy': 'semantic_search',  # keeping it simple, using semantic search
                'confidence': 0.8,  # pretty confident in semantic search tbh
                'stories_found': len(relevant_stories)
            }
            
        except Exception as e:
            # if something breaks,
            print(f"Error in memory retrieval: {e}")
            return {
                'relevant_stories': [],
                'context_summary': "",
                'retrieval_strategy': 'error',
                'confidence': 0.0,
                'stories_found': 0
            }
    
    async def _generate_summary(self, 
                              user_question: str,
                              relevant_stories: List[Dict[str, Any]],
                              session_context: Dict[str, Any] = None) -> str:
        """
        Generate simple context summary
        """
        try:
            if not relevant_stories:
                return ""
            
            # just mash all the stories together - the LLM can figure out what matters
            stories_text = "\n\n".join([
                f"Story {i+1}: {story['story_text']}" 
                for i, story in enumerate(relevant_stories)
            ])
            
            # keeping the prompt dead simple - no fancy instructions needed
            system_prompt = f"""
Answer the user's question using their project history.

USER QUESTION: "{user_question}"

RELEVANT STORIES:
{stories_text}

Create a natural, helpful response (2-3 sentences) that directly answers their question using the story information.
"""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content="Generate a helpful response.")
            ]
            
            response = await self.llm.ainvoke(messages)
            return response.content.strip()
            
        except Exception as e:
            # fallback when AI craps out - at least tell them we found something
            print(f"Error generating summary: {e}")
            return f"Found {len(relevant_stories)} relevant activities in your project history."
    
    async def get_project_timeline(self, 
                                 project_name: str, 
                                 max_stories: int = 10) -> Dict[str, Any]:
        """
        Simple project timeline using semantic search
        """
        try:
            # just search for the project name - semantic search should find related stuff
            stories = await self.memory_manager.search_stories(
                query=f"project {project_name}",
                top_k=max_stories
            )
            
            if not stories:
                return {
                    'project_name': project_name,
                    'timeline': [],
                    'total_activities': 0,
                    'date_range': 'No activities found'
                }
            
            # sort by time so we get a proper timeline, not just relevance
            sorted_stories = sorted(
                stories, 
                key=lambda x: x['metadata'].get('timestamp', ''),
                reverse=False  # oldest first makes more sense for timelines
            )
            
            # figure out the date range so users know what period we're covering
            timestamps = [s['metadata'].get('timestamp', '') for s in sorted_stories if s['metadata'].get('timestamp')]
            date_range = 'Unknown dates'
            if timestamps:
                start_date = timestamps[0][:10]  # just the date part, not time
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
        Simple direct question answering
        """
        context = await self.get_relevant_context(question)
        
        if context['context_summary']:
            return context['context_summary']
        elif context['relevant_stories']:
            # letting them know if we did not find anything
            return f"I found {len(context['relevant_stories'])} relevant activities, but couldn't generate a summary."
        else:
            return "I don't have any relevant information about that in your project history."