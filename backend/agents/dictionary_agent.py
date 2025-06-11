# backend/agents/dictionary_agent.py
import os
import openai
from sqlalchemy import select, update
from db import SessionLocal
from models import ColumnMeta, ColumnDictionary
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

async def dictionary_agent(table_name: str):
    """
    Generate descriptions for each column in `columns` table, upsert into `column_dictionary`.
    """
    async with SessionLocal() as session:
        result = await session.execute(
            select(ColumnMeta).where(ColumnMeta.table_name == table_name)
        )
        cols = result.scalars().all()

        for col in cols:
            prompt = (
                f"Describe the following database column in a brief, developer-friendly way:\n"
                f"Table: {table_name}\n"
                f"Column: {col.column_name}\n"
                f"Data Type: {col.data_type}\n"
                f"Include typical use cases or units if applicable."
            )
            resp = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            desc = resp.choices[0].message.content.strip()

            existing = await session.execute(
                select(ColumnDictionary).where(ColumnDictionary.column_id == col.id)
            )
            if existing.scalar_one_or_none():
                await session.execute(
                    update(ColumnDictionary)
                    .where(ColumnDictionary.column_id == col.id)
                    .values(description=desc)
                )
            else:
                await session.execute(
                    """
                    INSERT INTO column_dictionary (column_id, description)
                    VALUES (:cid, :desc)
                    """,
                    {"cid": col.id, "desc": desc}
                )
        await session.commit()
