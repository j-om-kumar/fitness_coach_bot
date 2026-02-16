"""Handlers for context-aware actions (modify, delete, query meals)."""
from typing import Optional, Dict, Any
from telegram import Update
from telegram.ext import ContextTypes

from app.db.db_service import (
    get_meal_by_id,
    update_meal,
    delete_meal,
    get_user_by_telegram_id
)
from app.services.intent_classifier import extract_portion_multiplier
from app.services.ai_service import analyze_meal_photo
from app.utils.conversation_context import ConversationContext


async def handle_meal_deletion(
    update: Update,
    context_data: Dict[str, Any]
) -> None:
    """
    Handle meal deletion request.
    
    Args:
        update: Telegram update
        context_data: Context data containing meal_id
    """
    meal_id = context_data.get('last_meal_id')
    
    if not meal_id:
        await update.message.reply_text(
            "❌ I couldn't find the meal to delete. It may have been too long ago."
        )
        return
    
    # Get meal details before deleting
    meal = await get_meal_by_id(meal_id)
    
    if not meal:
        await update.message.reply_text(
            "❌ That meal no longer exists in the database."
        )
        return
    
    # Delete the meal
    success = await delete_meal(meal_id)
    
    if success:
        await update.message.reply_text(
            f"✅ **Meal Deleted**\n\n"
            f"Removed: {meal.description or 'Meal'}\n"
            f"Calories: {meal.calories_kcal or 0} kcal\n\n"
            f"Your daily totals have been updated.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "❌ Failed to delete the meal. Please try again."
        )


async def handle_portion_adjustment(
    update: Update,
    context_data: Dict[str, Any],
    portion_size: str
) -> None:
    """
    Handle portion size adjustment.
    
    Args:
        update: Telegram update
        context_data: Context data containing meal_id and analysis
        portion_size: 'small', 'medium', or 'large'
    """
    meal_id = context_data.get('last_meal_id')
    last_analysis = context_data.get('last_meal_analysis')
    
    if not meal_id or not last_analysis:
        await update.message.reply_text(
            "❌ I couldn't find the meal to update."
        )
        return
    
    # Get multiplier
    multiplier = extract_portion_multiplier(portion_size)
    
    # Calculate new values
    new_calories = int((last_analysis.get('calories_kcal', 0) or 0) * multiplier)
    new_protein = int((last_analysis.get('protein_g', 0) or 0) * multiplier)
    new_carbs = int((last_analysis.get('carbs_g', 0) or 0) * multiplier)
    new_fats = int((last_analysis.get('fats_g', 0) or 0) * multiplier)
    new_fiber = int((last_analysis.get('fiber_g', 0) or 0) * multiplier)
    
    # Update description to include portion size
    original_desc = last_analysis.get('description', '')
    new_description = f"{original_desc} ({portion_size.capitalize()} portion)"
    
    # Update meal
    updated_meal = await update_meal(
        meal_id=meal_id,
        description=new_description,
        calories_kcal=new_calories,
        protein_g=new_protein,
        carbs_g=new_carbs,
        fats_g=new_fats,
        fiber_g=new_fiber
    )
    
    if updated_meal:
        await update.message.reply_text(
            f"✅ **Portion Size Updated to {portion_size.capitalize()}!**\n\n"
            f"📝 {new_description}\n\n"
            f"📊 **Updated Nutrition:**\n"
            f"• Calories: {new_calories} kcal\n"
            f"• Protein: {new_protein}g\n"
            f"• Carbs: {new_carbs}g\n"
            f"• Fats: {new_fats}g\n"
            f"• Fiber: {new_fiber}g\n\n"
            f"Your daily totals have been updated! 💪",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "❌ Failed to update the meal. Please try again."
        )


async def handle_meal_type_change(
    update: Update,
    context_data: Dict[str, Any],
    new_meal_type: str
) -> None:
    """
    Handle meal type change (breakfast -> lunch, etc).
    
    Args:
        update: Telegram update
        context_data: Context data containing meal_id
        new_meal_type: New meal type
    """
    meal_id = context_data.get('last_meal_id')
    
    if not meal_id:
        await update.message.reply_text(
            "❌ I couldn't find the meal to update."
        )
        return
    
    # Update meal type
    updated_meal = await update_meal(
        meal_id=meal_id,
        meal_type=new_meal_type
    )
    
    if updated_meal:
        await update.message.reply_text(
            f"✅ **Meal Type Updated!**\n\n"
            f"Changed to: **{new_meal_type.capitalize()}**\n"
            f"📝 {updated_meal.description or 'Meal'}\n\n"
            f"Your meal log has been updated.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "❌ Failed to update the meal type. Please try again."
        )


async def handle_add_to_meal(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    context_data: Dict[str, Any],
    food_item: str
) -> None:
    """
    Handle adding food to existing meal.
    
    Args:
        update: Telegram update
        context: Telegram context
        context_data: Context data containing meal info
        food_item: Food item to add
    """
    meal_id = context_data.get('last_meal_id')
    last_photo_bytes = context_data.get('last_photo_bytes')
    last_analysis = context_data.get('last_meal_analysis')
    
    if not meal_id:
        await update.message.reply_text(
            "❌ I couldn't find the meal to update."
        )
        return
    
    # Get current meal
    meal = await get_meal_by_id(meal_id)
    if not meal:
        await update.message.reply_text(
            "❌ That meal no longer exists."
        )
        return
    
    # Create updated description
    original_desc = meal.description or "Meal"
    new_description = f"{original_desc} + {food_item}"
    
    # If we have the photo, re-analyze with the addition
    if last_photo_bytes:
        await update.message.reply_text("🔄 Re-analyzing with the addition...")
        
        # Re-analyze with updated description
        new_analysis = await analyze_meal_photo(last_photo_bytes, new_description)
        
        if new_analysis:
            # Update meal with new analysis
            updated_meal = await update_meal(
                meal_id=meal_id,
                description=new_analysis.description or new_description,
                calories_kcal=new_analysis.calories_kcal,
                protein_g=new_analysis.protein_g,
                carbs_g=new_analysis.carbs_g,
                fats_g=new_analysis.fats_g,
                fiber_g=new_analysis.fiber_g
            )
            
            if updated_meal:
                await update.message.reply_text(
                    f"✅ **Meal Updated!**\n\n"
                    f"📝 {new_analysis.description}\n\n"
                    f"📊 **Updated Nutrition:**\n"
                    f"• Calories: {new_analysis.calories_kcal} kcal\n"
                    f"• Protein: {new_analysis.protein_g}g\n"
                    f"• Carbs: {new_analysis.carbs_g}g\n"
                    f"• Fats: {new_analysis.fats_g}g\n"
                    f"• Fiber: {new_analysis.fiber_g}g\n\n"
                    f"Your daily totals have been updated! 💪",
                    parse_mode="Markdown"
                )
                
                # Update context with new analysis
                user = update.effective_user
                ConversationContext.save_context(
                    user.id,
                    'meal_context',
                    {
                        'last_meal_id': meal_id,
                        'last_photo_bytes': last_photo_bytes,
                        'last_meal_analysis': {
                            'description': new_analysis.description,
                            'calories_kcal': new_analysis.calories_kcal,
                            'protein_g': new_analysis.protein_g,
                            'carbs_g': new_analysis.carbs_g,
                            'fats_g': new_analysis.fats_g,
                            'fiber_g': new_analysis.fiber_g
                        }
                    }
                )
            else:
                await update.message.reply_text(
                    "❌ Failed to update the meal. Please try again."
                )
        else:
            await update.message.reply_text(
                "❌ Failed to re-analyze the meal. Please try uploading a new photo."
            )
    else:
        # No photo available, just update description
        updated_meal = await update_meal(
            meal_id=meal_id,
            description=new_description
        )
        
        if updated_meal:
            await update.message.reply_text(
                f"✅ **Meal Updated!**\n\n"
                f"📝 {new_description}\n\n"
                f"Note: I couldn't recalculate nutrition without the original photo.\n"
                f"The nutritional values remain the same.",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "❌ Failed to update the meal. Please try again."
            )


async def handle_meal_query(
    update: Update,
    context_data: Dict[str, Any],
    nutrient: Optional[str] = None
) -> None:
    """
    Handle query about previous meal.
    
    Args:
        update: Telegram update
        context_data: Context data containing meal analysis
        nutrient: Specific nutrient being asked about (optional)
    """
    last_analysis = context_data.get('last_meal_analysis')
    
    if not last_analysis:
        await update.message.reply_text(
            "❌ I don't have information about your last meal."
        )
        return
    
    # Get user for targets
    user_tg = update.effective_user
    user = await get_user_by_telegram_id(user_tg.id)
    
    description = last_analysis.get('description', 'Your last meal')
    
    if nutrient:
        # Specific nutrient query
        value = last_analysis.get(f'{nutrient}_kcal' if nutrient == 'calories' else f'{nutrient}_g', 0)
        unit = 'kcal' if nutrient == 'calories' else 'g'
        
        # Get target if available
        target = None
        if user:
            target_map = {
                'calories': user.daily_calorie_target,
                'protein': user.daily_protein_target,
                'carbs': user.daily_carbs_target,
                'fats': user.daily_fats_target,
                'fiber': user.daily_fiber_target
            }
            target = target_map.get(nutrient)
        
        response = f"📊 **{nutrient.capitalize()} in {description}:**\n\n"
        response += f"• {value} {unit}\n"
        
        if target:
            percentage = int((value / target) * 100) if target > 0 else 0
            response += f"• That's {percentage}% of your daily target ({target} {unit})"
        
        await update.message.reply_text(response, parse_mode="Markdown")
    else:
        # General query - show all nutrition
        response = f"📊 **Nutrition for {description}:**\n\n"
        response += f"• Calories: {last_analysis.get('calories_kcal', 0)} kcal\n"
        response += f"• Protein: {last_analysis.get('protein_g', 0)}g\n"
        response += f"• Carbs: {last_analysis.get('carbs_g', 0)}g\n"
        response += f"• Fats: {last_analysis.get('fats_g', 0)}g\n"
        response += f"• Fiber: {last_analysis.get('fiber_g', 0)}g"
        
        await update.message.reply_text(response, parse_mode="Markdown")
