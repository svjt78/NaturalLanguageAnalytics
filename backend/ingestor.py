# backend/ingestor.py
import io
import pandas as pd
import re
from sqlalchemy import text
from db import engine
from sqlalchemy.ext.asyncio import AsyncConnection

class Ingestor:
    """
    Ingest CSV or Excel file into Postgres as a new table / replace / append.
    """

    @staticmethod
    def _sanitize_col(col: str) -> str:
        sanitized = re.sub(r"[^0-9a-zA-Z_]+", "_", col.strip().lower())
        if sanitized and sanitized[0].isdigit():
            sanitized = "_" + sanitized
        return sanitized

    @staticmethod
    async def ingest_file(file_bytes: bytes, filename: str, mode: str, target_table: str = None, user: str = "anonymous"):
        """
        file_bytes: raw bytes of CSV or Excel
        filename: original filename
        mode: "create", "replace", or "append"
        target_table: required for replace/append
        """
        # 1. Load into pandas DataFrame(s)
        if filename.lower().endswith((".xlsx", ".xls")):
            xls = pd.read_excel(io.BytesIO(file_bytes), sheet_name=None, engine="openpyxl")
            tables = {sheet: df for sheet, df in xls.items()}
        else:
            df = pd.read_csv(io.BytesIO(file_bytes))
            tables = {"sheet1": df}

        loaded_tables = []
        async with engine.begin() as conn:  # type: AsyncConnection
            for sheet_name, df in tables.items():
                # 2. Sanitize column names
                df.columns = [Ingestor._sanitize_col(c) for c in df.columns]

                # 3. Determine new table name
                if mode == "create":
                    base_name = sheet_name.lower()
                    table_name = base_name
                    suffix = 0
                    while True:
                        exists = await conn.execute(text("SELECT to_regclass(:tbl)"), {"tbl": table_name})
                        if exists.scalar() is None:
                            break
                        suffix += 1
                        table_name = f"{base_name}_{suffix}"
                else:
                    if not target_table:
                        raise ValueError("target_table required for replace/append")
                    table_name = target_table

                # 4. Replace vs Append logic
                if mode == "replace":
                    await conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE;'))

                # 5. Create if needed
                if mode == "create":
                    col_types = []
                    sample = df.head(1000)
                    for col, ser in sample.items():
                        dtype = "TEXT"
                        if pd.api.types.is_integer_dtype(ser.dropna()):
                            dtype = "BIGINT"
                        elif pd.api.types.is_float_dtype(ser.dropna()):
                            dtype = "DOUBLE PRECISION"
                        elif pd.api.types.is_datetime64_any_dtype(ser.dropna()):
                            dtype = "TIMESTAMP"
                        col_types.append(f'"{col}" {dtype}')
                    cols_ddl = ", ".join(col_types)
                    create_sql = f'CREATE TABLE "{table_name}" ({cols_ddl});'
                    await conn.execute(text(create_sql))

                # 6. COPY data
                tmp_buffer = io.StringIO()
                df.to_csv(tmp_buffer, index=False, header=True)
                tmp_buffer.seek(0)
                copy_sql = f'COPY "{table_name}" FROM STDIN WITH (FORMAT csv, HEADER true);'
                await conn.connection.copy_expert(copy_sql, tmp_buffer)

                # 7. ANALYZE table
                await conn.execute(text(f'ANALYZE "{table_name}";'))

                # 8. Record ingestion history
                row_count = len(df)
                await conn.execute(
                    text("""
                    INSERT INTO ingest_history (table_name, mode, file_name, row_count, loaded_by)
                    VALUES (:tbl, :mode, :fname, :rows, :user)
                    """),
                    {
                        "tbl": table_name,
                        "mode": mode,
                        "fname": filename,
                        "rows": row_count,
                        "user": user
                    }
                )

                loaded_tables.append(table_name)

        return loaded_tables
