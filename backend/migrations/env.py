import os
import sys
from logging.config import fileConfig

# ------------------------------------------------------------------------
# 0. Tell db.py we’re in Alembic context so it skips async_engine creation
# ------------------------------------------------------------------------
os.environ["ALEMBIC_CONTEXT"] = "1"

# ------------------------------------------------------------------------
# 1. Load .env for DATABASE_URL
# ------------------------------------------------------------------------
from dotenv import load_dotenv
here = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(here, ".."))
load_dotenv(os.path.join(project_root, ".env"))

# ------------------------------------------------------------------------
# 2. Alembic config & logging
# ------------------------------------------------------------------------
from alembic import context
config = context.config
fileConfig(config.config_file_name)

# ------------------------------------------------------------------------
# 3. Override SQLA URL from .env, stripping any async driver suffix
# ------------------------------------------------------------------------
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise RuntimeError("DATABASE_URL not set in .env")

# remove any async driver markers
sync_url = database_url.replace("+asyncpg", "").replace("+psycopg2", "")
config.set_main_option("sqlalchemy.url", sync_url)

# ------------------------------------------------------------------------
# 4. Import your MetaData (and models!) so autogenerate sees all tables
# ------------------------------------------------------------------------
sys.path.append(project_root)
from db import Base           # SQLAlchemy Base
import models                 # ensure all model classes are registered on Base.metadata
target_metadata = Base.metadata

# ------------------------------------------------------------------------
# 5. Offline migrations
# ------------------------------------------------------------------------
def run_migrations_offline():
    """Run migrations without DB connection."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

# ------------------------------------------------------------------------
# 6. Online migrations (sync engine)
# ------------------------------------------------------------------------
from sqlalchemy import create_engine, pool

def run_migrations_online():
    """Run migrations with a live DB connection."""
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with connection.begin():
            context.run_migrations()

# ------------------------------------------------------------------------
# 7. Choose mode and execute
# ------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
