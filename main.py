"""
WhatsApp Coach - Main Application Entry Point

A Telegram bot that helps users track their nutrition and fitness goals.
"""
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import TELEGRAM_TOKEN, DEFAULT_TZ
from app.utils.handlers import handle_photo, handle_text
from app.utils.registration_handler import registration_handler
from app.utils.recipe_handler import end_recipe_mode
from app.utils.now_report_handler import handle_now_report
from app.utils.scheduler_tasks import (
    send_daily_reminders,
    send_lunch_reminder,
    send_evening_steps_reminder,
    send_daily_reports
)

# Initialize FastAPI app
app = FastAPI(title="WhatsApp Coach")

# Initialize Telegram bot
tg_app = Application.builder().token(TELEGRAM_TOKEN).build()

# Initialize scheduler
scheduler = AsyncIOScheduler()


def setup_handlers() -> None:
    """Register all Telegram message handlers."""
    # Registration conversation handler (must be added first)
    tg_app.add_handler(registration_handler)
    
    # Command handlers
    tg_app.add_handler(CommandHandler("nowreport", handle_now_report))
    tg_app.add_handler(CommandHandler("end_recipe", end_recipe_mode))
    
    # Other handlers
    tg_app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))


# Async wrapper functions for scheduler
async def morning_reminder_job():
    """Wrapper for morning reminder."""
    await send_daily_reminders(tg_app)


async def lunch_reminder_job():
    """Wrapper for lunch reminder."""
    await send_lunch_reminder(tg_app)


async def evening_reminder_job():
    """Wrapper for evening reminder."""
    await send_evening_steps_reminder(tg_app)


async def daily_report_job():
    """Wrapper for daily report."""
    await send_daily_reports(tg_app)


def setup_scheduler() -> None:
    """Configure scheduled reminder jobs."""
    tz = ZoneInfo(DEFAULT_TZ)
    
    # Morning reminder at 9:05 AM
    scheduler.add_job(
        morning_reminder_job,
        "cron",
        hour=9,
        minute=5,
        timezone=tz
    )
    
    # Lunch reminder at 1:00 PM
    scheduler.add_job(
        lunch_reminder_job,
        "cron",
        hour=13,
        minute=0,
        timezone=tz
    )
    
    # Evening reminder at 9:30 PM
    scheduler.add_job(
        evening_reminder_job,
        "cron",
        hour=21,
        minute=30,
        timezone=tz
    )
    
    # Daily report at 9:13 PM (for testing, change to 11:45 PM later)
    scheduler.add_job(
        daily_report_job,
        "cron",
        hour=23,
        minute=45,
        timezone=tz
    )
    

    scheduler.start()



@app.on_event("startup")
async def on_startup() -> None:
    """Initialize application on startup."""
    await tg_app.initialize()
    await tg_app.start()
    
    setup_handlers()
    setup_scheduler()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """Cleanup on application shutdown."""
    scheduler.shutdown(wait=False)
    await tg_app.stop()
    await tg_app.shutdown()


@app.post("/webhook")
async def telegram_webhook(request: Request) -> dict:
    """
    Handle incoming Telegram webhook updates.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Success response
    """
    data = await request.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"ok": True}


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
