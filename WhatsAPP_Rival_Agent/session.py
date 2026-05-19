from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

# 🔥 Import the standard built-in SQLiteSession
from agents import SQLiteSession

@dataclass
class UserContext:
    """Per WhatsApp sender context (in-memory; restart clears).
    The conversational history is handled by SQLiteSession, 
    so this just stores tool-specific state like the last generated code.
    """
    last_code: Optional[str] = None

_contexts = {}

def get_user_context(sender_id: str) -> UserContext:
    if sender_id not in _contexts:
        _contexts[sender_id] = UserContext()
    return _contexts[sender_id]

# 🔥 Removed 'async' because SQLiteSession initializes synchronously
def get_agent_session(sender_id: str) -> SQLiteSession:
    """SQLite session to persist chat history automatically."""
    db_dir = "User_Sessions_Directory"
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "whatsapp_sessions.db")
    
    # Returns an SQLiteSession tailored for this sender
    return SQLiteSession(session_id=sender_id, db_path=db_path)