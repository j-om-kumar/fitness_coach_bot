"""Conversation context management for multi-turn interactions."""
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

# Simple in-memory storage for conversation context
# Key format: f"{user_id}:{context_type}"
# In production, use Redis or database
_conversation_contexts: Dict[str, 'ConversationContext'] = {}

# Default context expires after 5 minutes of inactivity
DEFAULT_CONTEXT_TIMEOUT = 300  # seconds


class ConversationContext:
    """Manages conversation context for a user."""
    
    def __init__(self, user_id: int, context_type: str = 'default'):
        self.user_id = user_id
        self.context_type = context_type
        self.data: Dict[str, Any] = {}
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
    
    def set(self, key: str, value: Any) -> None:
        """Set a context value."""
        self.data[key] = value
        self.last_updated = datetime.now()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a context value."""
        return self.data.get(key, default)
    
    def clear(self) -> None:
        """Clear all context data."""
        self.data.clear()
        self.last_updated = datetime.now()
    
    def is_expired(self, timeout_seconds: int = DEFAULT_CONTEXT_TIMEOUT) -> bool:
        """
        Check if context has expired.
        
        Args:
            timeout_seconds: Timeout in seconds (default 300 = 5 minutes)
            
        Returns:
            True if expired, False otherwise
        """
        elapsed = (datetime.now() - self.last_updated).total_seconds()
        return elapsed > timeout_seconds
    
    @staticmethod
    def get_context(user_id: int, context_type: str = 'default') -> Optional['ConversationContext']:
        """
        Get conversation context for a user.
        
        Args:
            user_id: Telegram user ID
            context_type: Type of context (e.g., 'recipe_chat', 'meal_followup')
            
        Returns:
            ConversationContext instance or None if not found
        """
        # Clean up expired contexts
        ConversationContext._cleanup_expired_contexts()
        
        key = f"{user_id}:{context_type}"
        return _conversation_contexts.get(key)
    
    @staticmethod
    def save_context(user_id: int, context_type: str, data: Dict[str, Any]) -> 'ConversationContext':
        """
        Save or update conversation context for a user.
        
        Args:
            user_id: Telegram user ID
            context_type: Type of context
            data: Context data to save
            
        Returns:
            ConversationContext instance
        """
        key = f"{user_id}:{context_type}"
        
        if key in _conversation_contexts:
            # Update existing context
            ctx = _conversation_contexts[key]
            ctx.data.update(data)
            ctx.last_updated = datetime.now()
        else:
            # Create new context
            ctx = ConversationContext(user_id, context_type)
            ctx.data = data
            _conversation_contexts[key] = ctx
        
        return ctx
    
    @staticmethod
    def clear_context(user_id: int, context_type: str = 'default') -> None:
        """
        Clear conversation context for a user.
        
        Args:
            user_id: Telegram user ID
            context_type: Type of context to clear
        """
        key = f"{user_id}:{context_type}"
        if key in _conversation_contexts:
            del _conversation_contexts[key]
    
    @staticmethod
    def _cleanup_expired_contexts() -> None:
        """Remove expired conversation contexts."""
        expired_keys = [
            key for key, ctx in _conversation_contexts.items()
            if ctx.is_expired()
        ]
        
        for key in expired_keys:
            del _conversation_contexts[key]


# Legacy function for backward compatibility
def get_context(user_id: int) -> ConversationContext:
    """
    Get or create conversation context for a user (legacy function).
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        ConversationContext instance
    """
    ctx = ConversationContext.get_context(user_id, 'default')
    if not ctx:
        ctx = ConversationContext.save_context(user_id, 'default', {})
    return ctx


def clear_context(user_id: int) -> None:
    """
    Clear conversation context for a user (legacy function).
    
    Args:
        user_id: Telegram user ID
    """
    ConversationContext.clear_context(user_id, 'default')
