# src/memory/vector_memory_manager.py
"""
Vector Memory Manager - Handles embedding, storage, and retrieval of user stories
Uses FAISS for local vector storage with Google Embeddings API
"""

import os
import json
import pickle
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import faiss
from pathlib import Path
from google.generativeai import embed_content
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class VectorMemoryManager:
    """
    Manages vector storage and retrieval of user stories using FAISS
    """
    
    def __init__(self, storage_path: str = "data/memory"):
        """
        Initialize vector memory manager
        
        Args:
            storage_path: Directory to store FAISS index and metadata
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.index_path = self.storage_path / "stories.index"
        self.metadata_path = self.storage_path / "stories_metadata.json"
        self.stories_path = self.storage_path / "stories_text.json"
        
        # Initialize Google AI for embeddings
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        
        # Vector configuration
        self.embedding_dimension = 768  # Google's text-embedding dimension
        self.max_stories = 10000  # Maximum stories to store
        
        # Initialize or load existing index
        self.index = None
        self.stories_metadata = []
        self.stories_text = []
        self.story_count = 0
        
        self._initialize_storage()
        
        print(f"Vector Memory Manager initialized with {self.story_count} existing stories")
    
    def _initialize_storage(self):
        """
        Initialize or load existing FAISS index and metadata
        """
        if self.index_path.exists() and self.metadata_path.exists():
            # Load existing index and metadata
            self._load_existing_storage()
        else:
            # Create new index
            self._create_new_storage()
    
    def _create_new_storage(self):
        """
        Create new FAISS index and storage files
        """
        # Create FAISS index (using IndexFlatIP for cosine similarity)
        self.index = faiss.IndexFlatIP(self.embedding_dimension)
        
        # Initialize empty storage
        self.stories_metadata = []
        self.stories_text = []
        self.story_count = 0
        
        print("Created new vector memory storage")
    
    def _load_existing_storage(self):
        """
        Load existing FAISS index and metadata from disk
        """
        try:
            # Load FAISS index
            self.index = faiss.read_index(str(self.index_path))
            
            # Load metadata
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                self.stories_metadata = json.load(f)
            
            # Load story texts
            with open(self.stories_path, 'r', encoding='utf-8') as f:
                self.stories_text = json.load(f)
            
            self.story_count = len(self.stories_metadata)
            
            print(f"Loaded existing vector memory with {self.story_count} stories")
            
        except Exception as e:
            print(f"Error loading existing storage: {e}")
            print("Creating new storage...")
            self._create_new_storage()
    
    def _save_storage(self):
        """
        Save FAISS index and metadata to disk
        """
        try:
            # Save FAISS index
            faiss.write_index(self.index, str(self.index_path))
            
            # Save metadata
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.stories_metadata, f, indent=2, ensure_ascii=False)
            
            # Save story texts
            with open(self.stories_path, 'w', encoding='utf-8') as f:
                json.dump(self.stories_text, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            print(f"Error saving storage: {e}")
    
    async def add_story(self, story_data: Dict[str, Any]) -> bool:
        """
        Add a new story to vector memory
        
        Args:
            story_data: {
                'story_text': 'The narrative text',
                'metadata': {...},
                'story_id': 'unique_id'
            }
        
        Returns:
            bool: Success status
        """
        try:
            story_text = story_data.get('story_text', '')
            metadata = story_data.get('metadata', {})
            story_id = story_data.get('story_id', f"story_{len(self.stories_text)}")
            
            if not story_text:
                print("Warning: Empty story text, skipping...")
                return False
            
            # Generate embedding
            embedding = await self._generate_embedding(story_text)
            if embedding is None:
                return False
            
            # Add to FAISS index
            embedding_array = np.array([embedding]).astype('float32')
            # Normalize for cosine similarity
            faiss.normalize_L2(embedding_array)
            self.index.add(embedding_array)
            
            # Store metadata and text
            enhanced_metadata = {
                **metadata,
                'story_id': story_id,
                'added_timestamp': datetime.now().isoformat(),
                'vector_index': self.story_count
            }
            
            self.stories_metadata.append(enhanced_metadata)
            self.stories_text.append(story_text)
            self.story_count += 1
            
            # Save to disk after every story for immediate persistence
            self._save_storage()
            
            print(f"Added story to vector memory: {story_id} (saved to disk)")
            return True
            
        except Exception as e:
            print(f"Error adding story to vector memory: {e}")
            return False
    
    async def search_stories(self, 
                           query: str, 
                           top_k: int = 5, 
                           filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Search for relevant stories based on query
        
        Args:
            query: Search query text
            top_k: Number of results to return
            filters: Optional filters like {'app_name': 'vibe_studio', 'project_name': 'Aktasks'}
        
        Returns:
            List of matching stories with scores
        """
        try:
            if self.story_count == 0:
                return []
            
            # Generate query embedding
            query_embedding = await self._generate_embedding(query)
            if query_embedding is None:
                return []
            
            # Search FAISS index
            query_array = np.array([query_embedding]).astype('float32')
            faiss.normalize_L2(query_array)
            
            # Get more results than needed for filtering
            search_k = min(top_k * 3, self.story_count)
            scores, indices = self.index.search(query_array, search_k)
            
            # Collect results with metadata
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx >= len(self.stories_metadata):
                    continue
                
                metadata = self.stories_metadata[idx]
                story_text = self.stories_text[idx]
                
                # Apply filters if provided
                if filters and not self._matches_filters(metadata, filters):
                    continue
                
                result = {
                    'story_text': story_text,
                    'metadata': metadata,
                    'similarity_score': float(score),
                    'rank': len(results) + 1
                }
                
                results.append(result)
                
                # Stop when we have enough results
                if len(results) >= top_k:
                    break
            
            return results
            
        except Exception as e:
            print(f"Error searching stories: {e}")
            return []
    
    async def search_by_timeframe(self, 
                                days_back: int = 7, 
                                top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent stories within a timeframe
        """
        try:
            cutoff_date = datetime.now().timestamp() - (days_back * 24 * 60 * 60)
            
            recent_stories = []
            for i, metadata in enumerate(self.stories_metadata):
                story_timestamp = metadata.get('timestamp', '')
                if story_timestamp:
                    try:
                        story_time = datetime.fromisoformat(story_timestamp.replace('Z', '+00:00')).timestamp()
                        if story_time >= cutoff_date:
                            recent_stories.append({
                                'story_text': self.stories_text[i],
                                'metadata': metadata,
                                'similarity_score': 1.0,  # Perfect match for time-based queries
                                'rank': len(recent_stories) + 1
                            })
                    except:
                        continue
            
            # Sort by timestamp (newest first) and limit
            recent_stories.sort(key=lambda x: x['metadata'].get('timestamp', ''), reverse=True)
            return recent_stories[:top_k]
            
        except Exception as e:
            print(f"Error searching by timeframe: {e}")
            return []
    
    async def search_by_project(self, 
                              project_name: str, 
                              top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Get all stories related to a specific project
        """
        filters = {'project_name': project_name.lower()}
        return await self.search_stories(f"project {project_name}", top_k=top_k, filters=filters)
    
    def _matches_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """
        Check if metadata matches provided filters
        """
        for filter_key, filter_value in filters.items():
            metadata_value = metadata.get(filter_key, '').lower()
            filter_value_lower = str(filter_value).lower()
            
            if filter_value_lower not in metadata_value:
                return False
        
        return True
    
    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for text using Google's embedding API
        """
        try:
            result = embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document"
            )
            
            return result['embedding']
            
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the memory storage
        """
        if self.story_count == 0:
            return {
                'total_stories': 0,
                'storage_size_mb': 0,
                'apps_covered': [],
                'projects_covered': [],
                'date_range': 'No stories yet'
            }
        
        # Analyze metadata
        apps = set()
        projects = set()
        timestamps = []
        
        for metadata in self.stories_metadata:
            apps.add(metadata.get('app_name', 'unknown'))
            projects.add(metadata.get('project_name', 'unknown'))
            
            timestamp = metadata.get('timestamp', '')
            if timestamp:
                timestamps.append(timestamp)
        
        # Calculate storage size
        storage_size = 0
        for file_path in [self.index_path, self.metadata_path, self.stories_path]:
            if file_path.exists():
                storage_size += file_path.stat().st_size
        
        storage_size_mb = storage_size / (1024 * 1024)
        
        # Date range
        date_range = 'No dates available'
        if timestamps:
            timestamps.sort()
            start_date = timestamps[0][:10]  # Just the date part
            end_date = timestamps[-1][:10]
            date_range = f"{start_date} to {end_date}"
        
        return {
            'total_stories': self.story_count,
            'storage_size_mb': round(storage_size_mb, 2),
            'apps_covered': list(apps),
            'projects_covered': list(projects),
            'date_range': date_range
        }
    
    def force_save(self):
        """
        Force save current state to disk
        """
        self._save_storage()
        print("Memory storage saved to disk")
    
    def clear_memory(self, confirm: bool = False):
        """
        Clear all stored memories (use with caution!)
        """
        if not confirm:
            print("Use clear_memory(confirm=True) to actually clear the memory")
            return
        
        # Remove files
        for file_path in [self.index_path, self.metadata_path, self.stories_path]:
            if file_path.exists():
                file_path.unlink()
        
        # Reset in-memory storage
        self._create_new_storage()
        
        print("All memory storage cleared!")
    
    async def add_batch_stories(self, stories: List[Dict[str, Any]]) -> int:
        """
        Add multiple stories in batch for better performance
        """
        success_count = 0
        
        for story in stories:
            if await self.add_story(story):
                success_count += 1
        
        # Force save after batch
        self._save_storage()
        
        print(f"Added {success_count}/{len(stories)} stories to memory")
        return success_count