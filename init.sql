-- init.sql - Update the metadata column name
-- Enable the pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Create our main tables for the Steve Connect system

-- Sessions table - tracks user conversation sessions
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Context memory table - stores conversation context across apps
CREATE TABLE IF NOT EXISTS context_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    app_name VARCHAR(100) NOT NULL,
    context_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Knowledge base table - for RAG agent (app capabilities, documentation)
CREATE TABLE IF NOT EXISTS knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    meta_data JSONB,  -- Changed from metadata to meta_data
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- App states table - tracks which app is currently active
CREATE TABLE IF NOT EXISTS app_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    current_app VARCHAR(100),
    previous_app VARCHAR(100),
    state_data JSONB,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_context_session_id ON context_memory(session_id);
CREATE INDEX IF NOT EXISTS idx_context_app_name ON context_memory(app_name);
CREATE INDEX IF NOT EXISTS idx_knowledge_embedding ON knowledge_base USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_app_states_session_id ON app_states(session_id);

-- Insert some initial knowledge base data for our apps
INSERT INTO knowledge_base (content, meta_data) VALUES 
('Ideation app helps users brainstorm and categorize product ideas across domains like Digital Product, Finance, Services, Healthcare, Education, Entertainment, Travel, Food & Beverage, Telecommunication, Automotive, IT/Technology, and Fashion.', 
 '{"app": "ideation", "category": "capabilities"}'),

('Vibe Studio is an AI-powered Streamlit app builder that generates complete UI code, debugs applications, and creates web app interfaces based on user prompts and ideas.', 
 '{"app": "vibe_studio", "category": "capabilities"}'),

('Design app integrates with AI image generation to create marketing images, logos, and visual content based on user ideas and prompts.', 
 '{"app": "design", "category": "capabilities"}'),

('Gmail integration helps draft marketing emails, manage contact lists, and send promotional content for app launches.', 
 '{"app": "gmail", "category": "capabilities"}');