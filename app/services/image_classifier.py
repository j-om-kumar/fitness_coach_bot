"""Image classification service to identify photo types."""
from typing import Optional, Literal
import base64
import json

from openai import OpenAI
from app.config import OPENAI_API_KEY, OPENAI_MODEL

client = OpenAI(api_key=OPENAI_API_KEY)

# Image type classification
ImageType = Literal["food", "weight_scale", "body_photo", "steps_count", "other"]

IMAGE_CLASSIFICATION_PROMPT = """
You are an image classifier for a fitness tracking app.

Analyze the image and classify it into ONE of these categories:
1. "food" - Any image containing food, meals, drinks, snacks
2. "weight_scale" - Image of a weighing scale showing weight measurement
3. "body_photo" - Progress photo of person's body (mirror selfie, body transformation, etc.)
4. "steps_count" - Screenshot or photo showing step count (fitness tracker, phone screen, etc.)
5. "other" - Anything else that doesn't fit the above categories

Return ONLY a JSON object with these keys:
{
  "image_type": "food" | "weight_scale" | "body_photo" | "steps_count" | "other",
  "confidence": "low" | "medium" | "high",
  "description": "brief description of what you see"
}

For weight_scale images, also try to extract:
{
  "weight_kg": <number or null>
}

For steps_count images, also try to extract:
{
  "steps": <number or null>
}

No markdown, no extra text, just the JSON.
"""


class ImageClassificationResult:
    """Result from image classification."""
    
    def __init__(self, data: dict):
        self.image_type: ImageType = data.get("image_type", "other")
        self.confidence: str = data.get("confidence", "low")
        self.description: Optional[str] = data.get("description")
        self.weight_kg: Optional[float] = data.get("weight_kg")
        self.steps: Optional[int] = data.get("steps")
    
    def is_trackable(self) -> bool:
        """Check if this image type should be tracked."""
        return self.image_type in ["food", "weight_scale", "body_photo", "steps_count"]


async def classify_image(file_bytes: bytes) -> Optional[ImageClassificationResult]:
    """
    Classify an image to determine its type.
    
    Args:
        file_bytes: Image file bytes
        
    Returns:
        ImageClassificationResult if successful, None otherwise
    """
    try:
        # Encode image to base64
        image_b64 = base64.b64encode(file_bytes).decode()
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": IMAGE_CLASSIFICATION_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Classify this image."},
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
        
        return ImageClassificationResult(data)
        
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"Error classifying image: {e}")
        return None
