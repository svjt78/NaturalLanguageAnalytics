# backend/agents/analyst_agent.py
from sqlalchemy import select, delete
from db import SessionLocal
from models import ColumnMeta, ColumnDictionary, Metric
import asyncio

async def analyst_agent(table_name: str):
    """
    Generate simple heuristic-based metrics for each column and insert into `metrics`.
    """
    async with SessionLocal() as session:
        # Fetch columns + descriptions
        result = await session.execute(
            select(ColumnMeta, ColumnDictionary.description)
            .join(ColumnDictionary, ColumnMeta.id == ColumnDictionary.column_id)
            .where(ColumnMeta.table_name == table_name)
        )
        rows = result.all()

        # Delete existing metrics for this table
        await session.execute(
            delete(Metric).where(Metric.metric_name.startswith(f"{table_name}."))
        )

        for col_meta, desc in rows:
            col = col_meta.column_name

            # Numeric → SUM, AVG
            if col_meta.is_numeric:
                sum_name = f"{table_name}.{col}_sum"
                avg_name = f"{table_name}.{col}_avg"
                sum_sql = f"SELECT SUM(\"{col}\") AS \"sum_{col}\" FROM \"{table_name}\""
                avg_sql = f"SELECT AVG(\"{col}\") AS \"avg_{col}\" FROM \"{table_name}\""

                await session.execute(
                    """
                    INSERT INTO metrics (metric_name, sql_definition, viz_hint, tags)
                    VALUES (:name, :sql, :viz, :tags)
                    """,
                    {
                        "name": sum_name,
                        "sql": sum_sql,
                        "viz": {"x": None, "y": f"sum_{col}", "type": "numeric"},
                        "tags": [table_name, col, "sum"]
                    }
                )
                await session.execute(
                    """
                    INSERT INTO metrics (metric_name, sql_definition, viz_hint, tags)
                    VALUES (:name, :sql, :viz, :tags)
                    """,
                    {
                        "name": avg_name,
                        "sql": avg_sql,
                        "viz": {"x": None, "y": f"avg_{col}", "type": "numeric"},
                        "tags": [table_name, col, "avg"]
                    }
                )

            # Datetime → daily counts
            elif col_meta.is_datetime:
                daily_name = f"{table_name}.{col}_count_per_day"
                daily_sql = (
                    f"SELECT DATE(\"{col}\") AS day, COUNT(*) AS count "
                    f"FROM \"{table_name}\" GROUP BY DATE(\"{col}\") ORDER BY day"
                )
                await session.execute(
                    """
                    INSERT INTO metrics (metric_name, sql_definition, viz_hint, tags)
                    VALUES (:name, :sql, :viz, :tags)
                    """,
                    {
                        "name": daily_name,
                        "sql": daily_sql,
                        "viz": {"x": "day", "y": "count", "type": "line"},
                        "tags": [table_name, col, "time-series"]
                    }
                )

            # Categorical → top-20 counts
            else:
                distinct_name = f"{table_name}.{col}_distinct_count"
                distinct_sql = (
                    f"SELECT \"{col}\" AS category, COUNT(*) AS count "
                    f"FROM \"{table_name}\" GROUP BY \"{col}\" ORDER BY count DESC LIMIT 20"
                )
                await session.execute(
                    """
                    INSERT INTO metrics (metric_name, sql_definition, viz_hint, tags)
                    VALUES (:name, :sql, :viz, :tags)
                    """,
                    {
                        "name": distinct_name,
                        "sql": distinct_sql,
                        "viz": {"x": "category", "y": "count", "type": "bar"},
                        "tags": [table_name, col, "categorical"]
                    }
                )
        await session.commit()
