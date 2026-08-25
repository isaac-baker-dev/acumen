"""
Acumen Telegram Bot
====================
Chat with Acumen from Telegram. Trigger pipelines. Get notifications.
"""

import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters
)
from acumen.core.config import TELEGRAM_BOT_TOKEN
from acumen.core.llm import get_llm
from acumen.memory import MemoryManager
from acumen.dags.pipeline import submit_pipeline
from acumen.core.logger import get_logger

logger = get_logger("acumen.interface.telegram")

async def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("Research", callback_data="pipe_research"),
         InlineKeyboardButton("Code", callback_data="pipe_coding")],
        [InlineKeyboardButton("Search KB", callback_data="search"),
         InlineKeyboardButton("Status", callback_data="status")],
    ]
    await update.message.reply_text(
        "Welcome to *Acumen* \u2014 your personal AI system.\n\n"
        "Send me any message to chat, or use the buttons below.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )

async def handle_message(update: Update, context):
    user_msg = update.message.text
    await update.message.reply_chat_action("typing")

    memory = MemoryManager()
    ctx = memory.get_task_context(user_msg)

    llm = get_llm("reasoning")
   prompt = (
        f"You are Acumen, a knowledgeable and friendly AI assistant on Telegram. "
        f"Keep responses short (2-3 paragraphs max) since this is a chat app.\n\n"
        f"RULES:\n"
        f"- Give direct answers first\n"
        f"- Be warm and conversational\n"
        f"- If you don't know, say so honestly\n\n"
        f"Context: {ctx[:500]}\n\n"
        f"User: {user_msg}\nRespond naturally as Acumen:"
    )
    response = llm.invoke(prompt)
    memory.save_episode("telegram_chat", user_msg[:500],
                        {"platform": "telegram"})
    await update.message.reply_text(response[:4000])

async def handle_callback(update: Update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "status":
        memory = MemoryManager()
        await query.edit_message_text(
            f"*Acumen Status*\n"
            f"Knowledge Base: {memory.knowledge_count()} documents\n"
            f"Memory: Active",
            parse_mode="Markdown")
    elif query.data == "search":
        await query.edit_message_text("Send me a search query:")
        context.user_data["mode"] = "search"
    elif query.data.startswith("pipe_"):
        pipe_type = query.data.replace("pipe_", "")
        await query.edit_message_text(
            f"Send me the topic/spec for the *{pipe_type}* pipeline:",
            parse_mode="Markdown")
        context.user_data["mode"] = f"pipeline_{pipe_type}"

async def handle_command_research(update: Update, context):
    topic = " ".join(context.args) if context.args else ""
    if not topic:
        await update.message.reply_text("Usage: /research <topic>")
        return
    await update.message.reply_text(f"Starting research on: {topic}")
    pid = submit_pipeline("research", [
        {"name":"research","agent":"research","payload":topic,
         "depends_on":[],"priority":1}])
    await update.message.reply_text(f"Pipeline submitted: {pid}")

async def handle_command_code(update: Update, context):
    spec = " ".join(context.args) if context.args else ""
    if not spec:
        await update.message.reply_text("Usage: /code <spec>")
        return
    await update.message.reply_text(f"Starting coding pipeline: {spec}")
    pid = submit_pipeline("coding", [
        {"name":"coding","agent":"coding","payload":spec,
         "depends_on":[],"priority":1}])
    await update.message.reply_text(f"Pipeline submitted: {pid}")

def run_telegram_bot():
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("No TELEGRAM_BOT_TOKEN set. Bot disabled.")
        return

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("research", handle_command_research))
    app.add_handler(CommandHandler("code", handle_command_code))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Telegram bot starting...")
    app.run_polling()

if __name__ == "__main__":
    run_telegram_bot()