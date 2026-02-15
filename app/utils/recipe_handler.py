"""Handler for recipe suggestion requests with conversation management."""
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from app.db.db_service import get_user_by_telegram_id, get_daily_summary
from app.services.recipe_service import get_recipe_suggestion, format_macro_summary
from app.utils.conversation_context import ConversationContext


# Recipe conversation timeout (5 minutes)
RECIPE_CONVERSATION_TIMEOUT = 300  # seconds


async def handle_recipe_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle recipe suggestion requests with conversational AI."""
    user = update.effective_user
    user_message = update.message.text
    
    # Get user from database
    db_user = await get_user_by_telegram_id(user.id)
    
    if not db_user:
        await update.message.reply_text(
            "Please complete registration first by sending /start"
        )
        return
    
    # Check if user has targets set
    if not db_user.daily_calorie_target:
        await update.message.reply_text(
            "I need your nutrition targets to suggest recipes. "
            "Please complete registration with /start"
        )
        return
    
    # Get today's consumption
    today = datetime.now().date()
    daily_summary = await get_daily_summary(db_user, today)
    
    consumed_calories = daily_summary.get('total_calories', 0)
    consumed_protein = daily_summary.get('total_protein', 0)
    consumed_carbs = daily_summary.get('total_carbs', 0)
    consumed_fats = daily_summary.get('total_fats', 0)
    consumed_fiber = daily_summary.get('total_fiber', 0)
    
    # Calculate remaining macros
    remaining_calories = db_user.daily_calorie_target - consumed_calories
    remaining_protein = db_user.daily_protein_target - consumed_protein
    remaining_carbs = db_user.daily_carbs_target - consumed_carbs
    remaining_fats = db_user.daily_fats_target - consumed_fats
    remaining_fiber = db_user.daily_fiber_target - consumed_fiber
    
    # Get or create conversation context
    recipe_context = ConversationContext.get_context(user.id, 'recipe_chat')
    
    # Check if conversation has expired (5 minutes)
    if recipe_context and recipe_context.is_expired(timeout_seconds=RECIPE_CONVERSATION_TIMEOUT):
        ConversationContext.clear_context(user.id, 'recipe_chat')
        recipe_context = None
    
    # Build conversation history
    conversation_history = []
    if recipe_context and recipe_context.data.get('messages'):
        conversation_history = recipe_context.data['messages']
    
    # If this is a new conversation, show macro summary first
    if not recipe_context:
        macro_summary = format_macro_summary(
            consumed_calories, db_user.daily_calorie_target,
            consumed_protein, db_user.daily_protein_target,
            consumed_carbs, db_user.daily_carbs_target,
            consumed_fats, db_user.daily_fats_target
        )
        await update.message.reply_text(
            "🍳 **RECIPE MODE ACTIVATED** 🍳\n\n"
            + macro_summary + 
            "\n💬 What would you like to cook? I can suggest recipes!\n\n"
            "💡 Tip: Type `/end_recipe` anytime to exit recipe mode",
            parse_mode="Markdown"
        )
        
        # Save context to indicate conversation started
        ConversationContext.save_context(
            user.id,
            'recipe_chat',
            {'messages': [], 'started_at': datetime.now().isoformat()}
        )
        return
    
    # Get AI recipe suggestion
    await update.message.reply_text("🤔 Let me think of something perfect for you...")
    
    suggestion = await get_recipe_suggestion(
        user_message=user_message,
        remaining_calories=remaining_calories,
        remaining_protein=remaining_protein,
        remaining_carbs=remaining_carbs,
        remaining_fats=remaining_fats,
        remaining_fiber=remaining_fiber,
        goal=db_user.goal,
        conversation_history=conversation_history
    )
    
    if suggestion:
        # Send the suggestion
        await update.message.reply_text(suggestion, parse_mode="Markdown")
        
        # Update conversation history
        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": suggestion})
        
        # Keep only last 6 messages (3 exchanges) to avoid token limits
        if len(conversation_history) > 6:
            conversation_history = conversation_history[-6:]
        
        # Save updated context
        ConversationContext.save_context(
            user.id,
            'recipe_chat',
            {
                'messages': conversation_history,
                'started_at': recipe_context.data.get('started_at', datetime.now().isoformat())
            }
        )
        
        # Inform about conversation timeout
        time_remaining = RECIPE_CONVERSATION_TIMEOUT - (datetime.now() - recipe_context.created_at).total_seconds()
        if time_remaining > 0:
            minutes_remaining = int(time_remaining / 60)
            await update.message.reply_text(
                f"🍳 *Recipe Mode Active*\n\n"
                f"💡 Ask follow-up questions or request variations!\n"
                f"⏱️ Time remaining: {minutes_remaining} minutes\n"
                f"🚪 Type `/end_recipe` to exit",
                parse_mode="Markdown"
            )
    else:
        await update.message.reply_text(
            "Sorry, I couldn't generate a recipe suggestion right now. "
            "Please try again in a moment."
        )


async def is_recipe_request(message_text: str) -> bool:
    """
    Check if a message is a recipe request.
    
    Args:
        message_text: The message text to check
        
    Returns:
        True if it's a recipe request, False otherwise
    """
    recipe_keywords = [
        'recipe', 'recipes', 'cook', 'cooking', 
        'make', 'prepare', 'suggest', 'recommendation',
        'what should i', 'what can i', 'ideas for', 'hungry', 'craving'
    ]
    
    message_lower = message_text.lower()
    
    # Check for recipe keywords
    for keyword in recipe_keywords:
        if keyword in message_lower:
            return True
    
    # Check for question patterns about food
    food_questions = ['what to', 'what should', 'what can', 'how to make', 'how do i cook']
    for pattern in food_questions:
        if pattern in message_lower:
            return True
    
    return False


async def end_recipe_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /end_recipe command to exit recipe mode.
    
    Args:
        update: Telegram update
        context: Telegram context
    """
    user = update.effective_user
    
    # Check if user has an active recipe conversation
    recipe_context = ConversationContext.get_context(user.id, 'recipe_chat')
    
    if recipe_context:
        # Clear the recipe context
        ConversationContext.clear_context(user.id, 'recipe_chat')
        
        await update.message.reply_text(
            "✅ *Recipe Mode Ended*\n\n"
            "You've exited recipe mode. You can:\n"
            "• Send meal photos to track nutrition\n"
            "• Log weight or steps\n"
            "• Ask for recipes anytime to start a new session\n\n"
            "How can I help you? 😊",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "You're not currently in recipe mode.\n\n"
            "Ask for recipe suggestions to start a recipe conversation!",
            parse_mode="Markdown"
        )
