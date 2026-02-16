"""AI-powered intent classification for context-aware modifications."""
from typing import Optional, Dict, Any
import re


class IntentType:
    """Intent types for user messages."""
    MODIFY_MEAL = "modify_meal"
    DELETE_MEAL = "delete_meal"
    QUERY_MEAL = "query_meal"
    CHANGE_PORTION = "change_portion"
    CHANGE_MEAL_TYPE = "change_meal_type"
    ADD_TO_MEAL = "add_to_meal"
    CORRECT_VALUE = "correct_value"
    NONE = "none"


def detect_modification_intent(text: str) -> Dict[str, Any]:
    """
    Detect if user wants to modify their previous action.
    
    Args:
        text: User's message text
        
    Returns:
        Dictionary with intent type and extracted parameters
    """
    text_lower = text.lower().strip()
    
    # Delete/Remove intent
    delete_patterns = [
        r'\b(delete|remove|cancel|undo)\s+(that|it|the meal|this)\b',
        r'\b(that|it)\s+was\s+(wrong|mistake|incorrect)\b',
        r'\bnever\s+mind\b',
        r'\bignore\s+(that|it)\b'
    ]
    
    for pattern in delete_patterns:
        if re.search(pattern, text_lower):
            return {
                'intent': IntentType.DELETE_MEAL,
                'confidence': 'high'
            }
    
    # Add to meal intent
    add_patterns = [
        r'\b(add|include|also had)\s+(.+?)\s+(to\s+)?(that|it|the meal)\b',
        r'\b(and|plus)\s+(.+?)(\s+too)?$',
        r'\balso\s+(.+?)$'
    ]
    
    for pattern in add_patterns:
        match = re.search(pattern, text_lower)
        if match:
            # Extract what to add
            food_item = match.group(2) if match.lastindex >= 2 else match.group(1)
            return {
                'intent': IntentType.ADD_TO_MEAL,
                'food_item': food_item.strip(),
                'confidence': 'high'
            }
    
    # Portion size change intent
    portion_patterns = [
        r'\b(large|big|huge|small|tiny|medium)\s+(portion|size|serving)\b',
        r'\b(that|it)\s+was\s+(a\s+)?(large|big|huge|small|tiny|medium)\s+(portion|one|serving)?\b',
        r'\bmake\s+it\s+(large|big|huge|small|tiny|medium)\b',
        r'\bactually\s+(large|big|huge|small|tiny|medium)\b'
    ]
    
    for pattern in portion_patterns:
        match = re.search(pattern, text_lower)
        if match:
            # Extract portion size
            for word in ['large', 'big', 'huge', 'small', 'tiny', 'medium']:
                if word in text_lower:
                    portion_size = 'large' if word in ['large', 'big', 'huge'] else 'small' if word in ['small', 'tiny'] else 'medium'
                    return {
                        'intent': IntentType.CHANGE_PORTION,
                        'portion_size': portion_size,
                        'confidence': 'high'
                    }
    
    # Meal type change intent
    meal_type_patterns = [
        r'\b(that|it)\s+was\s+(actually\s+)?(breakfast|lunch|dinner|snack)\b',
        r'\bchange\s+(to|it to)\s+(breakfast|lunch|dinner|snack)\b',
        r'\bmake\s+it\s+(breakfast|lunch|dinner|snack)\b',
        r'\bnot\s+(breakfast|lunch|dinner|snack),?\s+(breakfast|lunch|dinner|snack)\b'
    ]
    
    for pattern in meal_type_patterns:
        match = re.search(pattern, text_lower)
        if match:
            # Extract meal type
            for meal_type in ['breakfast', 'lunch', 'dinner', 'snack']:
                if meal_type in text_lower:
                    return {
                        'intent': IntentType.CHANGE_MEAL_TYPE,
                        'meal_type': meal_type,
                        'confidence': 'high'
                    }
    
    # Query intent (asking about previous meal)
    query_patterns = [
        r'\b(how much|what was|what\'s|whats)\s+(the\s+)?(protein|calories|carbs|fats|fiber)\b',
        r'\b(protein|calories|carbs|fats|fiber)\s+(in\s+)?(that|it)\b',
        r'\btell me\s+(about\s+)?(that|it|the meal)\b'
    ]
    
    for pattern in query_patterns:
        match = re.search(pattern, text_lower)
        if match:
            # Extract what they're asking about
            nutrient = None
            for n in ['protein', 'calories', 'carbs', 'fats', 'fiber']:
                if n in text_lower:
                    nutrient = n
                    break
            
            return {
                'intent': IntentType.QUERY_MEAL,
                'nutrient': nutrient,
                'confidence': 'high'
            }
    
    # General modification intent
    modify_patterns = [
        r'\b(change|update|modify|correct|fix)\s+(that|it|the meal)\b',
        r'\b(actually|correction|oops)\b',
        r'\bthat\'s\s+not\s+right\b'
    ]
    
    for pattern in modify_patterns:
        if re.search(pattern, text_lower):
            return {
                'intent': IntentType.MODIFY_MEAL,
                'text': text,
                'confidence': 'medium'
            }
    
    # No clear intent detected
    return {
        'intent': IntentType.NONE,
        'confidence': 'none'
    }


def extract_portion_multiplier(portion_size: str) -> float:
    """
    Get multiplier for portion size adjustments.
    
    Args:
        portion_size: 'small', 'medium', or 'large'
        
    Returns:
        Multiplier for nutritional values
    """
    multipliers = {
        'small': 0.7,
        'medium': 1.0,
        'large': 1.5,
        'huge': 2.0
    }
    return multipliers.get(portion_size, 1.0)
