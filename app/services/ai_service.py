"""OpenAI integration for meal analysis."""
import base64
import json
from typing import Dict, Any, Optional

from openai import OpenAI

from app.config import OPENAI_API_KEY, OPENAI_MODEL

client = OpenAI(api_key=OPENAI_API_KEY)



# AI Prompts
MEAL_VISION_PROMPT = """
You are a nutrition coach. Analyze the meal photo and provide detailed nutritional estimates.
Return STRICT JSON only with these exact keys:
- meal_type (breakfast|lunch|dinner|snack|unknown)
- description (short description of the food items)
- calories_kcal (int or null)
- protein_g (int or null)
- carbs_g (int or null)
- fats_g (int or null)
- fiber_g (int or null)
- confidence (low|medium|high)

No extra keys, no markdown, no explanations.
If unsure about any value, set it to null and confidence to low.
Be as accurate as possible based on visible portion sizes and ingredients.
"""



class MealAnalysisResult:
    """Structured result from meal photo analysis."""
    
    def __init__(self, data: Dict[str, Any]):
        self.meal_type: str = data.get("meal_type", "unknown")
        self.description: Optional[str] = data.get("description")
        self.calories_kcal: Optional[int] = data.get("calories_kcal")
        self.protein_g: Optional[int] = data.get("protein_g")
        self.carbs_g: Optional[int] = data.get("carbs_g")
        self.fats_g: Optional[int] = data.get("fats_g")
        self.fiber_g: Optional[int] = data.get("fiber_g")
        self.confidence: str = data.get("confidence", "low")
    
    def is_valid(self) -> bool:
        """Check if analysis has meaningful data."""
        return self.calories_kcal is not None or self.protein_g is not None



async def analyze_meal_photo(file_bytes: bytes, user_notes: Optional[str] = None) -> Optional[MealAnalysisResult]:
    """
    Analyze a meal photo using OpenAI Vision API.
    
    Args:
        file_bytes: Image file bytes
        user_notes: Optional user-provided description/notes about the meal
        
    Returns:
        MealAnalysisResult if successful, None otherwise
    """
    try:
        # Encode image to base64
        image_b64 = base64.b64encode(file_bytes).decode()
        
        # Build user message
        user_message_text = "Estimate this meal."
        if user_notes:
            user_message_text += f"\n\nUser's notes: {user_notes}\n\nUse these details to make a more accurate estimate."
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": MEAL_VISION_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_message_text},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                        }
                    ]
                }
            ]
        )
        
        # Parse JSON response
        raw_json = response.choices[0].message.content.strip()
        data = json.loads(raw_json)
        
        return MealAnalysisResult(data)
        
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        # Log error in production
        print(f"Error analyzing meal photo: {e}")
        return None

