"""Calorie calculation utilities using Mifflin-St Jeor equation."""
from typing import Literal

# Activity level multipliers for TDEE calculation
ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,        # Little or no exercise
    "lightly_active": 1.375,  # 1-2 days/week
    "moderately_active": 1.55,  # 3-4 days/week
    "very_active": 1.725,    # 5-6 days/week
    "extremely_active": 1.9  # Daily exercise
}

# Calorie adjustments based on goal
GOAL_ADJUSTMENTS = {
    "weight_loss": -500,      # 500 calorie deficit for ~0.5kg/week loss
    "muscle_gain": +300,      # 300 calorie surplus for muscle gain
    "maintenance": 0,         # No adjustment
    "general_fitness": -200   # Slight deficit for body recomposition
}


def calculate_bmr(weight_kg: float, height_cm: float, age: int = 30, gender: str = "male") -> float:
    """
    Calculate Basal Metabolic Rate using Mifflin-St Jeor equation.
    
    Args:
        weight_kg: Weight in kilograms
        height_cm: Height in centimeters
        age: Age in years (default 30 if unknown)
        gender: 'male' or 'female' (default 'male')
        
    Returns:
        BMR in calories/day
    """
    # Mifflin-St Jeor Equation
    # Men: BMR = (10 × weight in kg) + (6.25 × height in cm) - (5 × age in years) + 5
    # Women: BMR = (10 × weight in kg) + (6.25 × height in cm) - (5 × age in years) - 161
    
    bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)
    
    if gender.lower() == "female":
        bmr -= 161
    else:
        bmr += 5
    
    return bmr


def calculate_tdee(bmr: float, activity_level: str) -> float:
    """
    Calculate Total Daily Energy Expenditure.
    
    Args:
        bmr: Basal Metabolic Rate
        activity_level: Activity level key
        
    Returns:
        TDEE in calories/day
    """
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.2)
    return bmr * multiplier


def calculate_daily_calorie_target(
    weight_kg: float,
    height_cm: float,
    activity_level: str,
    goal: str,
    age: int = 30,
    gender: str = "male"
) -> int:
    """
    Calculate personalized daily calorie target.
    
    Args:
        weight_kg: Current weight in kg
        height_cm: Height in cm
        activity_level: Activity level (sedentary, lightly_active, etc.)
        goal: Fitness goal (weight_loss, muscle_gain, maintenance, general_fitness)
        age: Age in years (default 30)
        gender: Gender (default 'male')
        
    Returns:
        Daily calorie target (integer)
    """
    # Calculate BMR
    bmr = calculate_bmr(weight_kg, height_cm, age, gender)
    
    # Calculate TDEE
    tdee = calculate_tdee(bmr, activity_level)
    
    # Apply goal adjustment
    adjustment = GOAL_ADJUSTMENTS.get(goal, 0)
    target = tdee + adjustment
    
    # Ensure minimum safe calorie intake
    # Men: minimum 1500, Women: minimum 1200
    min_calories = 1200 if gender.lower() == "female" else 1500
    target = max(target, min_calories)
    
    return int(target)


def get_activity_display_name(activity_level: str) -> str:
    """Get user-friendly display name for activity level."""
    display_names = {
        "sedentary": "Not Active",
        "lightly_active": "1-2 days/week",
        "moderately_active": "3-4 days/week",
        "very_active": "5-6 days/week",
        "extremely_active": "Daily"
    }
    return display_names.get(activity_level, activity_level)


def calculate_macro_targets(daily_calories: int, weight_kg: float, goal: str) -> dict:
    """
    Calculate daily macro targets based on calories and goal.
    
    Args:
        daily_calories: Daily calorie target
        weight_kg: Current weight in kg
        goal: Fitness goal
        
    Returns:
        Dictionary with protein_g, carbs_g, fats_g, fiber_g targets
    """
    # Protein targets (g/kg body weight)
    protein_ratios = {
        "weight_loss": 2.2,      # Higher protein to preserve muscle during deficit
        "muscle_gain": 2.0,      # High protein for muscle building
        "maintenance": 1.8,      # Moderate protein
        "general_fitness": 1.8   # Moderate protein
    }
    
    protein_ratio = protein_ratios.get(goal, 1.8)
    protein_g = int(weight_kg * protein_ratio)
    
    # Fat targets (% of calories)
    fat_percentages = {
        "weight_loss": 0.25,     # 25% of calories from fat
        "muscle_gain": 0.25,     # 25% of calories from fat
        "maintenance": 0.30,     # 30% of calories from fat
        "general_fitness": 0.28  # 28% of calories from fat
    }
    
    fat_percentage = fat_percentages.get(goal, 0.28)
    fat_calories = daily_calories * fat_percentage
    fats_g = int(fat_calories / 9)  # 9 calories per gram of fat
    
    # Calculate remaining calories for carbs
    protein_calories = protein_g * 4  # 4 calories per gram of protein
    remaining_calories = daily_calories - protein_calories - fat_calories
    carbs_g = int(remaining_calories / 4)  # 4 calories per gram of carbs
    
    # Fiber target (general health recommendation)
    # 14g per 1000 calories
    fiber_g = int((daily_calories / 1000) * 14)
    
    return {
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fats_g": fats_g,
        "fiber_g": fiber_g
    }

