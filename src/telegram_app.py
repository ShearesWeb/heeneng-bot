import json
import logging
import os
import random
from io import BytesIO
from pathlib import Path

import boto3
from telegram import InputFile, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

LOG = logging.getLogger(__name__)

SRC_DIR = Path(__file__).resolve().parent
RESPONSES_PATH = SRC_DIR / "responses.json"
RESPONSES = {"text_rules": [], "image_rules": []}
S3_BUCKET = os.getenv("IMAGES_BUCKET_NAME")
S3_CLIENT = boto3.client("s3") if S3_BUCKET else None


def load_responses() -> None:
    global RESPONSES
    if RESPONSES_PATH.exists():
        with RESPONSES_PATH.open("r", encoding="utf-8") as f:
            RESPONSES = json.load(f)
    else:
        LOG.warning("responses.json not found; text/image replies disabled")


def _get_s3_key(path_str: str) -> str:
    return path_str.lstrip("/")


def _fetch_s3_image(key: str) -> BytesIO | None:
    if not S3_CLIENT or not S3_BUCKET:
        return None

    try:
        response = S3_CLIENT.get_object(Bucket=S3_BUCKET, Key=key)
        body = response["Body"].read()
        return BytesIO(body)
    except Exception as exc:
        LOG.warning("Failed to fetch s3://%s/%s: %s", S3_BUCKET, key, exc)
        return None


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message or not message.text:
        return

    LOG.info("user_id=%s", update.effective_user.id if update.effective_user else None)

    text = message.text.strip().lower()

    for rule in RESPONSES.get("image_rules", []):
        any_keys = [k.lower() for k in rule.get("any", [])]
        all_keys = [k.lower() for k in rule.get("all", [])]
        if any_keys and not any(k in text for k in any_keys):
            continue
        if all_keys and not all(k in text for k in all_keys):
            continue

        image_path = rule.get("image")
        if image_path:
            key = _get_s3_key(image_path)
            image_bytes = _fetch_s3_image(key)
            if image_bytes:
                image_bytes.name = Path(key).name
                await message.reply_photo(photo=InputFile(image_bytes))
            else:
                await message.reply_text(f"{Path(key).name} not found on server", parse_mode=None)
            return

    for rule in RESPONSES.get("text_rules", []):
        any_keys = [k.lower() for k in rule.get("any", [])]
        all_keys = [k.lower() for k in rule.get("all", [])]
        if any_keys and not any(k in text for k in any_keys):
            continue
        if all_keys and not all(k in text for k in all_keys):
            continue

        reply = rule.get("reply")
        if reply:
            await message.reply_text(reply, parse_mode=None)
            return


async def handle_sticker_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message:
        return
    LOG.info("Handling /sticker for chat_id=%s", message.chat_id)

    sticker_id = random.choice(RESPONSES.get("sticker_ids", []))
    await message.reply_sticker(sticker=sticker_id)


def get_bot_token() -> str:
    bot_token = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise RuntimeError("Missing required environment variable: BOT_TOKEN")
    return bot_token


def build_application(bot_token: str):
    load_responses()
    application = ApplicationBuilder().token(bot_token).build()
    application.add_handler(CommandHandler("sticker", handle_sticker_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    return application
