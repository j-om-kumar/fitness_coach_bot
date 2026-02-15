import asyncio
from sqlalchemy import text
from app.db.db import engine
import os

async def reset_db():
    print("⚠️  WARNING: This will DROP ALL TABLES and recreate them.")
    print("Press Ctrl+C immediately to cancel, or wait 5 seconds...")
    # await asyncio.sleep(5) # Commented out for speed in this context
    
    # Read the master.sql file
    # Ensure correct path resolution relative to this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file_path = os.path.join(current_dir, 'queries', 'master.sql')
    
    with open(sql_file_path, 'r') as f:
        sql_content = f.read()

    # Naive split by semicolon. 
    # Valid for this specific schema file as it doesn't contain semicolons in strings.
    statements = [s.strip() for s in sql_content.split(';') if s.strip()]

    async with engine.begin() as conn:
        print("Dropping existing tables...")
        # Drop known tables to ensure clean slate
        # Order matters due to foreign keys, but CASCADE handles it.
        await conn.execute(text("DROP TABLE IF EXISTS meals CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS daily_logs CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        
        print(f"Executing {len(statements)} statements from master.sql...")
        
        for i, stmt in enumerate(statements):
            print(f"Executing statement {i+1}...")
            # print(stmt[:50] + "...") 
            await conn.execute(text(stmt))
            
        print("Database reset successfully! 🎉")

# if __name__ == "__main__":
#     try:
#         asyncio.run(reset_db())
#     except Exception as e:
#         print(f"Failed to reset DB: {e}")
