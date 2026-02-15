"""
Database migration script to add activity_level and daily_calorie_target fields to users table.

Run this script to update your existing database schema.
"""
import asyncio
from sqlalchemy import text
from db import engine


async def migrate():
    """Add activity and calorie tracking columns to users table."""
    async with engine.begin() as conn:
        # Add activity_level column
        await conn.execute(text(
            """
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS activity_level VARCHAR(32)
            """
        ))
        
        # Add daily_calorie_target column
        await conn.execute(text(
            """
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS daily_calorie_target INTEGER
            """
        ))
        
        print("✅ Migration completed successfully!")
        print("Added columns: activity_level, daily_calorie_target to users table")


if __name__ == "__main__":
    asyncio.run(migrate())
