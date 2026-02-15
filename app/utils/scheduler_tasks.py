"""Scheduled reminder tasks."""
from datetime import date
from telegram.ext import Application
from telegram import InputFile

from app.db.db_service import get_all_users
from app.services.report_generator import generate_daily_report


async def send_daily_reminders(bot_app: Application) -> None:
    """
    Send morning reminders to all users.
    
    Args:
        bot_app: Telegram application instance
    """
    users = await get_all_users()
    
    for user in users:
        try:
            await bot_app.bot.send_message(
                chat_id=user.chat_id,
                text=(
                    "🌅 Morning check-in:\n"
                    "1) Send BREAKFAST photo\n"
                    "2) Send your WEIGHT (e.g., 'weight 98.6')"
                )
            )
        except Exception as e:
            # Ignore failures (user blocked bot, etc.)
            print(f"Failed to send morning reminder to user {user.id}: {e}")


async def send_lunch_reminder(bot_app: Application) -> None:
    """
    Send lunch reminders to all users.
    
    Args:
        bot_app: Telegram application instance
    """
    users = await get_all_users()
    
    for user in users:
        try:
            await bot_app.bot.send_message(
                chat_id=user.chat_id,
                text=(
                    "🍽️ Lunch time!\n"
                    "Don't forget to send a photo of your lunch.\n"
                    "I'll track the calories and nutrients for you! 😊"
                )
            )
        except Exception as e:
            print(f"Failed to send lunch reminder to user {user.id}: {e}")


async def send_evening_steps_reminder(bot_app: Application) -> None:
    """
    Send evening reminders to all users.
    
    Args:
        bot_app: Telegram application instance
    """
    users = await get_all_users()
    
    for user in users:
        try:
            await bot_app.bot.send_message(
                chat_id=user.chat_id,
                text=(
                    "🌙 Night check-in: Send your STEPS today (e.g., 'steps 8200'). "
                    "If you ate dinner, send the photo too."
                )
            )
        except Exception as e:
            # Ignore failures (user blocked bot, etc.)
            print(f"Failed to send evening reminder to user {user.id}: {e}")


async def send_daily_reports(bot_app: Application) -> None:
    """
    Send daily nutrition report with image to all users at 11:45 PM.
    
    Args:
        bot_app: Telegram application instance
    """
    users = await get_all_users()
    today = date.today()
    
    for user in users:
        try:
            # Generate report image
            report_image = await generate_daily_report(user.telegram_user_id, today)
            
            if report_image:
                # Send the report image
                await bot_app.bot.send_photo(
                    chat_id=user.chat_id,
                    photo=InputFile(report_image, filename=f"daily_report_{today}.png"),
                    caption=(
                        f"📊 **Your Daily Nutrition Report**\n\n"
                        f"Here's your complete summary for {today.strftime('%B %d, %Y')}.\n"
                        f"Keep up the great work! 💪"
                    ),
                    parse_mode="Markdown"
                )
            else:
                # Fallback text message if report generation fails
                await bot_app.bot.send_message(
                    chat_id=user.chat_id,
                    text=(
                        "📊 Daily Report\n\n"
                        "No nutrition data logged today. "
                        "Start tracking tomorrow to see your progress! 💪"
                    )
                )
        except Exception as e:
            print(f"Failed to send daily report to user {user.id}: {e}")

