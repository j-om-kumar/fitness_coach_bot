"""Handler for /nowreport command."""
from telegram import Update
from telegram.ext import ContextTypes
from app.services.now_report_service import generate_now_report
from app.db.db_service import is_user_registered


async def handle_now_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /nowreport command to show today's nutrition progress.
    
    Args:
        update: Telegram update object
        context: Telegram context
    """
    user = update.effective_user
    
    # Check if user is registered
    if not await is_user_registered(user.id):
        await update.message.reply_text(
            "⚠️ Please complete registration first!\n\n"
            "Send /start to get started."
        )
        return
    
    # Send a "generating" message
    status_message = await update.message.reply_text("📊 Generating your report...")
    
    try:
        # Generate the report
        report = await generate_now_report(user.id)
        
        # Delete the status message
        await status_message.delete()
        
        # Send the report
        await update.message.reply_text(report, parse_mode="Markdown")
        
    except Exception as e:
        await status_message.edit_text(
            f"❌ Error generating report: {str(e)}\n\n"
            "Please try again later."
        )
