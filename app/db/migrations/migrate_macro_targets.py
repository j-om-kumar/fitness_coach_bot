"""
Database migration script to add macro target fields to users table.

Run this script to update your existing database schema.
"""
import asyncio
from sqlalchemy import text
from db import engine


async def migrate():
    """Add macro target columns to users table."""
    async with engine.begin() as conn:
        # Add protein target column
        await conn.execute(text(
            """
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS daily_protein_target INTEGER
            """
        ))
        
        # Add carbs target column
        await conn.execute(text(
            """
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS daily_carbs_target INTEGER
            """
        ))
        
        # Add fats target column
        await conn.execute(text(
            """
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS daily_fats_target INTEGER
            """
        ))
        
        # Add fiber target column
        await conn.execute(text(
            """
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS daily_fiber_target INTEGER
            """
        ))
        
        print("✅ Migration completed successfully!")
        print("Added columns: daily_protein_target, daily_carbs_target, daily_fats_target, daily_fiber_target to users table")


if __name__ == "__main__":
    asyncio.run(migrate())
