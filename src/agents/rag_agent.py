# src/agents/rag_agent.py - Fixed version
"""
RAG Agent - Retrieval Augmented Generation for Steve Connect
Provides knowledge about app capabilities and helps with intelligent routing
Uses pgvector for semantic search of knowledge base
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import numpy as np
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv

from src.database.models import KnowledgeBase
from src.database.connection import AsyncSessionLocal

load_dotenv()

class RAGAgent:
    """
    RAG agent for knowledge retrieval about Steve OS apps and capabilities
    """
    
    # src/agents/rag_agent.py
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",  # 🔧 Latest model
            temperature=0.3,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            convert_system_message_to_human=True
        )
        
        # Cache for embeddings to avoid recomputation
        self.embedding_cache = {}
    
    async def initialize_knowledge_base(self):
        """
        Initialize the knowledge base with app information
        This runs once when the system starts
        """
        try:
            async with AsyncSessionLocal() as db:
                # Check if knowledge base is already populated
                result = await db.execute(select(KnowledgeBase).limit(1))
                existing_knowledge = result.scalar_one_or_none()
                
                if existing_knowledge:
                    print("✅ Knowledge base already populated")
                    return
                
                # Define initial knowledge about Steve OS apps
                app_knowledge = [
                    {
                        "content": "Ideation app helps users brainstorm product ideas across multiple categories including Digital Product, Finance, Services, Healthcare, Education, Entertainment, Travel, Food & Beverage, Telecommunication, Automotive, IT/Technology, and Fashion. Users can select categories and develop detailed concepts.",
                        "metadata": {"app": "ideation", "category": "capabilities", "keywords": ["brainstorm", "ideas", "categories", "product"]}
                    },
                    {
                        "content": "Vibe Studio is an AI-powered Streamlit app development platform that generates complete UI code, debugs applications, and creates web app interfaces. It takes user prompts and ideas to generate working Streamlit/Python code with modern UI components.",
                        "metadata": {"app": "vibe_studio", "category": "capabilities", "keywords": ["streamlit", "code", "web", "ui", "development"]}
                    },
                    {
                        "content": "Design app integrates with AI image generation to create marketing materials, logos, app icons, and promotional images. It helps users visualize their products and create professional marketing content using Stable Diffusion.",
                        "metadata": {"app": "design", "category": "capabilities", "keywords": ["images", "marketing", "logos", "visual", "graphics"]}
                    },
                    {
                        "content": "Gmail integration helps users draft professional marketing emails, manage contact lists, and send promotional campaigns for product launches. It can create compelling email content based on project context.",
                        "metadata": {"app": "gmail", "category": "capabilities", "keywords": ["email", "marketing", "campaigns", "contacts", "launch"]}
                    },
                    {
                        "content": "Typical workflow in Steve OS: Start with Ideation to brainstorm concepts → Move to Vibe Studio to build the actual app → Use Design app for marketing materials → Finally use Gmail to launch and promote the product.",
                        "metadata": {"app": "workflow", "category": "process", "keywords": ["workflow", "process", "sequence", "steps"]}
                    },
                    {
                        "content": "When users say 'I want to create an app' or 'I have an idea', they should typically start with the Ideation app first to properly develop their concept before moving to development.",
                        "metadata": {"app": "routing", "category": "decision_making", "keywords": ["create", "idea", "start", "new"]}
                    },
                    {
                        "content": "When users say 'let's build it' or 'start developing' after ideation, they should be routed to Vibe Studio for actual code generation and app development.",
                        "metadata": {"app": "routing", "category": "decision_making", "keywords": ["build", "develop", "code", "create"]}
                    },
                    {
                        "content": "When users want to 'market the app', 'create visuals', or 'make images', they should be routed to the Design app for marketing material creation.",
                        "metadata": {"app": "routing", "category": "decision_making", "keywords": ["market", "visual", "image", "design", "promote"]}
                    },
                    {
                        "content": "When users want to 'launch', 'send emails', or 'contact users', they should be routed to Gmail for email marketing and communication.",
                        "metadata": {"app": "routing", "category": "decision_making", "keywords": ["launch", "email", "contact", "send", "promote"]}
                    }
                ]
                
                # Store knowledge without embeddings for now
                for knowledge in app_knowledge:
                    kb_entry = KnowledgeBase(
                        content=knowledge["content"],
                        meta_data=knowledge["metadata"],
                        embedding=""  # Empty string for now
                    )
                    
                    db.add(kb_entry)
                
                await db.commit()
                print("✅ Knowledge base initialized with app information")
                
        except Exception as e:
            print(f"❌ Error initializing knowledge base: {e}")
            raise
    
    async def search_knowledge(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search knowledge base using text search (fallback when no vector search)
        """
        try:
            async with AsyncSessionLocal() as db:
                # Simple text search fallback
                result = await db.execute(
                    text("""
                    SELECT content, meta_data
                    FROM knowledge_base
                    WHERE LOWER(content) LIKE LOWER(:query)
                    ORDER BY created_at DESC
                    LIMIT :limit
                    """),
                    {
                        "query": f"%{query}%",
                        "limit": limit
                    }
                )
                
                knowledge_results = []
                for row in result:
                    knowledge_results.append({
                        "content": row.content,
                        "meta_data": row.meta_data,
                        "similarity_score": 0.8  # Fixed score for text search
                    })
                
                return knowledge_results
                
        except Exception as e:
            print(f"Error searching knowledge base: {e}")
            return []
    
    async def get_app_capabilities(self, app_name: str) -> str:
        """
        Get specific capabilities for an app
        """
        try:
            query = f"What can the {app_name} app do? Capabilities and features"
            results = await self.search_knowledge(query, limit=3)
            
            if not results:
                return f"Information about {app_name} app capabilities."
            
            # Combine relevant results
            capabilities = []
            for result in results:
                if result["meta_data"].get("app") == app_name or app_name in result["content"].lower():
                    capabilities.append(result["content"])
            
            return " ".join(capabilities) if capabilities else results[0]["content"]
            
        except Exception as e:
            print(f"Error getting app capabilities: {e}")
            return f"General capabilities for {app_name} app."
    
    async def enhance_routing_decision(self, user_message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Use RAG to enhance routing decisions with knowledge about apps
        """
        try:
            # Search for relevant routing knowledge
            routing_results = await self.search_knowledge(
                f"routing decision for: {user_message}",
                limit=3
            )
            
            # Get workflow knowledge
            workflow_results = await self.search_knowledge(
                "workflow process steps sequence",
                limit=2
            )
            
            # Combine knowledge for enhanced decision making
            knowledge_context = []
            
            for result in routing_results + workflow_results:
                if result["similarity_score"] > 0.5:  # Lower threshold for text search
                    knowledge_context.append(result["content"])
            
            # Generate enhanced routing recommendation
            if knowledge_context:
                system_prompt = f"""
                You are Steve's routing expert. Based on the knowledge about Steve OS apps and typical workflows, 
                provide routing recommendations.
                
                Knowledge context:
                {' '.join(knowledge_context)}
                
                User message: "{user_message}"
                Current context: {context or 'No previous context'}
                
                Provide a routing recommendation with confidence score (0-1) and reasoning.
                Format: {{"recommendation": "app_name", "confidence": 0.8, "reasoning": "explanation"}}
                """
                
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_message)
                ]
                
                response = await self.llm.ainvoke(messages)
                
                return {
                    "enhanced_knowledge": knowledge_context,
                    "recommendation": response.content,
                    "knowledge_confidence": len([r for r in routing_results if r["similarity_score"] > 0.5]) / max(len(routing_results), 1)
                }
            
            return {"enhanced_knowledge": [], "recommendation": None, "knowledge_confidence": 0}
            
        except Exception as e:
            print(f"Error enhancing routing decision: {e}")
            return {"enhanced_knowledge": [], "recommendation": None, "knowledge_confidence": 0}
    
    async def add_knowledge(self, content: str, metadata: Dict[str, Any]):
        """
        Add new knowledge to the knowledge base
        """
        try:
            async with AsyncSessionLocal() as db:
                kb_entry = KnowledgeBase(
                    content=content,
                    meta_data=metadata,
                    embedding=""  # Empty for now
                )
                
                db.add(kb_entry)
                await db.commit()
                
                print(f"✅ Added new knowledge: {content[:50]}...")
                
        except Exception as e:
            print(f"Error adding knowledge: {e}")
            raise