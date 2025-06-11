# backend/db.py

import os
from dotenv import load_dotenv
import trio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Load environment variables from .env
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in .env")

# 2. Detect if we’re running inside Alembic migrations
#    (we’ll set ALEMBIC_CONTEXT=1 in migrations/env.py)
_IS_MIGRATING = os.getenv("ALEMBIC_CONTEXT") == "1"

# 3. Only create the async engine & sessionmaker when not migrating
if not _IS_MIGRATING:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        future=True
    )
    SessionLocal = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False
    )
else:
    engine = None
    SessionLocal = None

# 4. Concurrency limiter for LangGraph runs (max 3 concurrent pipelines)
langgraph_semaphore = trio.CapacityLimiter(3)

# 5. Base model for SQLAlchemy
Base = declarative_base()
