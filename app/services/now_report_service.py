"""Generate real-time daily nutrition report with progress bars."""
from datetime import date
from typing import Dict, Any, List
from app.db.db_service import get_user_by_telegram_id, get_or_create_daily_log
from app.db.db import SessionLocal, User, Meal
from sqlalchemy import select


def create_progress_bar(current: int, target: int, length: int = 10) -> str:
    """
    Create a visual progress bar.
    
    Args:
        current: Current value
        target: Target value
        length: Length of the progress bar in characters
        
    Returns:
        String representation of progress bar
    """
    if target == 0:
        percentage = 0
    else:
        percentage = min(100, int((current / target) * 100))
    
    filled = int((percentage / 100) * length)
    empty = length - filled
    
    # Use different colors based on percentage
    if percentage < 50:
        bar_char = "🟥"  # Red for low
    elif percentage < 80:
        bar_char = "🟨"  # Yellow for medium
    elif percentage <= 100:
        bar_char = "🟩"  # Green for good
    else:
        bar_char = "🟦"  # Blue for over target
    
    empty_char = "⬜"
    
    bar = bar_char * filled + empty_char * empty
    return f"{bar} {percentage}%"


async def get_today_nutrition_data(user: User) -> Dict[str, Any]:
    """
    Get today's nutrition data for a user.
    
    Args:
        user: User instance
        
    Returns:
        Dictionary with meals and totals
    """
    today = date.today()
    
    async with SessionLocal() as session:
        # Get today's daily log
        daily_log = await get_or_create_daily_log(session, user.id, today)
        
        # Get all meals for today
        result = await session.execute(
            select(Meal).where(Meal.daily_log_id == daily_log.id).order_by(Meal.created_at)
        )
        meals = list(result.scalars().all())
        
        # Calculate totals
        totals = {
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fats': 0,
            'fiber': 0
        }
        
        meal_list = []
        
        for meal in meals:
            totals['calories'] += meal.calories_kcal or 0
            totals['protein'] += meal.protein_g or 0
            totals['carbs'] += meal.carbs_g or 0
            totals['fats'] += meal.fats_g or 0
            totals['fiber'] += meal.fiber_g or 0
            
            meal_list.append({
                'type': meal.meal_type,
                'description': meal.description or 'No description',
                'calories': meal.calories_kcal or 0,
                'protein': meal.protein_g or 0,
                'carbs': meal.carbs_g or 0,
                'fats': meal.fats_g or 0,
                'fiber': meal.fiber_g or 0,
                'time': meal.created_at.strftime('%I:%M %p')
            })
        
        return {
            'meals': meal_list,
            'totals': totals,
            'targets': {
                'calories': user.daily_calorie_target or 2000,
                'protein': user.daily_protein_target or 150,
                'carbs': user.daily_carbs_target or 200,
                'fats': user.daily_fats_target or 60,
                'fiber': user.daily_fiber_target or 30
            }
        }


def format_now_report(data: Dict[str, Any]) -> str:
    """
    Format the nutrition data into a beautiful text report.
    
    Args:
        data: Nutrition data dictionary
        
    Returns:
        Formatted report string
    """
    meals = data['meals']
    totals = data['totals']
    targets = data['targets']
    
    # Header
    report = "📊 **TODAY'S NUTRITION REPORT**\n"
    report += f"📅 {date.today().strftime('%A, %B %d, %Y')}\n"
    report += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Meals section
    if meals:
        report += "🍽️ **MEALS LOGGED:**\n\n"
        
        for i, meal in enumerate(meals, 1):
            meal_emoji = {
                'breakfast': '🌅',
                'lunch': '🌞',
                'dinner': '🌙',
                'snack': '🍪'
            }.get(meal['type'], '🍴')
            
            report += f"{meal_emoji} **{meal['type'].upper()}** ({meal['time']})\n"
            report += f"   📝 {meal['description']}\n"
            report += f"   🔥 {meal['calories']} kcal | "
            report += f"P: {meal['protein']}g | "
            report += f"C: {meal['carbs']}g | "
            report += f"F: {meal['fats']}g\n\n"
    else:
        report += "🍽️ **MEALS LOGGED:** None yet\n\n"
    
    report += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Totals and Progress
    report += "📈 **DAILY PROGRESS:**\n\n"
    
    # Calories
    cal_current = totals['calories']
    cal_target = targets['calories']
    cal_remaining = cal_target - cal_current
    
    report += f"🔥 **Calories:** {cal_current} / {cal_target} kcal\n"
    report += f"   {create_progress_bar(cal_current, cal_target)}\n"
    if cal_remaining > 0:
        report += f"   ✅ {cal_remaining} kcal remaining\n\n"
    elif cal_remaining == 0:
        report += f"   🎯 Perfect! Target reached!\n\n"
    else:
        report += f"   ⚠️ {abs(cal_remaining)} kcal over target\n\n"
    
    # Protein
    protein_current = totals['protein']
    protein_target = targets['protein']
    report += f"💪 **Protein:** {protein_current}g / {protein_target}g\n"
    report += f"   {create_progress_bar(protein_current, protein_target)}\n\n"
    
    # Carbs
    carbs_current = totals['carbs']
    carbs_target = targets['carbs']
    report += f"🍞 **Carbs:** {carbs_current}g / {carbs_target}g\n"
    report += f"   {create_progress_bar(carbs_current, carbs_target)}\n\n"
    
    # Fats
    fats_current = totals['fats']
    fats_target = targets['fats']
    report += f"🥑 **Fats:** {fats_current}g / {fats_target}g\n"
    report += f"   {create_progress_bar(fats_current, fats_target)}\n\n"
    
    # Fiber
    fiber_current = totals['fiber']
    fiber_target = targets['fiber']
    report += f"🌾 **Fiber:** {fiber_current}g / {fiber_target}g\n"
    report += f"   {create_progress_bar(fiber_current, fiber_target)}\n\n"
    
    report += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Summary message
    if cal_current < cal_target * 0.5:
        report += "💡 **Tip:** You're doing great! Keep tracking your meals.\n"
    elif cal_current < cal_target * 0.8:
        report += "💡 **Tip:** You're on track! Don't forget your remaining meals.\n"
    elif cal_current <= cal_target:
        report += "💡 **Tip:** Almost there! You're close to your daily goal.\n"
    else:
        report += "💡 **Tip:** You've exceeded your target. Stay mindful of portions.\n"
    
    report += "\n🎯 Keep up the great work! 💪"
    
    return report


async def generate_now_report(telegram_user_id: int) -> str:
    """
    Generate the current day's nutrition report.
    
    Args:
        telegram_user_id: Telegram user ID
        
    Returns:
        Formatted report string or error message
    """
    user = await get_user_by_telegram_id(telegram_user_id)
    
    if not user:
        return "❌ User not found. Please register first with /start"
    
    data = await get_today_nutrition_data(user)
    report = format_now_report(data)
    
    return report
