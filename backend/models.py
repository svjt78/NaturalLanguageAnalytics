# backend/models.py
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, TIMESTAMP,
    JSON, UniqueConstraint, ForeignKey
)
from sqlalchemy.orm import relationship
from db import Base
import datetime

class ColumnMeta(Base):
    __tablename__ = "columns"
    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String, index=True)
    column_name = Column(String)
    data_type = Column(String)
    is_numeric = Column(Boolean)
    is_datetime = Column(Boolean)

    __table_args__ = (UniqueConstraint("table_name", "column_name", name="uq_table_column"),)

class ColumnDictionary(Base):
    __tablename__ = "column_dictionary"
    column_id = Column(Integer, ForeignKey("columns.id", ondelete="CASCADE"), primary_key=True)
    description = Column(Text)
    updated_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)

class Metric(Base):
    __tablename__ = "metrics"
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String, unique=True, index=True)
    sql_definition = Column(Text)
    viz_hint = Column(JSON)       # e.g. { "x": "order_date", "y": "SUM(total)", "type": "bar" }
    importance_score = Column(Integer, default=0)
    tags = Column(JSON)           # e.g. ["table", "column", "sum"]

class IngestHistory(Base):
    __tablename__ = "ingest_history"
    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String)
    mode = Column(String)                # 'create', 'replace', 'append'
    file_name = Column(String)
    row_count = Column(Integer)
    loaded_by = Column(String)
    loaded_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
