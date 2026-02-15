"""Recipe suggestion service using AI to provide personalized meal recommendations."""
from typing import Optional, Dict
import json
from openai import OpenAI
from app.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)
OPENAI_MODEL = "gpt-4o-mini"

RECIPE_SYSTEM_PROMPT = """You are a helpful nutrition coach and recipe expert. Your role is to suggest simple, practical recipes based on:
1. User's remaining daily macros (calories, protein, carbs, fats, fiber)
2. User's cooking skills and available ingredients
3. User's dietary preferences and restrictions
4. User's fitness goal (weight loss, muscle gain, maintenance)

Guidelines:
- Suggest recipes that fit within their remaining macro budget
- If they've exceeded their targets, suggest low-calorie, high-satiety options
- If they're under their targets, suggest nutrient-dense meals to meet goals
- Keep recipes simple and practical (15-30 minutes prep time)
- Provide clear ingredient lists and step-by-step instructions
- Include estimated macros for each recipe
- Be encouraging and supportive in your tone

Format your response as a friendly conversation, not a formal document.
"""


async def get_recipe_suggestion(
    user_message: str,
    remaining_calories: int,
    remaining_protein: int,
    remaining_carbs: int,
    remaining_fats: int,
    remaining_fiber: int,
    goal: str,
    conversation_history: list = None
) -> str:
    """
    Get AI-powered recipe suggestions based on remaining macros.
    
    Args:
        user_message: User's request (e.g., "I want something quick for dinner")
        remaining_calories: Remaining calories for the day
        remaining_protein: Remaining protein in grams
        remaining_carbs: Remaining carbs in grams
        remaining_fats: Remaining fats in grams
        remaining_fiber: Remaining fiber in grams
        goal: User's fitness goal
        conversation_history: Previous messages in the conversation
        
    Returns:
        AI-generated recipe suggestion
    """
    try:
        # Build context message about user's macro status
        if remaining_calories > 0:
            macro_context = f"""
User's Remaining Macros for Today:
- Calories: {remaining_calories} kcal
- Protein: {remaining_protein}g
- Carbs: {remaining_carbs}g
- Fats: {remaining_fats}g
- Fiber: {remaining_fiber}g

Goal: {goal.replace('_', ' ').title()}

The user has room in their daily budget. Suggest meals that help them reach their targets.
"""
        else:
            over_calories = abs(remaining_calories)
            macro_context = f"""
User's Macro Status for Today:
- Already OVER target by {over_calories} kcal
- Remaining Protein: {remaining_protein}g
- Remaining Carbs: {remaining_carbs}g
- Remaining Fats: {remaining_fats}g

Goal: {goal.replace('_', ' ').title()}

The user has exceeded their calorie target. Suggest low-calorie, high-satiety options or encourage them to adjust tomorrow's intake.
"""
        
        # Build conversation messages
        messages = [
            {"role": "system", "content": RECIPE_SYSTEM_PROMPT},
            {"role": "system", "content": macro_context}
        ]
        
        # Add conversation history if exists
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.8,  # More creative for recipe suggestions
            max_tokens=800
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"Error getting recipe suggestion: {e}")
        return None


def format_macro_summary(
    consumed_calories: int,
    target_calories: int,
    consumed_protein: int,
    target_protein: int,
    consumed_carbs: int,
    target_carbs: int,
    consumed_fats: int,
    target_fats: int
) -> str:
    """
    Format a user-friendly macro summary.
    
    Returns:
        Formatted string with macro progress
    """
    remaining_calories = target_calories - consumed_calories
    remaining_protein = target_protein - consumed_protein
    remaining_carbs = target_carbs - consumed_carbs
    remaining_fats = target_fats - consumed_fats
    
    cal_pct = int((consumed_calories / target_calories) * 100) if target_calories > 0 else 0
    protein_pct = int((consumed_protein / target_protein) * 100) if target_protein > 0 else 0
    
    summary = f"📊 **Today's Progress:**\n"
    summary += f"• Calories: {consumed_calories}/{target_calories} kcal ({cal_pct}%)\n"
    summary += f"• Protein: {consumed_protein}/{target_protein}g ({protein_pct}%)\n"
    summary += f"• Carbs: {consumed_carbs}/{target_carbs}g\n"
    summary += f"• Fats: {consumed_fats}/{target_fats}g\n\n"
    
    if remaining_calories > 0:
        summary += f"✅ You have **{remaining_calories} kcal** remaining today.\n"
        if remaining_protein > 0:
            summary += f"💪 Try to get **{remaining_protein}g more protein**!\n"
    else:
        summary += f"⚠️ You're **{abs(remaining_calories)} kcal over** your target.\n"
        summary += "Consider lighter meals for the rest of the day.\n"
    
    return summary
