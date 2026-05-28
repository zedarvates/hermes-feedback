"""feedback_gateway.py — Inline star-rating buttons for Telegram/Discord gateway.

This module provides the gateway-side infrastructure for interactive
feedback buttons (⭐⭐⭐⭐⭐) on messaging platforms.

DESIGN PHILOSOPHY
------------------
Mirrors the existing `clarify` and `exec_approval` patterns in the
Hermes gateway (see issue #24191, PR #24199). Three components:

1. BLOCK-AND-WAIT primitive (tools/feedback_gateway.py)
   - Threading.Event-based queue, same shape as clarify_gateway.py
   - Agent thread blocks waiting for user button click

2. ADAPTER METHOD (telegram.py, discord.py)
   - send_feedback_buttons() — renders 5 star buttons
   - Handles callback_data prefix "fb:"

3. CALLBACK HANDLER (telegram.py _handle_callback_query)
   - Parses "fb:<session_key>:<rating>" from callback_data
   - Resolves via resolve_gateway_feedback()
   - Edits message to show the selected rating

USAGE IN SKILL
--------------
When the agent wants feedback, it calls:

    python3 feedback_gateway.py send <session_key> "<question>"

On Telegram, this sends a message with 5 inline star buttons.
The user taps one → rating is saved → message updates to show it.

TOKEN COST
----------
Agent thread blocks until button click, then unblocks with the rating.
Zero LLM tokens for the actual rating — the button callback directly
calls resolve_gateway_feedback() which writes to ratings.ndjson.
"""

import json
import os
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

FEED_DIR = os.path.expanduser("~/.hermes/feedback")

# ─── Block-and-wait primitive ──────────────────────────────────────────────

@dataclass
class _FeedbackEntry:
    event: threading.Event
    response: Optional[str] = None
    rating: Optional[int] = None

_feedback_queues: dict[str, _FeedbackEntry] = {}

_counter = 0
_lock = threading.Lock()

def _next_id() -> str:
    global _counter
    with _lock:
        _counter += 1
        return f"fb_{int(time.time())}_{_counter}"

def register_gateway_feedback(feedback_id: str) -> _FeedbackEntry:
    """Register a blocking feedback request. Called by the agent thread."""
    entry = _FeedbackEntry(event=threading.Event())
    _feedback_queues[feedback_id] = entry
    return entry

def resolve_gateway_feedback(feedback_id: str, rating: int, context: str = "") -> int:
    """Resolve a pending feedback request. Called by the button callback.
    Returns the number of entries resolved (0 or 1).
    """
    entry = _feedback_queues.pop(feedback_id, None)
    if entry is None:
        return 0
    entry.rating = rating
    entry.response = str(rating)
    entry.event.set()

    # Save to ndjson immediately (zero LLM tokens)
    save_rating(rating, context)

    return 1

def wait_for_feedback(feedback_id: str, timeout: float = 600) -> Optional[int]:
    """Block the agent thread waiting for a button click.
    Returns the rating (1-5) or None on timeout.
    """
    entry = _feedback_queues.get(feedback_id)
    if entry is None:
        return None
    if entry.event.wait(timeout=timeout):
        return entry.rating
    # Timeout
    _feedback_queues.pop(feedback_id, None)
    return None

def save_rating(rating: int, context: str = ""):
    """Write a rating to ratings.ndjson."""
    filepath = os.path.join(FEED_DIR, "ratings.ndjson")
    os.makedirs(FEED_DIR, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rating": rating,
        "session": os.environ.get("HERMES_SESSION_ID", "gateway"),
        "topic": "",
        "context": context,
        "source": "gateway_button",
    }
    with open(filepath, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return rating

# ─── Telegram integration blueprint ────────────────────────────────────────

TELEGRAM_BLUEPRINT = r"""
===========================================================================
INTEGRATION BLUEPRINT: Telegram Inline Star Buttons
===========================================================================
Add to: gateway/platforms/telegram.py

1) ADD METHOD to TelegramAdapter class (around line 2781, after send_clarify):
---------------------------------------------------------------------------

    async def send_feedback_buttons(
        self,
        chat_id: str,
        question: str,
        feedback_id: str,
        session_key: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SendResult:
        \"\"\"Send ⁄r rating buttons (1-5 stars) via inline keyboard.
        
        Each button has callback_data fb:<session_key>:<rating>.
        The button handler resolves via resolve_gateway_feedback().
        \"\"\"
        if not self._bot:
            return SendResult(success=False, error="Not connected")

        try:
            thread_id = self._metadata_thread_id(metadata)
            
            # Five star buttons in one row
            stars = ["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"]
            row = []
            for i in range(5):
                rating = i + 1
                row.append(
                    InlineKeyboardButton(
                        stars[i],
                        callback_data=f"fb:{session_key}:{rating}",
                    )
                )
            
            keyboard = InlineKeyboardMarkup([row])
            
            text = f"❓ {_html.escape(question)}"
            
            kwargs: Dict[str, Any] = {
                "chat_id": int(chat_id),
                "text": text,
                "parse_mode": ParseMode.HTML,
                "reply_markup": keyboard,
                **self._link_preview_kwargs(),
            }
            reply_to_id = self._reply_to_message_id_for_send(None, metadata)
            kwargs["reply_to_message_id"] = reply_to_id
            kwargs.update(
                self._thread_kwargs_for_send(
                    chat_id, thread_id, metadata,
                    reply_to_message_id=reply_to_id,
                )
            )
            
            msg = await self._send_message_with_thread_fallback(**kwargs)
            self._feedback_state[feedback_id] = session_key
            return SendResult(success=True, message_id=str(msg.message_id))
        except Exception as e:
            logger.warning("[%s] send_feedback_buttons failed: %s", self.name, e)
            return SendResult(success=False, error=str(e))


2) ADD STATE DICT in __init__ (around line 406):
---------------------------------------------------------------------------

    self._feedback_state: Dict[str, str] = {}  # feedback_id -> session_key


3) ADD HANDLER BLOCK in _handle_callback_query (after clarify handler at line ~3300):
---------------------------------------------------------------------------

        # --- Feedback button callbacks (fb:session_key:rating) ---
        if data.startswith("fb:"):
            parts = data.split(":", 2)
            if len(parts) == 3:
                session_key = parts[1]
                try:
                    rating = int(parts[2])
                except (ValueError, IndexError):
                    await query.answer(text="Invalid rating data.")
                    return

                # Find feedback_id from state
                feedback_id = None
                for fid, sk in self._feedback_state.items():
                    if sk == session_key:
                        feedback_id = fid
                        break

                if not feedback_id:
                    await query.answer(text="This feedback has already been submitted.")
                    return

                # Resolve — saves rating to ndjson
                user_display = getattr(query.from_user, "first_name", "User")
                try:
                    from tools.feedback_gateway import resolve_gateway_feedback
                    count = resolve_gateway_feedback(feedback_id, rating, f"via Telegram by {user_display}")
                    if count:
                        self._feedback_state.pop(feedback_id, None)
                except Exception as exc:
                    logger.error("Failed to resolve gateway feedback: %s", exc)
                    count = 0

                label = f"{'⭐' * rating} {rating}/5"
                await query.answer(text=label)

                # Edit message to show selection
                try:
                    await query.edit_message_text(
                        text=f"📊 {label} — thanks!",
                        reply_markup=None,
                    )
                except Exception:
                    pass

                # Resume typing indicator if needed
                query_chat_id = str(query.message.chat_id) if query.message else None
                if count and query_chat_id:
                    self.resume_typing_for_chat(query_chat_id)
            return


===========================================================================
DISCORD INTEGRATION
===========================================================================
For Discord, use discord.ui.Button with custom_id="fb:<rating>"
and a View with 5 buttons in one row. Same callback logic.

Add to gateway/platforms/discord.py:
    async def send_feedback_buttons(self, ...):
        view = discord.ui.View()
        for i in range(5):
            view.add_item(discord.ui.Button(
                label="⭐" * (i+1),
                custom_id=f"fb:{session_key}:{i+1}",
                style=discord.ButtonStyle.secondary,
            ))
        await message.edit(view=view)
"""

# ─── CLI usage for testing ─────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "blueprint":
        print(TELEGRAM_BLUEPRINT)
    elif len(sys.argv) >= 2 and sys.argv[1] == "save":
        rating = int(sys.argv[2])
        context = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else "gateway button"
        save_rating(rating, context)
        print(f"✓ Rating {rating}/5 saved (gateway style)")
    else:
        print("Usage:")
        print("  feedback_gateway.py blueprint    — show integration guide")
        print("  feedback_gateway.py save <1-5>   — save a rating (gateway style)")
        print("  feedback_gateway.py send <id> <q> — (standalone, not yet)")
