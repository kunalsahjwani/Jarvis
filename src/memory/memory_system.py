# src/memory/memory_system.py
"""
Memory System Integration - Core orchestrator for the user story memory system
Handles initialization and coordination between all memory components
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from src.agents.story_writer_agent import StoryWriterAgent
from src.memory.vector_memory_manager import VectorMemoryManager
from src.agents.memory_retrieval_agent import MemoryRetrievalAgent

class MemorySystem:
    """
    Core memory system that orchestrates story writing, storage, and retrieval
    """
    
    def __init__(self, storage_path: str = "data/memory"):
        """
        Initialize the complete memory system
        """
        print("Initializing Memory System...")
        
        # Initialize components
        self.vector_manager = VectorMemoryManager(storage_path=storage_path)
        self.story_writer = StoryWriterAgent()
        self.memory_retriever = MemoryRetrievalAgent(memory_manager=self.vector_manager)
        
        self.initialized = True
        
        print(f"Memory System initialized with {self.vector_manager.story_count} existing stories")
    
    async def record_app_action(self, 
                               app_name: str,
                               action: str,
                               session_id: str,
                               user_id: str = "default_user",
                               action_data: Dict[str, Any] = None,
                               session_context: Dict[str, Any] = None) -> bool:
        """
        Record an app action as a user story in memory
        
        Args:
            app_name: Name of the app (ideation, vibe_studio, design, gmail)
            action: Action performed (generate_app, create_image, etc.)
            session_id: Current session ID
            user_id: User identifier
            action_data: Specific data from the action
            session_context: Current session context for richer stories
        
        Returns:
            bool: Success status
        """
        try:
            # Create event data structure
            event_data = {
                'app_name': app_name,
                'action': action,
                'timestamp': datetime.now().isoformat(),
                'session_id': session_id,
                'user_id': user_id,
                'data': action_data or {}
            }
            
            # Generate story using Story Writer Agent
            print(f"Recording action: {app_name}.{action}")
            story_result = await self.story_writer.write_story(
                event_data=event_data,
                session_context=session_context
            )
            
            if not story_result.get('success', False):
                print(f"Failed to write story: {story_result.get('error', 'Unknown error')}")
                return False
            
            # Store story in vector memory
            storage_success = await self.vector_manager.add_story(story_result)
            
            if storage_success:
                print(f"Action recorded in memory: {story_result['story_id']}")
                return True
            else:
                print(f"Failed to store story in vector memory")
                return False
                
        except Exception as e:
            print(f"Error recording app action: {e}")
            return False
    
    async def get_context_for_chat(self, 
                                 user_message: str,
                                 session_context: Dict[str, Any] = None,
                                 max_stories: int = 5) -> Dict[str, Any]:
        """
        Get relevant memory context for a chat message
        
        Args:
            user_message: The user's chat message
            session_context: Current session context
            max_stories: Maximum number of stories to retrieve
        
        Returns:
            {
                'has_context': bool,
                'context_summary': str,
                'relevant_stories': [...],
                'retrieval_info': {...}
            }
        """
        try:
            print(f"Retrieving context for: '{user_message[:50]}...'")
            
            # Get relevant context using Memory Retrieval Agent
            context_result = await self.memory_retriever.get_relevant_context(
                user_question=user_message,
                session_context=session_context,
                max_context_stories=max_stories
            )
            
            has_context = len(context_result.get('relevant_stories', [])) > 0
            
            if has_context:
                print(f"Found {context_result['stories_found']} relevant stories")
            else:
                print("No relevant stories found in memory")
            
            return {
                'has_context': has_context,
                'context_summary': context_result.get('context_summary', ''),
                'relevant_stories': context_result.get('relevant_stories', []),
                'retrieval_info': {
                    'strategy': context_result.get('retrieval_strategy', 'unknown'),
                    'confidence': context_result.get('confidence', 0.0),
                    'stories_found': context_result.get('stories_found', 0)
                }
            }
            
        except Exception as e:
            print(f"Error retrieving chat context: {e}")
            return {
                'has_context': False,
                'context_summary': '',
                'relevant_stories': [],
                'retrieval_info': {'error': str(e)}
            }
    
    async def get_project_summary(self, project_name: str) -> Dict[str, Any]:
        """
        Get a comprehensive summary of a specific project
        """
        try:
            timeline = await self.memory_retriever.get_project_timeline(
                project_name=project_name,
                max_stories=20
            )
            
            return {
                'project_name': project_name,
                'total_activities': timeline['total_activities'],
                'date_range': timeline['date_range'],
                'timeline': timeline['timeline'],
                'has_data': timeline['total_activities'] > 0
            }
            
        except Exception as e:
            print(f"Error getting project summary: {e}")
            return {
                'project_name': project_name,
                'total_activities': 0,
                'date_range': 'Error',
                'timeline': [],
                'has_data': False
            }
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the memory system
        """
        try:
            stats = self.vector_manager.get_memory_stats()
            stats['system_status'] = 'healthy' if self.initialized else 'error'
            return stats
        except Exception as e:
            return {
                'system_status': 'error',
                'error': str(e),
                'total_stories': 0
            }
    
    async def search_memories(self, 
                            query: str, 
                            filters: Dict[str, Any] = None,
                            max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Direct memory search (useful for debugging/admin)
        """
        try:
            return await self.vector_manager.search_stories(
                query=query,
                top_k=max_results,
                filters=filters
            )
        except Exception as e:
            print(f"Error searching memories: {e}")
            return []
    
    def force_save_memory(self):
        """
        Force save all memory to disk
        """
        try:
            self.vector_manager.force_save()
            print("Memory forced to disk")
        except Exception as e:
            print(f"Error force saving memory: {e}")
    
    async def test_memory_system(self) -> Dict[str, Any]:
        """
        Test the memory system with a sample action (useful for debugging)
        """
        try:
            print("Testing memory system...")
            
            # Test recording an action
            test_success = await self.record_app_action(
                app_name="test",
                action="system_test",
                session_id="test_session",
                action_data={"test": True, "timestamp": datetime.now().isoformat()},
                session_context={"app_data": {"ideation": {"name": "TestApp", "category": "test"}}}
            )
            
            if not test_success:
                return {"status": "failed", "error": "Failed to record test action"}
            
            # Test retrieving context
            context = await self.get_context_for_chat("What is my test app?")
            
            # Clean up test story (optional)
            # Note: In production, you might want to keep test stories or have a separate test storage
            
            return {
                "status": "passed",
                "record_success": test_success,
                "retrieval_success": context['has_context'],
                "stories_in_memory": self.vector_manager.story_count
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}

# Global memory system instance (initialized in main.py)
memory_system: Optional[MemorySystem] = None

def get_memory_system() -> MemorySystem:
    """
    Get the global memory system instance
    """
    global memory_system
    if memory_system is None:
        memory_system = MemorySystem()
    return memory_system

async def initialize_memory_system(storage_path: str = "data/memory") -> MemorySystem:
    """
    Initialize the global memory system
    """
    global memory_system
    memory_system = MemorySystem(storage_path=storage_path)
    return memory_system