"""Simple memory management for the Notion assistant."""
from typing import Dict, List, Tuple
from datetime import datetime, timezone

class Memory:
    """Memory store for chat history with simple role and content storage."""
    
    def __init__(self):
        self._messages: List[Dict[str, str]] = []  # List of message dicts
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation history.
        Args:
            role: Either 'user' or 'ai'
            content: The message content
        """
        message = {
            'role': role,
            'timestamp': datetime.now(tz=timezone.utc).isoformat(),
            'content': content
        }
        self._messages.append(message)
    
    def get_messages(self) -> List[Dict[str, str]]:
        """Get all messages in a format suitable for the agent."""
        return [{
            'role': msg['role'],
            'content': msg['content']
        } for msg in self._messages]

# Global memory instance
memory = Memory()
