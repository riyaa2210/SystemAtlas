"""
One-time migration: adds graph_data JSONB column to analytics_snapshots.
Run once: python app/db/migrate_add_graph.py
"""
import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import text
from app.db.postgres import engine


async def migrate():
    async with engine.begin() as conn:
        # Add column if it doesn't exist
        await conn.execute(text("""
            ALTER TABLE analytics_snapshots
            ADD COLUMN IF NOT EXISTS graph_data JSONB
        """))
        print("Migration complete: graph_data column added to analytics_snapshots")


if __name__ == "__main__":
    asyncio.run(migrate())
