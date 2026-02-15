"""Text parsing utilities for weight and steps."""
import re

# Regex patterns
WEIGHT_RE = re.compile(r"(?i)\b(weight|wt)\b.*?(\d{2,3}(\.\d)?)|^(\d{2,3}(\.\d)?)\b")
STEPS_RE = re.compile(r"(?i)\b(steps?)\b.*?(\d{3,6})|^(\d{3,6})\b")

# Validation ranges
WEIGHT_MIN = 30
WEIGHT_MAX = 250
STEPS_MIN = 100
STEPS_MAX = 200000


def parse_weight(text: str) -> float | None:
    """
    Parse weight from text input.
    
    Args:
        text: User input text
        
    Returns:
        Weight in kg if valid, None otherwise
    """
    match = WEIGHT_RE.search(text.strip())
    if not match:
        return None
    
    value = match.group(2) or match.group(4)
    try:
        weight = float(value)
        if WEIGHT_MIN <= weight <= WEIGHT_MAX:
            return weight
    except (ValueError, TypeError):
        pass
    
    return None


def parse_steps(text: str) -> int | None:
    """
    Parse steps from text input.
    
    Args:
        text: User input text
        
    Returns:
        Step count if valid, None otherwise
    """
    match = STEPS_RE.search(text.strip())
    if not match:
        return None
    
    value = match.group(2) or match.group(3)
    try:
        steps = int(value)
        if STEPS_MIN <= steps <= STEPS_MAX:
            return steps
    except (ValueError, TypeError):
        pass
    
    return None
