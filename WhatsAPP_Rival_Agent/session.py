from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional
from agents import SQLiteSession

@dataclass
class UserContext:
    """Per WhatsApp sender context (in-memory; restart clears)."""
    last_code: Optional[str] = None
    function_id: Optional[str] = None      
    function_slug: Optional[str] = None    
    
    # 🌟 NEW: Agent Routing & Session Flags
    active_agent_id: Optional[str] = None        # Stores the adopted agent_id
    active_agent_name: Optional[str] = None      # Stores the user-friendly name
    agent_conversation_id: Optional[str] = None  # Tracks conversation window for that agent
    pending_search_query: Optional[str] = None   # Tracks if assistant is awaiting search terms

_contexts = {}


def get_user_context(sender_id: str) -> UserContext:
    if sender_id not in _contexts:
        _contexts[sender_id] = UserContext()
    return _contexts[sender_id]

def get_agent_session(sender_id: str) -> SQLiteSession:
    """SQLite session to persist chat history automatically."""
    db_dir = "User_Sessions_Directory"
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "whatsapp_sessions.db")
    return SQLiteSession(session_id=sender_id, db_path=db_path)