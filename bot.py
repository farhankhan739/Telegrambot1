#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
bot.py

A Telegram deep-link gateway bot built with python-telegram-bot v22+.

Run locally or on Railway with:
    python bot.py

Environment variables required:
    BOT_TOKEN - your bot token from @BotFather

Configuration:
    config.json (same directory as this file) - maps deep-link parameters
    to a target channel + destination link. Example:

    {
      "jjk": {
        "channel_username": "@AnimeStreet_backup",
        "destination_link": "https://t.me/+3RnRB0avwhk1OTBl"
      }
    }
"""

import json
import logging
import os
import sys
from typing import Any, Dict

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatMemberStatus
from telegram.error import BadRequest, Forbidden, TelegramError
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load environment variables (.env locally; Railway injects real env vars
# directly, so load_dotenv() is a harmless no-op there if no .env exists)
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Read and validate BOT_TOKEN
# ---------------------------------------------------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.critical(
        "BOT_TOKEN environment variable is not set. "
        "Set it locally in a .env file or in Railway's Variables tab."
    )
    # Exit immediately - there is no point starting the bot without a token.
    sys.exit(1)

# ---------------------------------------------------------------------------
# Path to the campaign configuration file (same directory as this script)
# ---------------------------------------------------------------------------
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def load_config(path: str) -> Dict[str, Any]:
    """
    Loads the campaign configuration from config.json exactly once at
    startup. Returns an empty dict (with a warning logged) if the file
    is missing or malformed, so the bot can still start and simply
    report "Invalid or expired link." for every deep link rather than
    crashing.
    """
    if not os.path.exists(path):
        logger.warning(
            "config.json not found at '%s'. The bot will start, but every "
            "deep link will be treated as invalid until the file is added.",
            path,
        )
        return {}

    try:
        with open(path, "r", encoding="utf-8") as config_file:
            data = json.load(config_file)
    except json.JSONDecodeError as exc:
        logger.error("config.json contains invalid JSON: %s", exc)
        return {}
    except OSError as exc:
        logger.error("Failed to read config.json: %s", exc)
        return {}

    if not isinstance(data, dict):
        logger.error("config.json must contain a top-level JSON object. Ignoring file.")
        return {}

    # Validate each campaign entry; skip (and warn about) malformed ones
    # instead of letting one bad entry break the whole config.
    validated: Dict[str, Any] = {}
    for key, value in data.items():
        if (
            isinstance(value, dict)
            and value.get("channel_username")
            and value.get("destination_link")
        ):
            validated[key] = value
        else:
            logger.warning(
                "Skipping campaign '%s': missing 'channel_username' or "
                "'destination_link'.",
                key,
            )

    logger.info("Loaded %d campaign(s) from config.json.", len(validated))
    return validated


# Config is loaded once at startup and kept in memory for the lifetime
# of the process. Restart the bot to pick up changes to config.json.
CAMPAIGNS: Dict[str, Any] = load_config(CONFIG_PATH)


# Chat member statuses that count as "is a member" for our purposes.
# Excludes LEFT and BANNED/KICKED.
MEMBER_STATUSES = {
    ChatMemberStatus.MEMBER,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.OWNER,
}


async def check_membership(
    context: ContextTypes.DEFAULT_TYPE, user_id: int, channel_username: str
) -> bool:
    """
    Checks whether a user is currently a member of channel_username.

    IMPORTANT: the bot must be an ADMINISTRATOR of the target channel for
    get_chat_member to succeed. If it isn't (or the channel is invalid),
    Telegram raises an error, which we catch and treat as "not a member"
    so the gateway fails safe instead of crashing.
    """
    try:
        member = await context.bot.get_chat_member(chat_id=channel_username, user_id=user_id)
        return member.status in MEMBER_STATUSES
    except Forbidden as exc:
        logger.error(
            "Forbidden checking membership in %s: %s. "
            "Make sure the bot is an ADMIN of this channel.",
            channel_username,
            exc,
        )
        return False
    except BadRequest as exc:
        logger.error("BadRequest checking membership in %s: %s", channel_username, exc)
        return False
    except TelegramError as exc:
        logger.error("Telegram error checking membership in %s: %s", channel_username, exc)
        return False


def build_gate_keyboard(channel_url: str, campaign_key: str) -> InlineKeyboardMarkup:
    """
    Builds the two-button keyboard shown on /start:
        1. Join Channel (url button)
        2. Continue (callback button - triggers a membership check)
    """
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(text="📢 Join Channel", url=channel_url)],
            [InlineKeyboardButton(text="➡️ Continue", callback_data=f"verify:{campaign_key}")],
        ]
    )


WELCOME_TEXT = (
    "👋 Welcome!\n\n"
    "Please join our channel first, then tap *Continue* to proceed."
)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /start command, including deep-link parameters such as
    /start jjk (sent by Telegram when a user opens
    https://t.me/YourBot?start=jjk).
    """
    message = update.message
    if message is None:
        return

    # context.args contains whatever follows "/start ", split by spaces.
    # e.g. "/start jjk" -> context.args == ["jjk"]
    args = context.args
    param = args[0].strip().lower() if args else None

    # No parameter, or parameter not found in our loaded config.
    if not param or param not in CAMPAIGNS:
        logger.info("Invalid or missing deep-link parameter: %r", param)
        await message.reply_text("Invalid or expired link.")
        return

    campaign = CAMPAIGNS[param]
    channel_username = campaign["channel_username"]

    # Build the URL for the "Join Channel" button. Telegram channel links
    # don't include the '@', so strip it if present.
    channel_url = f"https://t.me/{channel_username.lstrip('@')}"

    keyboard = build_gate_keyboard(channel_url, param)

    await message.reply_text(
        text=WELCOME_TEXT,
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


async def continue_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles taps on the "➡️ Continue" button.

    callback_data is "verify:<campaign_key>". We re-check membership in
    the required channel:
        - If the user has joined -> delete the gate message (it
          "vanishes") and send a NEW message with the destination link
          as a button.
        - If not -> re-send (forward again, as a new message, not an
          edit) the same welcome message with the same two buttons so
          they can try again.
    """
    query = update.callback_query
    user = update.effective_user

    # Acknowledge immediately so Telegram doesn't show a loading spinner.
    await query.answer()

    try:
        _, campaign_key = query.data.split(":", maxsplit=1)
    except (ValueError, AttributeError):
        logger.error("Malformed callback_data: %r", query.data)
        await query.answer(text="Something went wrong. Please use the link again.", show_alert=True)
        return

    campaign = CAMPAIGNS.get(campaign_key)
    if campaign is None:
        await context.bot.send_message(chat_id=user.id, text="Invalid or expired link.")
        return

    channel_username = campaign["channel_username"]
    destination_link = campaign["destination_link"]
    channel_url = f"https://t.me/{channel_username.lstrip('@')}"

    is_member = await check_membership(context, user.id, channel_username)

    if is_member:
        # User has joined - delete the gate message so it vanishes from
        # the chat, then send a new message with the destination link.
        try:
            await query.message.delete()
        except (BadRequest, Forbidden) as exc:
            # Not fatal - e.g. message already deleted, or too old to
            # delete. Log it and continue to deliver the destination link.
            logger.warning("Could not delete gate message for user %s: %s", user.id, exc)

        destination_keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="Download", url=destination_link)]]
        )
        await context.bot.send_message(
            chat_id=user.id,
            text="✅ Verification successful! Tap below to continue:",
            reply_markup=destination_keyboard,
        )
    else:
        # User hasn't joined yet - forward (re-send) the same welcome
        # message with the same two buttons, as a brand-new message.
        keyboard = build_gate_keyboard(channel_url, campaign_key)
        await context.bot.send_message(
            chat_id=user.id,
            text=WELCOME_TEXT,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )


async def unknown_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Catches any message that isn't recognized as a known command
    (registered as a fallback MessageHandler with filters.COMMAND).
    """
    message = update.message
    if message is None:
        return
    await message.reply_text("Unknown command. Please use a valid deep link to get started.")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Global error handler. Logs unhandled exceptions with traceback so
    they're visible in Railway's log viewer, without crashing the bot.
    """
    logger.error("Unhandled exception while processing update %s", update, exc_info=context.error)


def main() -> None:
    """
    Builds the Application, registers all handlers, and starts polling.
    """
    logger.info("Starting bot...")

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # /start (with or without a deep-link parameter)
    application.add_handler(CommandHandler("start", start_handler))

    # "Continue" button -> callback_data starts with "verify:"
    application.add_handler(CallbackQueryHandler(continue_callback, pattern=r"^verify:"))

    # Fallback for any other command the bot doesn't explicitly handle.
    # filters.COMMAND matches any message starting with "/".
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command_handler))

    # Global error handler for unhandled exceptions in any handler above.
    application.add_error_handler(error_handler)

    logger.info("Bot is running. Press Ctrl+C to stop.")

    # Long polling - no webhook server, no open port required. This is
    # exactly what's needed for a Railway "Worker" style deployment.
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
