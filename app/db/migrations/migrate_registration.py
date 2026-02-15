"""
Database migration script to add registration fields to users table.

Run this script to update your existing database schema.
"""
import asyncio
from sqlalchemy import text
from db import engine


async def migrate():
    """Add new columns to users table."""
    async with engine.begin() as conn:
        # Add registration_completed column
        await conn.execute(text(
            """
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS registration_completed INTEGER DEFAULT 0 NOT NULL
            """
        ))
        
        # Add height_cm column
        await conn.execute(text(
            """
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS height_cm NUMERIC(5, 2)
            """
        ))
        
        # Add initial_weight_kg column
        await conn.execute(text(
            """
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS initial_weight_kg NUMERIC(5, 2)
            """
        ))
        
        # Add goal column
        await conn.execute(text(
            """
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS goal VARCHAR(64)
            """
        ))
        
        print("✅ Migration completed successfully!")
        print("Added columns: registration_completed, height_cm, initial_weight_kg, goal")



