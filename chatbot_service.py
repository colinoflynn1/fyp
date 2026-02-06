"""AI chatbot service using Google Gemini for savings advice and goal creation."""

# Reference: Based on Google Gen AI SDK Documentation
# https://googleapis.github.io/python-genai/
# Reference: Gemini API Quickstart - https://ai.google.dev/gemini-api/docs/quickstart
# Reference: Gemini API Text Generation - https://ai.google.dev/gemini-api/docs/text-generation
# Reference: Gemini API Models - https://ai.google.dev/gemini-api/docs/models

from __future__ import annotations

import json
import re
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from goals import FREQUENCIES, build_progress, list_goals

# Reference: Lazy import pattern to avoid startup failure if GEMINI_API_KEY is missing
# Adapted from Python import best practices
_genai_client = None


# Reference: Based on Google Gen AI SDK - Client initialization
# https://ai.google.dev/gemini-api/docs/api-key
def _get_client():
    """Lazy-load the Gemini client."""
    global _genai_client
    if _genai_client is None:
        from google import genai
        from google.genai import types
        api_key = __import__("os").environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Add it to your .env file. "
                "Get a free key at https://aistudio.google.com/apikey"
            )
        _genai_client = (genai, types)
    return _genai_client


# Reference: Based on Gemini API System Instructions
# https://ai.google.dev/gemini-api/docs/text-generation#system_instructions
# Reference: Prompt engineering for structured output (JSON goal proposal)
def build_system_prompt() -> str:
    """Build the system instruction for the savings advisor chatbot."""
    return """You are a friendly savings advisor for a personal finance app. Your role is to:
1. Give personalized savings advice based on the user's budget and preferred contribution frequency (weekly, bi-weekly, or monthly).
2. When appropriate, propose a new savings goal that fits their situation.
3. Be concise, warm, and practical. Use euros (€) for amounts.

CRITICAL - Source of truth for current goals: The "Current savings goals" (or "The user has no savings goals yet") section below is fetched LIVE from the database on every message. It is the ONLY authoritative list of what goals exist. NEVER assume a goal exists based on earlier messages in our conversation—the user may have deleted it, cancelled creation, or it may never have been created. If the context says they have no goals, they have no goals. If a goal is not listed, it does not exist.

IMPORTANT - When you want to propose creating a savings goal, you MUST include a JSON block at the end of your message in this exact format (replace values as needed):

```json
{"proposed_goal": {"goal_name": "Emergency Fund", "target_amount": 1000, "target_date": "2025-12-31", "frequency": "weekly", "initial_deposit": 0}}
```

Rules for proposed goals:
- goal_name: A short, descriptive name
- target_amount: Number in euros (no € symbol)
- target_date: YYYY-MM-DD format, must be in the future
- frequency: Must be exactly one of: weekly, bi-weekly, monthly
- initial_deposit: Number (0 if none)

Before proposing a goal, summarize what you're suggesting and ask if they'd like you to create it. Only output the proposed_goal JSON when the user has agreed or asked you to create it. The user must confirm before the goal is actually created."""


# Reference: Uses list_goals and build_progress from goals.py (project-internal)
def build_context_message(user_id: int) -> str:
    """Build a context block with the user's current goals and progress."""
    goals = list_goals(user_id)
    if not goals:
        return "The user has no savings goals yet."
    lines = ["Current savings goals:"]
    for g in goals:
        prog = build_progress(g)
        lines.append(
            f"- {g['goal_name']}: €{prog['saved_amount']} / €{prog['target_amount']} "
            f"({prog['percent_complete']:.0f}% complete), {g['frequency']} contributions"
        )
    return "\n".join(lines)


# Reference: Based on Python re module - https://docs.python.org/3/library/re.html
# Reference: Based on Python json module - https://docs.python.org/3/library/json.html
def parse_proposed_goal(text: str) -> Optional[Dict[str, Any]]:
    """Extract a proposed_goal JSON block from the AI response."""
    # Look for ```json ... ``` or ``` ... ``` blocks (common LLM output format)
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        block = match.group(1).strip()
        try:
            data = json.loads(block)
            return data.get("proposed_goal")
        except json.JSONDecodeError:
            pass
    # Fallback: look for {"proposed_goal": ...} anywhere
    match = re.search(r'\{[^{}]*"proposed_goal"\s*:\s*\{[^}]+\}[^{}]*\}', text)
    if match:
        try:
            data = json.loads(match.group(0))
            return data.get("proposed_goal")
        except json.JSONDecodeError:
            pass
    return None


# Reference: Based on Google Gen AI SDK - generate_content with multi-turn conversation
# https://ai.google.dev/gemini-api/docs/text-generation#multi-turn
# Reference: Content and Part types - https://googleapis.github.io/python-genai/
def chat(
    user_id: int,
    user_message: str,
    history: List[Dict[str, str]],
) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Send a message to the chatbot and get a response.
    Returns (response_text, proposed_goal or None).
    """
    import os as _os
    genai_mod, types_mod = _get_client()
    client = genai_mod.Client()

    context = build_context_message(user_id)
    system = build_system_prompt() + f"\n\n{context}"

    # Build contents for multi-turn: history + new message
    contents = []
    for h in history:
        role = "user" if h.get("role") == "user" else "model"
        text = h.get("content", "")
        if text:
            contents.append(types_mod.Content(role=role, parts=[types_mod.Part.from_text(text=text)]))

    # Add the new user message
    contents.append(types_mod.Content(role="user", parts=[types_mod.Part.from_text(text=user_message)]))

    config = types_mod.GenerateContentConfig(
        system_instruction=system,
        temperature=0.7,
    )

    model = _os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    # Fallback chain: 2.5-flash -> 2.5-flash-lite -> 2.0-flash -> 2.0-flash-lite
    # (gemini-1.5-flash is deprecated and returns 404)
    fallbacks_404 = ["gemini-2.5-flash-lite", "gemini-2.0-flash", "gemini-2.0-flash-lite"]
    fallbacks_429 = ["gemini-2.5-flash-lite", "gemini-2.0-flash-lite"]
    try:
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )
    except Exception as e:
        err_str = str(e)
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            for fb in fallbacks_429:
                if fb != model:
                    try:
                        response = client.models.generate_content(
                            model=fb,
                            contents=contents,
                            config=config,
                        )
                        break
                    except Exception:
                        continue
            else:
                raise ValueError(
                    "Gemini API quota exceeded. Please wait a minute and try again."
                ) from e
        elif "404" in err_str or "not found" in err_str.lower():
            for fb in fallbacks_404:
                try:
                    response = client.models.generate_content(
                        model=fb,
                        contents=contents,
                        config=config,
                    )
                    break
                except Exception:
                    continue
            else:
                raise ValueError(
                    "No compatible Gemini model available. Try setting GEMINI_MODEL=gemini-2.0-flash in .env"
                ) from e
        else:
            raise

    response_text = (response.text or "").strip()
    proposed = parse_proposed_goal(response_text)

    return response_text, proposed


# Reference: Based on goals.py create_goal validation logic (project-internal)
# Reference: Python Decimal - https://docs.python.org/3/library/decimal.html
# Reference: Python datetime - https://docs.python.org/3/library/datetime.html
def validate_and_fix_proposed_goal(proposed: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict]]:
    """
    Validate a proposed goal and return (is_valid, error_message, fixed_goal).
    Fixes minor issues like date format.
    """
    name = (proposed.get("goal_name") or "").strip()
    target = proposed.get("target_amount")
    target_date_str = proposed.get("target_date", "")
    freq = (proposed.get("frequency") or "").strip().lower()
    initial = proposed.get("initial_deposit", 0)

    if not name:
        return False, "Goal name is required.", None
    if freq not in FREQUENCIES:
        return False, f"Frequency must be one of: {', '.join(FREQUENCIES)}", None

    try:
        target_dec = Decimal(str(target))
        if target_dec <= 0:
            return False, "Target amount must be positive.", None
    except Exception:
        return False, "Invalid target amount.", None

    try:
        initial_dec = Decimal(str(initial))
        if initial_dec < 0:
            return False, "Initial deposit cannot be negative.", None
    except Exception:
        initial_dec = Decimal("0")

    # Parse date
    try:
        target_date = date.fromisoformat(target_date_str)
    except (TypeError, ValueError):
        # Default: 1 year from today
        target_date = date.today() + timedelta(days=365)

    if target_date <= date.today():
        target_date = date.today() + timedelta(days=30)

    return True, "", {
        "goal_name": name,
        "target_amount": target_dec,
        "target_date": target_date,
        "frequency": freq,
        "initial_deposit": initial_dec,
    }
