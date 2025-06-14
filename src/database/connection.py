# src/database/connection.py - Updated to create tables
"""
Database connection and initialization for Steve Connect
Handles PostgreSQL with pgvector setup
"""

import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

# TODO: Update this URL if you change database credentials in .env
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    # Convert to async URL
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # TODO: Set to False in production for less verbose logs
    future=True
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for SQLAlchemy models
Base = declarative_base()

async def init_database():
    """
    Initialize database connection and create tables
    """
    try:
        async with engine.begin() as conn:
            # Test basic connection
            result = await conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            
            # Check for pgvector extension (optional)
            try:
                result = await conn.execute(
                    text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')")
                )
                has_vector = result.scalar()
                if has_vector:
                    print("✅ pgvector extension is available")
                else:
                    print("⚠️ pgvector extension not found (will use text storage)")
            except Exception as e:
                print(f"⚠️ Could not check pgvector extension: {e}")
            
            # Import models to ensure they're registered with Base
            from src.database.models import Session, ContextMemory, AppState, KnowledgeBase
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Database tables created successfully")
                
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise

async def get_db():
    """
    Dependency function to get database session
    Use this in your FastAPI route dependencies
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()

async def close_database():
    """
    Close database connections (useful for testing or shutdown)
    """
    await engine.dispose()