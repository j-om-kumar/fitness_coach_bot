"""
Database migration script to add photo tracking fields to daily_logs table.

Run this script to update your existing database schema.
"""
import asyncio
from sqlalchemy import text
from db import engine


async def migrate():
    """Add photo tracking columns to daily_logs table."""
    async with engine.begin() as conn:
        # Add body_photo_file_id column
        await conn.execute(text(
            """
            ALTER TABLE daily_logs 
            ADD COLUMN IF NOT EXISTS body_photo_file_id TEXT
            """
        ))
        
        # Add weight_scale_photo_file_id column
        await conn.execute(text(
            """
            ALTER TABLE daily_logs 
            ADD COLUMN IF NOT EXISTS weight_scale_photo_file_id TEXT
            """
        ))
        
        print("✅ Migration completed successfully!")
        print("Added columns: body_photo_file_id, weight_scale_photo_file_id to daily_logs table")

