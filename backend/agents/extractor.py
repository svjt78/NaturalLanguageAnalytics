# backend/agents/extractor.py
from sqlalchemy import inspect, delete
from db import SessionLocal
from models import ColumnMeta
import asyncio

async def extractor_agent(table_name: str):
    """
    Extract column metadata from Postgres table and persist into `columns`.
    """
    async with SessionLocal() as session:
        engine = session.bind
        insp = inspect(engine.sync_engine)
        columns = insp.get_columns(table_name)

        # Delete any existing metadata for this table
        await session.execute(
            delete(ColumnMeta).where(ColumnMeta.table_name == table_name)
        )

        # Insert fresh rows
        for col in columns:
            dtype = col["type"].__class__.__name__.lower()
            is_num = "int" in dtype or "double" in dtype or "numeric" in dtype
            is_dt = "date" in dtype or "time" in dtype
            await session.execute(
                """
                INSERT INTO columns (table_name, column_name, data_type, is_numeric, is_datetime)
                VALUES (:tbl, :col, :dt, :num, :dtm)
                """,
                {
                    "tbl": table_name,
                    "col": col["name"],
                    "dt": dtype,
                    "num": is_num,
                    "dtm": is_dt
                }
            )
        await session.commit()
