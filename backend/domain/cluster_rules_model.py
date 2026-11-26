from sqlalchemy import Boolean, Column, DateTime, Float, Integer, JSON, String, Table

from core.db import metadata


cluster_rules = Table('cluster_rules', metadata,
    Column('code', String(64), primary_key=True),
    Column('version', Integer, nullable=False, unique=True),
    Column('threshold', Float, nullable=False),
    Column('state', String(16), nullable=False),
    Column('created_by', String(100), nullable=False),
    Column('created_at', DateTime, nullable=False),
)


cluster_evaluations = Table('cluster_evaluations', metadata,
    Column('code', String(64), primary_key=True),
    Column('current_version', Integer, nullable=False),
    Column('current_threshold', Float, nullable=False),
    Column('pending_version', Integer, nullable=False),
    Column('pending_threshold', Float, nullable=False),
    Column('selection', JSON, nullable=False),
    Column('fingerprint', String(64), nullable=False),
    Column('passed', Boolean, nullable=False),
    Column('detail', JSON, nullable=False),
    Column('created_by', String(100), nullable=False),
    Column('created_at', DateTime, nullable=False),
)
