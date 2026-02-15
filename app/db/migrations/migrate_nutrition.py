"""
Database migration script to add nutritional fields to meals table.

Run this script to update your existing database schema.
"""
import asyncio
from sqlalchemy import text
from db import engine


async def migrate():
    """Add new nutritional columns to meals table."""
    async with engine.begin() as conn:
        # Add carbs_g column
        await conn.execute(text(
            """
            ALTER TABLE meals 
            ADD COLUMN IF NOT EXISTS carbs_g INTEGER
            """
        ))
        
        # Add fats_g column
        await conn.execute(text(
            """
            ALTER TABLE meals 
            ADD COLUMN IF NOT EXISTS fats_g INTEGER
            """
        ))
        
        # Add fiber_g column
        await conn.execute(text(
            """
            ALTER TABLE meals 
            ADD COLUMN IF NOT EXISTS fiber_g INTEGER
            """
        ))
        
        print("✅ Migration completed successfully!")
        print("Added columns: carbs_g, fats_g, fiber_g to meals table")


# if __name__ == "__main__":
#     print("🔄 Running database migration for nutritional fields...")
#     asyncio.run(migrate())
