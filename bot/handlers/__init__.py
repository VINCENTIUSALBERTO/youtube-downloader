"""Handlers package."""

from bot.handlers.start import start_command, help_command
from bot.handlers.admin import (
    admin_command,
    add_token_command,
    stats_command,
    broadcast_command,
)
from bot.handlers.download import handle_url_message
from bot.handlers.callback import handle_callback_query

__all__ = [
    "start_command",
    "help_command",
    "admin_command",
    "add_token_command",
    "stats_command",
    "broadcast_command",
    "handle_url_message",
    "handle_callback_query",
]
