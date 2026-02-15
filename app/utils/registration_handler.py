"""Registration conversation handler for new users."""
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters
)

from app.db.db_service import (
    register_user,
    is_user_registered,
    update_registration_step,
    complete_registration,
    get_user_by_telegram_id
)
from app.config import DEFAULT_TZ
from app.utils.calorie_calculator import calculate_daily_calorie_target, calculate_macro_targets

# Conversation states
ASKING_HEIGHT = 1
ASKING_WEIGHT = 2
ASKING_GOAL = 3
ASKING_TARGET_WEIGHT = 4
ASKING_ACTIVITY_LEVEL = 5

# Goal options
GOAL_OPTIONS = [
    ["🔥 Weight Loss", "💪 Muscle Gain"],
    ["⚖️ Maintenance", "🏃 General Fitness"]
]

# Activity level options
ACTIVITY_OPTIONS = [
    ["😴 Not Active", "🚶 1-2 days/week"],
    ["🏃 3-4 days/week", "💪 5-6 days/week"],
    ["🔥 Daily"]
]


async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the registration process."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Check if already registered
    if await is_user_registered(user.id):
        await update.message.reply_text(
            "✅ You're already registered!\n\n"
            "Send me:\n"
            "• A meal PHOTO anytime (I'll estimate calories/protein)\n"
            "• Weight like: 'weight 98.6'\n"
            "• Steps like: 'steps 8200'"
        )
        return ConversationHandler.END
    
    # Create user record if doesn't exist
    await register_user(user.id, chat_id, DEFAULT_TZ)
    await update_registration_step(user.id, 1)  # In progress
    
    await update.message.reply_text(
        f"👋 Welcome {user.first_name}!\n\n"
        "I'm your personal fitness coach. Let's get you set up!\n\n"
        "📏 **Step 1/5**: What's your height?\n"
        "Please send it in centimeters (e.g., 175 or 170.5)",
        parse_mode="Markdown"
    )
    
    return ASKING_HEIGHT


async def receive_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and validate height."""
    text = update.message.text.strip()
    
    try:
        height = float(text)
        
        # Validate height range (100cm to 250cm)
        if not (100 <= height <= 250):
            await update.message.reply_text(
                "❌ That doesn't seem right. Height should be between 100-250 cm.\n"
                "Please try again:"
            )
            return ASKING_HEIGHT
        
        # Store in context
        context.user_data['height_cm'] = height
        
        await update.message.reply_text(
            f"✅ Height: {height} cm\n\n"
            "⚖️ **Step 2/5**: What's your current weight?\n"
            "Please send it in kilograms (e.g., 75 or 75.5)",
            parse_mode="Markdown"
        )
        
        return ASKING_WEIGHT
        
    except ValueError:
        await update.message.reply_text(
            "❌ Please send a valid number for your height in cm (e.g., 175)"
        )
        return ASKING_HEIGHT


async def receive_weight(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and validate weight."""
    text = update.message.text.strip()
    
    try:
        weight = float(text)
        
        # Validate weight range (30kg to 250kg)
        if not (30 <= weight <= 250):
            await update.message.reply_text(
                "❌ That doesn't seem right. Weight should be between 30-250 kg.\n"
                "Please try again:"
            )
            return ASKING_WEIGHT
        
        # Store in context
        context.user_data['weight_kg'] = weight
        
        # Show goal options with keyboard
        reply_markup = ReplyKeyboardMarkup(
            GOAL_OPTIONS,
            one_time_keyboard=True,
            resize_keyboard=True
        )
        
        await update.message.reply_text(
            f"✅ Weight: {weight} kg\n\n"
            "🎯 **Step 3/5**: What's your fitness goal?\n"
            "Choose one from the options below:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return ASKING_GOAL
        
    except ValueError:
        await update.message.reply_text(
            "❌ Please send a valid number for your weight in kg (e.g., 75)"
        )
        return ASKING_WEIGHT


async def receive_target_weight(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and validate target weight."""
    text = update.message.text.strip()
    
    try:
        target_weight = float(text)
        
        # Validate target weight range (30kg to 250kg)
        if not (30 <= target_weight <= 250):
            await update.message.reply_text(
                "❌ That doesn't seem right. Target weight should be between 30-250 kg.\n"
                "Please try again:"
            )
            return ASKING_TARGET_WEIGHT
        
        # Store in context
        context.user_data['target_weight_kg'] = target_weight
        
        # Show activity level options with keyboard
        reply_markup = ReplyKeyboardMarkup(
            ACTIVITY_OPTIONS,
            one_time_keyboard=True,
            resize_keyboard=True
        )
        
        current_weight = context.user_data.get('weight_kg')
        goal_display = context.user_data.get('goal_display', 'your goal')
        weight_diff = target_weight - current_weight
        
        if weight_diff > 0:
            direction = f"gain {abs(weight_diff):.1f} kg"
        elif weight_diff < 0:
            direction = f"lose {abs(weight_diff):.1f} kg"
        else:
            direction = "maintain your current weight"
        
        await update.message.reply_text(
            f"✅ Target Weight: {target_weight} kg\n"
            f"📊 Goal: {direction}\n\n"
            "� **Step 5/5**: How active are you with exercise?\n"
            "Choose your typical weekly activity level:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return ASKING_ACTIVITY_LEVEL
        
    except ValueError:
        await update.message.reply_text(
            "❌ Please send a valid number for your target weight in kg (e.g., 70)"
        )
        return ASKING_TARGET_WEIGHT


async def receive_goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive goal and complete registration."""
    text = update.message.text.strip()
    
    # Map display text to database values
    goal_mapping = {
        "🔥 Weight Loss": "weight_loss",
        "💪 Muscle Gain": "muscle_gain",
        "⚖️ Maintenance": "maintenance",
        "🏃 General Fitness": "general_fitness"
    }
    
    goal = goal_mapping.get(text)
    
    if not goal:
        await update.message.reply_text(
            "❌ Please select one of the options from the keyboard."
        )
        return ASKING_GOAL
    
    # Store goal in context
    context.user_data['goal'] = goal
    context.user_data['goal_display'] = text
    
    await update.message.reply_text(
        f"✅ Goal: {text}\n\n"
        "� **Step 4/5**: What's your target weight?\n"
        "Please send your goal weight in kilograms (e.g., 70 or 80)",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )
    
    return ASKING_TARGET_WEIGHT


async def receive_activity_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive activity level, calculate calorie target, and complete registration."""
    text = update.message.text.strip()
    
    # Map display text to database values
    activity_mapping = {
        "😴 Not Active": "sedentary",
        "🚶 1-2 days/week": "lightly_active",
        "🏃 3-4 days/week": "moderately_active",
        "💪 5-6 days/week": "very_active",
        "🔥 Daily": "extremely_active"
    }
    
    activity_level = activity_mapping.get(text)
    
    if not activity_level:
        await update.message.reply_text(
            "❌ Please select one of the options from the keyboard."
        )
        return ASKING_ACTIVITY_LEVEL
    
    # Get stored data
    height = context.user_data.get('height_cm')
    weight = context.user_data.get('weight_kg')
    target_weight = context.user_data.get('target_weight_kg')
    goal = context.user_data.get('goal')
    goal_display = context.user_data.get('goal_display')
    user = update.effective_user
    
    # Calculate daily calorie target

    
    daily_calories = calculate_daily_calorie_target(
        weight_kg=weight,
        height_cm=height,
        activity_level=activity_level,
        goal=goal
    )
    
    # Calculate macro targets
    macros = calculate_macro_targets(
        daily_calories=daily_calories,
        weight_kg=weight,
        goal=goal
    )
    
    # Save to database
    await complete_registration(
        telegram_user_id=user.id,
        height_cm=height,
        weight_kg=weight,
        target_weight_kg=target_weight,
        goal=goal,
        activity_level=activity_level,
        daily_calorie_target=daily_calories,
        daily_protein_target=macros['protein_g'],
        daily_carbs_target=macros['carbs_g'],
        daily_fats_target=macros['fats_g'],
        daily_fiber_target=macros['fiber_g']
    )
    
    # Clear context
    context.user_data.clear()
    
    # Calculate BMI for personalized message
    height_m = height / 100
    bmi = weight / (height_m ** 2)
    
    # Calculate weight difference
    weight_diff = target_weight - weight
    if weight_diff > 0:
        progress_msg = f"• Target: Gain {abs(weight_diff):.1f} kg → {target_weight} kg\n"
    elif weight_diff < 0:
        progress_msg = f"• Target: Lose {abs(weight_diff):.1f} kg → {target_weight} kg\n"
    else:
        progress_msg = f"• Target: Maintain at {target_weight} kg\n"
    
    # Send completion message
    await update.message.reply_text(
        f"🎉 **Registration Complete!**\n\n"
        f"📊 Your Profile:\n"
        f"• Height: {height} cm\n"
        f"• Current Weight: {weight} kg\n"
        f"{progress_msg}"
        f"• BMI: {bmi:.1f}\n"
        f"• Goal: {goal_display}\n"
        f"• Activity: {text}\n\n"
        f"🎯 **Your Daily Nutrition Targets:**\n"
        f"• Calories: {daily_calories} kcal\n"
        f"• Protein: {macros['protein_g']} g\n"
        f"• Carbs: {macros['carbs_g']} g\n"
        f"• Fats: {macros['fats_g']} g\n"
        f"• Fiber: {macros['fiber_g']} g\n\n"
        f"These targets are calculated based on:\n"
        f"• Your current stats and goal\n"
        f"• Activity level\n"
        f"• Optimal macro ratios for {goal_display.lower()}\n\n"
        f"✅ **You're all set!**\n\n"
        f"Now you can:\n"
        f"• Send meal PHOTOS (I'll track all macros)\n"
        f"• Track daily weight: 'weight 75.5'\n"
        f"• Track steps: 'steps 8200'\n\n"
        f"I'll send you daily reports showing your progress toward these targets! 💪",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )

    
    return ConversationHandler.END



async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the registration process."""
    context.user_data.clear()
    
    await update.message.reply_text(
        "❌ Registration cancelled.\n\n"
        "Send /start whenever you're ready to begin!",
        reply_markup=ReplyKeyboardRemove()
    )
    
    return ConversationHandler.END


# Create the conversation handler
registration_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start_registration)],
    states={
        ASKING_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_height)],
        ASKING_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_weight)],
        ASKING_GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_goal)],
        ASKING_TARGET_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_target_weight)],
        ASKING_ACTIVITY_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_activity_level)],
    },
    fallbacks=[CommandHandler("cancel", cancel_registration)],
    name="registration",
    persistent=False
)
