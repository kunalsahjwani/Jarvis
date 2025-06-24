# jarvis : AI-Powered App Development Orchestrator

## Project Overview

**Jarvis** is an intelligent AI orchestrator that addresses the critical gap in cross-app context sharing within the jarvis ecosystem. After experiencing the fragmented user experience where apps operate in isolation without shared memory or context, I developed this solution to create a unified, intelligent interface that remembers user interactions and provides seamless context across all applications.

## Problem Statement & Solution

### Core Problem
The current problems I identified and tackled:
- **Cross-app memory**: No shared context between different applications
- **Intelligent routing**: Manual navigation without understanding user intent
- **Persistent sessions**: Lost context when switching between apps
- **Workflow continuity**: Disjointed experience across the app development lifecycle

### AI Solution
jarvis  introduces intelligent app orchestration through:
- **RAG-Powered Memory System**: Persistent cross-session context using vector embeddings
- **AI-Driven Routing**: Pure AI decision making without hardcoded rules
- **Workflow Intelligence**: Seamless progression through ideation → development → design → marketing
- **Direct Service Integration**: MCP protocol for Gmail connectivity

---

## Advanced AI Engineering Techniques

### 1. Retrieval-Augmented Generation (RAG)

![Image](https://github.com/user-attachments/assets/1bc3f652-83fd-45ca-b766-de97368f9d51)
*Figure 1: RAG Memory System Architecture with Vector Embeddings and Semantic Search*
**Implementation**: Vector memory system using FAISS with Google Text Embeddings API
- **Story-Based Memory**: Converts user actions into searchable narratives
- **Semantic Search**: Natural language queries across project history
- **Context Injection**: Dynamically retrieves relevant past activities for current conversations
- **Cross-Session Persistence**: Maintains context across browser sessions and app switches

```python
class MemorySystem:
    async def get_context_for_chat(self, user_message: str):
        # Semantic search through user's project history
        relevant_stories = await self.vector_manager.search_stories(
            query=user_message, top_k=5
        )
        # AI-generated context summary for current conversation
        context_summary = await self.memory_retriever.generate_summary()
```

### 2. Model Context Protocol (MCP) Integration
**Gmail Direct Integration**: Bypasses traditional API limitations
- **Automatic Token Refresh**: Eliminates manual re-authentication
- **Cross-Platform Compatibility**: Windows ProactorEventLoop support
- **Real-Time Email Sending**: Direct MCP tool invocation for immediate delivery

```python
class GmailMCPClient:
    async def send_email_with_auto_refresh(self):
        # Proactive token refresh before expiry
        if self._should_refresh_token():
            await self._refresh_access_token()
        # Direct MCP tool invocation
        result = await send_tool.ainvoke(email_data)
```

### 3. Fine-Tuned Model Specialization
**Domain-Specific Code Generation**: Fine-tuned Qwen 2.5 Coder for Streamlit applications
- **Dual Strategy Architecture**: Gemini primary + specialized model fallback
- **Streamlit Optimization**: Trained specifically on Python/Streamlit patterns
- **Reliable Fallback**: Ensures code generation even when primary model fails

```python
class CodeAgent:
    async def generate_streamlit_app(self, app_idea):
        # Primary: Google Gemini (fast, reliable)
        if self.gemini_available:
            result = await self._generate_with_gemini()
        # Fallback: Fine-tuned specialized model
        if result is None and self.finetuned_available:
            result = await self._generate_with_finetuned()
```

### 4. Comprehensive Evaluation Metrics
**Model Performance Assessment**: ROUGE and BLEU evaluation frameworks
- **ROUGE Metrics**: Content overlap and recall measurement for story generation quality
- **BLEU Scores**: N-gram precision evaluation for code generation accuracy
- **Semantic Similarity**: Embedding-based quality assessment using cosine similarity
- **A/B Testing**: Comparative analysis of RAG vs non-RAG performance

---

## LLM Agent Architecture

![Image](https://github.com/user-attachments/assets/5e67bac5-7f32-4c84-887b-4fe8743f3830)
*Figure 2: Multi-Agent System with Central Router and Specialized Agents*



### Agent Specialization
- **Router Agent**: Fully AI-driven routing with zero hardcoded patterns
- **Code Agent**: Streamlit generation with dual model strategy
- **Leonardo Agent**: Marketing image generation with workflow-aware prompts
- **Email Agent**: Campaign generation with cross-app context
- **Story Writer**: Action-to-narrative conversion for searchable memory

---

## Model Selection & Reasoning

### Primary Models: Google Gemini 2.0 Flash
**Rationale**: Free tier for students with excellent performance
- Fast response times for real-time interactions
- Strong reasoning capabilities for routing decisions
- Reliable image generation for marketing materials
- Cost-effective for development and testing

### Fine-Tuned Model: Qwen 2.5 Coder (Hugging Face)
**Rationale**: Laptop-compatible model for specialized code generation
- Small enough to run locally (1.5B parameters)
- Optimized for Python/Streamlit code patterns
- Fine-tuned on custom dataset for domain expertise
- Provides reliable fallback when primary model unavailable

**Note**: In production environments, Claude or GPT-4 would provide superior reasoning capabilities, but Gemini's free tier makes it ideal for development and demonstration purposes.

### Technology Stack Justification
- **LangChain**: Agent orchestration and prompt management
- **FAISS**: Local vector storage for persistent memory
- **FastAPI**: High-performance async API framework
- **MCP Protocol**: Direct service integration without API rate limits

---

## Technical Implementation

### Core Features
1. **Intelligent Workflow Management**: Ideation → Vibe Studio → Design → Gmail Marketing
2. **Persistent Memory System**: RAG-powered context retention across sessions
3. **Zero-Pattern Routing**: Pure AI decision making without if/else chains
4. **Direct Gmail Integration**: MCP protocol for immediate email sending

### Architecture Highlights
```python
# RAG Memory Implementation
async def record_app_action(self, app_name, action, session_context):
    # Convert action to searchable story
    story = await self.story_writer.write_story(event_data)
    # Store in vector database with embeddings
    await self.vector_manager.add_story(story)

# MCP Gmail Integration
async def _refresh_access_token(self):
    # Automatic token refresh without browser interaction
    response = requests.post(self.token_refresh_url, data=refresh_data)
    # Update environment variables automatically
    set_key(env_path, "GOOGLE_ACCESS_TOKEN", new_token)
```

---

## Deployment & CI/CD

### AWS Infrastructure
**Production Deployment**: Containerized deployment on AWS
- **ECR (Elastic Container Registry)**: Docker image storage and versioning
- **EC2 Instance**: Application hosting with auto-scaling capabilities
- **Application Load Balancer**: Traffic distribution and health checks
- **CloudWatch**: Monitoring and logging for production insights

### CI/CD Pipeline
```yaml
# Automated deployment workflow
Build → Test → Push to ECR → Deploy to EC2 → Health Check
```

### Docker Strategy
```dockerfile
FROM python:3.11-slim
# Install Node.js for MCP support
RUN apt-get update && apt-get install -y nodejs npm
# Global MCP server installation
RUN npm install -g @peakmojo/mcp-server-headless-gmail
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+ (for MCP Gmail)
- Google API credentials
- Docker (optional)

### Quick Setup
```bash
git clone https://github.com/yourusername/jarvis.git
cd jarvis
pip install -r requirements.txt
npm install -g @peakmojo/mcp-server-headless-gmail

# Configure environment variables
cp .env.example .env
# Add your Google API credentials

# Run application
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker Deployment
```bash
docker-compose up --build
# Access at http://localhost:8000
```

---

## Key Innovations

### 1. Story-Driven Memory Architecture
Converts every user action into natural language narratives that are semantically searchable, enabling intelligent context retrieval across sessions.

### 2. Zero-Pattern AI Routing
Eliminated hardcoded routing rules in favor of pure AI understanding, allowing natural language navigation between apps.

### 3. Automatic OAuth Management
Implemented transparent token refresh for Gmail MCP, eliminating manual re-authentication workflows.

### 4. Dual Model Reliability
Primary-fallback strategy ensures consistent performance with specialized domain expertise when needed.

---

## Assignment Requirements Fulfillment

**Core Requirements**:
- AI agent orchestration using LangChain
- RESTful API development with FastAPI
- Complete Docker containerization
- Production-ready deployment solution

**Advanced Techniques**:
- **RAG Implementation**: Vector-based memory with semantic search
- **MCP Protocol**: Direct Gmail service integration
- **Fine-Tuned Models**: Specialized Streamlit code generation
- **Evaluation Metrics**: ROUGE, BLEU, and semantic similarity assessment

**Innovation**: Solving cross-app context fragmentation in jarvis through intelligent orchestration and persistent memory.

---

## API Documentation

- **Interactive Docs**: http://localhost:8000/docs
- **Health Monitoring**: http://localhost:8000/health
- **Memory Dashboard**: http://localhost:8000/memory

---

## Author
Kunal Sahjwani


This project demonstrates advanced AI engineering practices while solving real-world problems in app orchestration and context management, showcasing technical proficiency suitable for Jarvis.
