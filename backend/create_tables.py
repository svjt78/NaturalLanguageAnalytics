#!/usr/bin/env python

import os
import sys

# ------------------------------------------------------------------------
# 0. Tell db.py we’re in migration mode (skip async engine creation)
# ------------------------------------------------------------------------
os.environ["ALEMBIC_CONTEXT"] = "1"

# ------------------------------------------------------------------------
# 1. Load .env so DATABASE_URL is available
# ------------------------------------------------------------------------
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ------------------------------------------------------------------------
# 2. Read and sanitize the sync URL
# ------------------------------------------------------------------------
database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("❌ DATABASE_URL not set in .env")
    sys.exit(1)

# Strip any async driver markers (+asyncpg, +psycopg2)
sync_url = database_url.replace("+asyncpg", "").replace("+psycopg2", "")

# ------------------------------------------------------------------------
# 3. Import Base and your models (so metadata is populated)
# ------------------------------------------------------------------------
# Ensure backend/ directory is on the path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from db import Base    # db.py defines Base
import models          # models.py registers all ORM classes on Base.metadata

# ------------------------------------------------------------------------
# 4. Create a synchronous engine & create all tables
# ------------------------------------------------------------------------
from sqlalchemy import create_engine

engine = create_engine(sync_url, echo=True, future=True)
Base.metadata.create_all(engine)

print("✅ All tables created (or already existed).")
