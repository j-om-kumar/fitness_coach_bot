"""
Database migration script to add target_weight_kg field to users table.

Run this script to update your existing database schema.
"""
import asyncio
from sqlalchemy import text
from db import engine


async def migrate():
    """Add target_weight_kg column to users table."""
    async with engine.begin() as conn:
        # Add target_weight_kg column
        await conn.execute(text(
            """
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS target_weight_kg NUMERIC(5, 2)
            """
        ))
        
        print("✅ Migration completed successfully!")
        print("Added column: target_weight_kg to users table")


# if __name__ == "__main__":
#     asyncio.run(migrate())
