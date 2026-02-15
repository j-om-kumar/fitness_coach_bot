"""Telegram message handlers."""
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes

from app.utils.parsers import parse_weight, parse_steps
from app.services.ai_service import analyze_meal_photo
from app.db.db_service import (
    get_user_by_telegram_id,
    save_weight,
    save_steps,
    save_meal,
    is_user_registered
)
from app.services.image_classifier import classify_image
from app.db.db_service import save_weight_scale_photo
from app.db.db_service import save_body_photo


async def check_registration(update: Update) -> bool:
    """Check if user is registered, prompt if not."""
    user = update.effective_user
    
    if not await is_user_registered(user.id):
        await update.message.reply_text(
            "⚠️ Please complete registration first!\n\n"
            "Send /start to get started."
        )
        return False
    
    return True



async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle photo messages with intelligent classification."""
    # Check if user is registered
    if not await check_registration(update):
        return
    
    user = update.effective_user
    
    # Validate photo
    photos = update.message.photo
    if not photos:
        await update.message.reply_text("Send a clear photo 🙂")
        return

    # Get highest resolution photo
    best_photo = photos[-1]
    file = await context.bot.get_file(best_photo.file_id)
    file_bytes = await file.download_as_bytearray()
    
    # Get caption if provided
    user_caption = update.message.caption if update.message.caption else None
    
    # First, classify the image type
    
    classification = await classify_image(bytes(file_bytes))
    
    if not classification:
        await update.message.reply_text(
            "I couldn't analyze that image. Please try again with a clearer photo."
        )
        return
    
    # Get user from database
    db_user = await get_user_by_telegram_id(user.id)
    
    # Handle based on image type
    if classification.image_type == "food":
        await handle_food_photo(update, db_user, best_photo.file_id, bytes(file_bytes), classification, user_caption)
    
    elif classification.image_type == "weight_scale":
        await handle_weight_scale_photo(update, db_user, best_photo.file_id, classification)
    
    elif classification.image_type == "body_photo":
        await handle_body_photo(update, db_user, best_photo.file_id, classification)
    
    elif classification.image_type == "steps_count":
        await handle_steps_photo(update, db_user, classification)
    
    else:  # "other"
        await update.message.reply_text(
            f"📷 I see: {classification.description}\n\n"
            "This doesn't seem to be a trackable item (food, weight scale, body photo, or steps count).\n\n"
            "Please send:\n"
            "• 🍽️ Food photos for meal tracking\n"
            "• ⚖️ Weight scale photos\n"
            "• 💪 Body progress photos\n"
            "• 👟 Steps count screenshots"
        )



async def handle_food_photo(update: Update, user, photo_file_id: str, file_bytes: bytes, classification, user_caption: Optional[str] = None) -> None:
    """Handle food photo with nutritional analysis."""
    # Analyze nutrition with user's notes if provided
    analysis = await analyze_meal_photo(file_bytes, user_caption)
    
    if not analysis:
        await update.message.reply_text(
            "I couldn't analyze the nutritional content. "
            "Try a clearer photo or add a description."
        )
        return
    
    # Save meal to database
    await save_meal(
        user=user,
        meal_type=analysis.meal_type,
        description=analysis.description,
        calories_kcal=analysis.calories_kcal,
        protein_g=analysis.protein_g,
        carbs_g=analysis.carbs_g,
        fats_g=analysis.fats_g,
        fiber_g=analysis.fiber_g,
        photo_file_id=photo_file_id
    )
    
    # Build detailed response
    reply = f"🍽️ **{analysis.meal_type.replace('_', ' ').title()} Logged**\n\n"
    
    if analysis.description:
        reply += f"*{analysis.description}*\n\n"
    
    # Show user's notes if provided
    if user_caption:
        reply += f"� Your notes: _{user_caption}_\n\n"
    
    reply += "�📊 **Nutritional Information:**\n"
    reply += f"• Calories: {analysis.calories_kcal if analysis.calories_kcal else '—'} kcal\n"
    reply += f"• Protein: {analysis.protein_g if analysis.protein_g else '—'} g\n"
    reply += f"• Carbs: {analysis.carbs_g if analysis.carbs_g else '—'} g\n"
    reply += f"• Fats: {analysis.fats_g if analysis.fats_g else '—'} g\n"
    reply += f"• Fiber: {analysis.fiber_g if analysis.fiber_g else '—'} g\n\n"
    reply += f"🎯 Confidence: {analysis.confidence}\n\n"
    reply += "Keep tracking your meals! 💪"
    
    await update.message.reply_text(reply, parse_mode="Markdown")



async def handle_weight_scale_photo(update: Update, user, photo_file_id: str, classification) -> None:
    """Handle weight scale photo."""
    
    
    weight = classification.weight_kg
    
    # Save photo and weight if detected
    await save_weight_scale_photo(user, photo_file_id, weight)
    
    if weight:
        reply = f"⚖️ **Weight Logged**\n\n"
        reply += f"Weight: {weight} kg\n\n"
        reply += "Great job tracking your progress! 📈"
    else:
        reply = f"⚖️ **Weight Scale Photo Saved**\n\n"
        reply += "I couldn't read the exact weight from the scale.\n"
        reply += "You can also send it as text: 'weight 75.5'"
    
    await update.message.reply_text(reply, parse_mode="Markdown")


async def handle_body_photo(update: Update, user, photo_file_id: str, classification) -> None:
    """Handle body progress photo."""
    
    
    await save_body_photo(user, photo_file_id)
    
    reply = f"💪 **Progress Photo Saved**\n\n"
    reply += f"{classification.description}\n\n"
    reply += "Keep up the amazing work! Your transformation is being tracked. 🔥"
    
    await update.message.reply_text(reply, parse_mode="Markdown")


async def handle_steps_photo(update: Update, user, classification) -> None:
    """Handle steps count screenshot."""
    steps = classification.steps
    
    if steps:
        await save_steps(user, steps)
        target = 8000 if steps < 8000 else 10000
        reply = f"👟 **Steps Logged**\n\n"
        reply += f"Steps: {steps:,}\n"
        reply += f"Tomorrow's target: {target:,}\n\n"
        reply += "Keep moving! 🚶‍♂️"
    else:
        reply = f"👟 **Steps Screenshot Detected**\n\n"
        reply += "I couldn't read the exact step count.\n"
        reply += "You can also send it as text: 'steps 8200'"
    
    await update.message.reply_text(reply, parse_mode="Markdown")




async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages (weight, steps, meal descriptions, etc.)."""
    # Check if user is registered
    if not await check_registration(update):
        return
    
    user = update.effective_user
    text = (update.message.text or "").strip()

    
    # Try parsing weight first
    weight = parse_weight(text)
    if weight is not None:
        db_user = await get_user_by_telegram_id(user.id)
        await save_weight(db_user, weight)
        await update.message.reply_text(
            f"✅ Weight saved: {weight} kg.\n"
            "Keep tracking your progress! 📈"
        )
        return
    
    # Try parsing steps
    steps = parse_steps(text)
    if steps is not None:
        db_user = await get_user_by_telegram_id(user.id)
        await save_steps(db_user, steps)
        
        # Simple coaching based on steps
        target = 8000 if steps < 8000 else 10000
        await update.message.reply_text(
            f"✅ Steps saved: {steps:,}.\n"
            f"Tomorrow target: {target:,}.\n"
            "Keep moving! 🚶‍♂️"
        )
        return
    
    # Check if user is responding to a pending meal request
    from app.utils.conversation_context import get_context
    
    ctx = get_context(user.id)
    pending_meal = ctx.get("pending_meal_description")
    
    if pending_meal:
        # User is providing additional details for a previous meal
        combined_text = f"{pending_meal}, {text}"
        ctx.clear()  # Clear the pending request
        
        # Re-analyze with combined information
        from app.services.text_meal_analyzer import analyze_text_meal
        meal_analysis = await analyze_text_meal(combined_text)
        
        if meal_analysis and meal_analysis.is_trackable:
            await handle_text_meal(update, user, combined_text, meal_analysis)
            return
    
    # Try analyzing as a new meal description
    from app.services.text_meal_analyzer import analyze_text_meal
    
    meal_analysis = await analyze_text_meal(text)
    
    if meal_analysis and meal_analysis.is_trackable:
        await handle_text_meal(update, user, text, meal_analysis)
        return
    
    # Check if this is a recipe request or part of recipe conversation
    from app.utils.recipe_handler import is_recipe_request, handle_recipe_request
    from app.utils.conversation_context import ConversationContext
    
    # Check for active recipe conversation
    recipe_context = ConversationContext.get_context(user.id, 'recipe_chat')
    
    if recipe_context and not recipe_context.is_expired(timeout_seconds=300):
        # User is in an active recipe conversation
        await handle_recipe_request(update, context)
        return
    
    # Check if this is a new recipe request
    if await is_recipe_request(text):
        await handle_recipe_request(update, context)
        return
    
    # Fallback message for non-trackable text
    await update.message.reply_text(
        "I can help you with:\n\n"
        "📸 **Photos:**\n"
        "• Food/meals\n"
        "• Weight scale\n"
        "• Body progress photos\n"
        "• Steps screenshots\n\n"
        "✍️ **Text:**\n"
        "• Meal descriptions (e.g., '2 eggs and toast')\n"
        "• Weight: 'weight 75.5'\n"
        "• Steps: 'steps 8200'\n\n"
        "🍳 **Recipe Suggestions:**\n"
        "• Ask for meal ideas based on your remaining macros\n"
        "• Get personalized recipes for your goals\n\n"
        "What would you like to do?"
    )



async def handle_text_meal(update: Update, user, original_text: str, analysis) -> None:
    """Handle text-based meal description."""
    # Check if we need more information
    if analysis.confidence == "low" and analysis.missing_info:
        # Save the original description in context for follow-up
        from app.utils.conversation_context import get_context
        ctx = get_context(user.id)
        ctx.set("pending_meal_description", original_text)
        
        await update.message.reply_text(
            f"📝 I can track this, but I need more details:\n\n"
            f"💡 {analysis.missing_info}\n\n"
            f"Example: '{original_text}, about 200g' or '{original_text}, large portion'"
        )

        return
    
    # Get user from database
    db_user = await get_user_by_telegram_id(user.id)
    
    # Save meal to database
    await save_meal(
        user=db_user,
        meal_type=analysis.meal_type,
        description=analysis.description or original_text,
        calories_kcal=analysis.calories_kcal,
        protein_g=analysis.protein_g,
        carbs_g=analysis.carbs_g,
        fats_g=analysis.fats_g,
        fiber_g=analysis.fiber_g,
        photo_file_id=None  # No photo for text-based meals
    )
    
    # Build response
    reply = f"✅ **{analysis.meal_type.replace('_', ' ').title()} Logged**\n\n"
    
    if analysis.description:
        reply += f"📝 {analysis.description}\n\n"
    
    reply += "📊 **Nutritional Estimate:**\n"
    reply += f"• Calories: {analysis.calories_kcal if analysis.calories_kcal else '—'} kcal\n"
    reply += f"• Protein: {analysis.protein_g if analysis.protein_g else '—'} g\n"
    reply += f"• Carbs: {analysis.carbs_g if analysis.carbs_g else '—'} g\n"
    reply += f"• Fats: {analysis.fats_g if analysis.fats_g else '—'} g\n"
    reply += f"• Fiber: {analysis.fiber_g if analysis.fiber_g else '—'} g\n\n"
    
    if analysis.confidence == "low":
        reply += "⚠️ Confidence: Low - Consider adding a photo for better accuracy\n\n"
    else:
        reply += f"🎯 Confidence: {analysis.confidence}\n\n"
    
    reply += "💡 Tip: Send a photo next time for more accurate tracking!"
    
    await update.message.reply_text(reply, parse_mode="Markdown")

