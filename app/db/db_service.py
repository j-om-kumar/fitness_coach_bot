"""Database service layer for user and log operations."""
from datetime import date
from typing import Optional

from sqlalchemy import select
from app.db.db import SessionLocal, User, DailyLog, Meal

from app.config import DEFAULT_TZ


async def get_or_create_daily_log(session, user_id: int, log_date: date) -> DailyLog:
    """
    Get or create a daily log entry for a user.
    
    Args:
        session: Database session
        user_id: User ID
        log_date: Date for the log
        
    Returns:
        DailyLog instance
    """
    query = await session.execute(
        select(DailyLog).where(
            DailyLog.user_id == user_id,
            DailyLog.log_date == log_date
        )
    )
    daily_log = query.scalar_one_or_none()
    
    if daily_log:
        return daily_log
    
    # Create new log
    daily_log = DailyLog(user_id=user_id, log_date=log_date)
    session.add(daily_log)
    await session.commit()
    await session.refresh(daily_log)
    
    return daily_log


async def register_user(
    telegram_user_id: int,
    chat_id: int,
    timezone: str = DEFAULT_TZ
) -> User:
    """
    Register or update a user.
    
    Args:
        telegram_user_id: Telegram user ID
        chat_id: Telegram chat ID
        timezone: User timezone
        
    Returns:
        User instance
    """
    async with SessionLocal() as session:
        query = await session.execute(
            select(User).where(User.telegram_user_id == telegram_user_id)
        )
        user = query.scalar_one_or_none()
        
        if user:
            # Update existing user
            user.chat_id = chat_id
            user.timezone = timezone or user.timezone
            await session.commit()
            return user
        
        # Create new user
        user = User(
            telegram_user_id=telegram_user_id,
            chat_id=chat_id,
            timezone=timezone
        )
        session.add(user)
        await session.commit()
        
        return user


async def get_user_by_telegram_id(telegram_user_id: int) -> Optional[User]:
    """Get user by Telegram ID."""
    async with SessionLocal() as session:
        query = await session.execute(
            select(User).where(User.telegram_user_id == telegram_user_id)
        )
        return query.scalar_one_or_none()


async def save_weight(user: User, weight_kg: float) -> None:
    """Save user's weight for today."""
    async with SessionLocal() as session:
        daily_log = await get_or_create_daily_log(session, user.id, date.today())
        daily_log.weight_kg = weight_kg
        await session.commit()


async def save_steps(user: User, steps: int) -> None:
    """Save user's steps for today."""
    async with SessionLocal() as session:
        daily_log = await get_or_create_daily_log(session, user.id, date.today())
        daily_log.steps = steps
        await session.commit()


async def save_body_photo(user: User, photo_file_id: str) -> None:
    """Save user's body progress photo for today."""
    async with SessionLocal() as session:
        daily_log = await get_or_create_daily_log(session, user.id, date.today())
        daily_log.body_photo_file_id = photo_file_id
        await session.commit()


async def save_weight_scale_photo(user: User, photo_file_id: str, weight_kg: Optional[float] = None) -> None:
    """Save user's weight scale photo for today, optionally with extracted weight."""
    async with SessionLocal() as session:
        daily_log = await get_or_create_daily_log(session, user.id, date.today())
        daily_log.weight_scale_photo_file_id = photo_file_id
        if weight_kg is not None:
            daily_log.weight_kg = weight_kg
        await session.commit()



async def save_meal(
    user: User,
    meal_type: str,
    description: Optional[str],
    calories_kcal: Optional[int],
    protein_g: Optional[int],
    carbs_g: Optional[int],
    fats_g: Optional[int],
    fiber_g: Optional[int],
    photo_file_id: str
) -> Meal:
    """Save a meal entry with complete nutritional information."""
    async with SessionLocal() as session:
        daily_log = await get_or_create_daily_log(session, user.id, date.today())
        
        meal = Meal(
            daily_log_id=daily_log.id,
            meal_type=meal_type,
            description=description,
            calories_kcal=calories_kcal,
            protein_g=protein_g,
            carbs_g=carbs_g,
            fats_g=fats_g,
            fiber_g=fiber_g,
            photo_file_id=photo_file_id,
        )
        session.add(meal)
        await session.commit()
        await session.refresh(meal)
        
        return meal



async def get_all_users() -> list[User]:
    """Get all registered users."""
    async with SessionLocal() as session:
        result = await session.execute(select(User))
        return list(result.scalars().all())


async def is_user_registered(telegram_user_id: int) -> bool:
    """Check if user has completed registration."""
    user = await get_user_by_telegram_id(telegram_user_id)
    if not user:
        return False
    return user.registration_completed == 2


async def update_registration_step(telegram_user_id: int, step: int) -> None:
    """Update user's registration progress."""
    async with SessionLocal() as session:
        query = await session.execute(
            select(User).where(User.telegram_user_id == telegram_user_id)
        )
        user = query.scalar_one_or_none()
        if user:
            user.registration_completed = step
            await session.commit()


async def complete_registration(
    telegram_user_id: int,
    height_cm: float,
    weight_kg: float,
    target_weight_kg: float,
    goal: str,
    activity_level: str,
    daily_calorie_target: int,
    daily_protein_target: int,
    daily_carbs_target: int,
    daily_fats_target: int,
    daily_fiber_target: int
) -> User:
    """Complete user registration with all required data."""
    async with SessionLocal() as session:
        query = await session.execute(
            select(User).where(User.telegram_user_id == telegram_user_id)
        )
        user = query.scalar_one_or_none()
        
        if user:
            user.height_cm = height_cm
            user.initial_weight_kg = weight_kg
            user.target_weight_kg = target_weight_kg
            user.goal = goal
            user.activity_level = activity_level
            user.daily_calorie_target = daily_calorie_target
            user.daily_protein_target = daily_protein_target
            user.daily_carbs_target = daily_carbs_target
            user.daily_fats_target = daily_fats_target
            user.daily_fiber_target = daily_fiber_target
            user.registration_completed = 2  # Completed
            await session.commit()
            await session.refresh(user)
            return user
        
        raise ValueError(f"User with telegram_id {telegram_user_id} not found")


async def get_daily_summary(user: User, log_date: date) -> dict:
    """
    Get summary of consumed macros for a specific day.
    
    Args:
        user: User instance
        log_date: Date to get summary for
        
    Returns:
        Dictionary with total calories, protein, carbs, fats, fiber consumed
    """
    async with SessionLocal() as session:
        # Get daily log for the date
        query = await session.execute(
            select(DailyLog).where(
                DailyLog.user_id == user.id,
                DailyLog.log_date == log_date
            )
        )
        daily_log = query.scalar_one_or_none()
        
        if not daily_log:
            # No log for this day, return zeros
            return {
                'total_calories': 0,
                'total_protein': 0,
                'total_carbs': 0,
                'total_fats': 0,
                'total_fiber': 0
            }
        
        # Get all meals for this day
        meals_query = await session.execute(
            select(Meal).where(Meal.daily_log_id == daily_log.id)
        )
        meals = meals_query.scalars().all()
        
        # Calculate totals
        total_calories = sum(meal.calories_kcal or 0 for meal in meals)
        total_protein = sum(meal.protein_g or 0 for meal in meals)
        total_carbs = sum(meal.carbs_g or 0 for meal in meals)
        total_fats = sum(meal.fats_g or 0 for meal in meals)
        total_fiber = sum(meal.fiber_g or 0 for meal in meals)
        
        return {
            'total_calories': int(total_calories),
            'total_protein': int(total_protein),
            'total_carbs': int(total_carbs),
            'total_fats': int(total_fats),
            'total_fiber': int(total_fiber)
        }


async def get_meal_by_id(meal_id: int) -> Optional[Meal]:
    """
    Get a meal by its ID.
    
    Args:
        meal_id: Meal ID
        
    Returns:
        Meal instance or None if not found
    """
    async with SessionLocal() as session:
        result = await session.execute(
            select(Meal).where(Meal.id == meal_id)
        )
        return result.scalar_one_or_none()


async def update_meal(
    meal_id: int,
    meal_type: Optional[str] = None,
    description: Optional[str] = None,
    calories_kcal: Optional[int] = None,
    protein_g: Optional[int] = None,
    carbs_g: Optional[int] = None,
    fats_g: Optional[int] = None,
    fiber_g: Optional[int] = None
) -> Optional[Meal]:
    """
    Update an existing meal entry.
    
    Args:
        meal_id: ID of the meal to update
        meal_type: New meal type (optional)
        description: New description (optional)
        calories_kcal: New calories (optional)
        protein_g: New protein (optional)
        carbs_g: New carbs (optional)
        fats_g: New fats (optional)
        fiber_g: New fiber (optional)
        
    Returns:
        Updated Meal instance or None if not found
    """
    async with SessionLocal() as session:
        result = await session.execute(
            select(Meal).where(Meal.id == meal_id)
        )
        meal = result.scalar_one_or_none()
        
        if not meal:
            return None
        
        # Update only provided fields
        if meal_type is not None:
            meal.meal_type = meal_type
        if description is not None:
            meal.description = description
        if calories_kcal is not None:
            meal.calories_kcal = calories_kcal
        if protein_g is not None:
            meal.protein_g = protein_g
        if carbs_g is not None:
            meal.carbs_g = carbs_g
        if fats_g is not None:
            meal.fats_g = fats_g
        if fiber_g is not None:
            meal.fiber_g = fiber_g
        
        await session.commit()
        await session.refresh(meal)
        
        return meal


async def delete_meal(meal_id: int) -> bool:
    """
    Delete a meal entry.
    
    Args:
        meal_id: ID of the meal to delete
        
    Returns:
        True if deleted, False if not found
    """
    async with SessionLocal() as session:
        result = await session.execute(
            select(Meal).where(Meal.id == meal_id)
        )
        meal = result.scalar_one_or_none()
        
        if not meal:
            return False
        
        await session.delete(meal)
        await session.commit()
        
        return True
