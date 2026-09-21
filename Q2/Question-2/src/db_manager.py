#!/usr/bin/env python3
"""
Question-2: Persistent Relational Database Manager
Manages SQLite connection, DDL schema, index lifecycle, and query planner profiling.
"""

import os
import sqlite3
from typing import List, Tuple, Dict, Any


class DatabaseManager:
    """
    Manages persistent SQLite storage for procurement notices and LSH bucket index.
    """
    def __init__(self, db_path: str = "Question-2/db/procurement_lsh.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA synchronous = OFF")
        self.conn.execute("PRAGMA journal_mode = MEMORY")

    def init_schema(self):
        """Initializes tables for notices, lsh_buckets, and candidate_pairs."""
        with self.conn:
            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS notices (
                notice_id TEXT PRIMARY KEY,
                portal_id TEXT NOT NULL,
                published_at TEXT,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                estimated_value INTEGER NOT NULL,
                closing_date TEXT
            )""")
            
            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS lsh_buckets (
                band_id INTEGER NOT NULL,
                bucket_hash TEXT NOT NULL,
                notice_id TEXT NOT NULL
            )""")
            
            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS candidate_pairs (
                notice_id_a TEXT NOT NULL,
                notice_id_b TEXT NOT NULL,
                band_collisions INTEGER NOT NULL,
                estimated_similarity REAL NOT NULL,
                is_merged BOOLEAN NOT NULL,
                PRIMARY KEY (notice_id_a, notice_id_b)
            )""")

    def create_covering_index(self):
        """Creates composite B-tree covering index on lsh_buckets(band_id, bucket_hash, notice_id)."""
        with self.conn:
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_lsh_covering ON lsh_buckets(band_id, bucket_hash, notice_id)"
            )

    def drop_index(self):
        """Drops index to force full table scan access path."""
        with self.conn:
            self.conn.execute("DROP INDEX IF EXISTS idx_lsh_covering")

    def get_query_plan(self, query: str, params: Tuple = ()) -> List[str]:
        """Returns SQLite EXPLAIN QUERY PLAN string lines."""
        cur = self.conn.execute(f"EXPLAIN QUERY PLAN {query}", params)
        return [row[3] for row in cur.fetchall()]

    def close(self):
        """Closes the database connection."""
        self.conn.close()
