"""Text-based meal analysis service."""
import json
from typing import Optional, Dict, Any
from openai import OpenAI

from app.config import OPENAI_API_KEY, OPENAI_MODEL

client = OpenAI(api_key=OPENAI_API_KEY)

TEXT_MEAL_ANALYSIS_PROMPT = """
You are a nutrition coach. The user is describing a meal they ate in natural language.

Analyze their description and provide detailed nutritional estimates.

Return STRICT JSON only with these exact keys:
{
  "is_trackable": true/false,  // Can you estimate nutrition from this description?
  "meal_type": "breakfast|lunch|dinner|snack|unknown",
  "description": "cleaned up description of the food",
  "calories_kcal": <int or null>,
  "protein_g": <int or null>,
  "carbs_g": <int or null>,
  "fats_g": <int or null>,
  "fiber_g": <int or null>,
  "confidence": "low|medium|high",
  "missing_info": "what information would help make a better estimate" or null
}

Examples of trackable descriptions:
- "I had 2 eggs and toast for breakfast"
- "Ate chicken curry with rice, about 200g chicken"
- "Had a protein shake with banana"
- "Pizza, 3 slices"

Examples of non-trackable descriptions:
- "I'm hungry"
- "What should I eat?"
- "Hello"
- "How are you?"

If the description is trackable but vague (e.g., "ate lunch"), set is_trackable to true but confidence to low and suggest missing_info.

No extra keys, no markdown, no explanations. Just the JSON.
"""


class TextMealAnalysisResult:
    """Result from text-based meal analysis."""
    
    def __init__(self, data: Dict[str, Any]):
        self.is_trackable: bool = data.get("is_trackable", False)
        self.meal_type: str = data.get("meal_type", "unknown")
        self.description: Optional[str] = data.get("description")
        self.calories_kcal: Optional[int] = data.get("calories_kcal")
        self.protein_g: Optional[int] = data.get("protein_g")
        self.carbs_g: Optional[int] = data.get("carbs_g")
        self.fats_g: Optional[int] = data.get("fats_g")
        self.fiber_g: Optional[int] = data.get("fiber_g")
        self.confidence: str = data.get("confidence", "low")
        self.missing_info: Optional[str] = data.get("missing_info")


async def analyze_text_meal(user_text: str) -> Optional[TextMealAnalysisResult]:
    """
    Analyze a text description of a meal.
    
    Args:
        user_text: User's description of their meal
        
    Returns:
        TextMealAnalysisResult if successful, None otherwise
    """
    try:
        # Call OpenAI API
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": TEXT_MEAL_ANALYSIS_PROMPT},
                {"role": "user", "content": user_text}
            ]
        )
        
        # Parse JSON response
        raw_json = response.choices[0].message.content.strip()
        data = json.loads(raw_json)
        
        return TextMealAnalysisResult(data)
        
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"Error analyzing text meal: {e}")
        return None
