from datetime import datetime, timezone, timedelta
import os
import time
import asyncio
import re
from dotenv import load_dotenv
from loguru import logger
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

from memory import MemorySystem
from agent import CaioAgent
from skills.scheduler_skill import SchedulerSkill
from skills.google_skill import GoogleSkill
from skills.google_drive_skill import GoogleDriveSkill
from skills.brave_search_skill import BraveSearchSkill
from skills.document_processor_skill import DocumentProcessorSkill
from skills.weather_skill import WeatherSkill
from skills.web_skill import WebSkill
from skills.filesystem_skill import FileSystemSkill

load_dotenv()
logger.add("logs/core.log", rotation="1 MB", level="INFO")

AGENT_NAME = os.getenv("AGENT_NAME", "Caio")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Instâncias Globais
google_skills = GoogleSkill()
drive_skill = GoogleDriveSkill(google_skills)
brave_skill = BraveSearchSkill()
doc_skill = DocumentProcessorSkill()
weather_skill = WeatherSkill()
web_skill = WebSkill()
fs_skill = FileSystemSkill()
brain_memory = MemorySystem()
caio_persona = CaioAgent()
scheduler_skill = None
app_instance = None

async def send_telegram_message_callback(chat_id, text):
    if app_instance:
        try:
            await app_instance.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Erro ao enviar lembrete: {e}")

class ProactiveMonitor:
    def __init__(self):
        self.user_chat_id = "205798346" # Default
        self.alerted_events = set()

    async def loop(self, bot):
        logger.info("🧠 Cérebro Proativo Iniciado...")
        while True:
            await asyncio.sleep(60)
            if not self.user_chat_id: continue
            try:
                events = google_skills.get_upcoming_raw()
                now = datetime.now(timezone.utc)
                for evt in events:
                    start_str = evt['start'].get('dateTime')
                    if not start_str: continue
                    start_dt = datetime.fromisoformat(start_str)
                    diff = (start_dt - now).total_seconds() / 60
                    if 10 <= diff <= 15:
                        evt_id = evt['id']
                        if evt_id not in self.alerted_events:
                            summary = evt.get('summary', 'Evento')
                            msg = f"🦁 *Lembrete Proativo*: '{summary}' começa em 15 minutos!"
                            await bot.send_message(chat_id=self.user_chat_id, text=msg, parse_mode="Markdown")
                            self.alerted_events.add(evt_id)
            except Exception as e:
                logger.error(f"Erro no Monitor: {e}")

monitor = ProactiveMonitor()

async def post_init(application):
    global scheduler_skill, app_instance
    app_instance = application
    scheduler_skill = SchedulerSkill(send_telegram_message_callback)
    scheduler_skill.start(asyncio.get_running_loop())
    asyncio.create_task(monitor.loop(application.bot))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.effective_chat.id
    monitor.user_chat_id = chat_id
    
    logger.info(f"📩 Msg: {user_text}")
    brain_memory.store(user_text, source="telegram")

    # 1. Detectar Intenções (Múltiplas)
    intents = caio_persona.detect_intent(user_text)
    
    for intent in intents:
        action = intent.get("action")
        response_text = ""

        if action == "reminder_set":
            response_text = scheduler_skill.set_reminder(chat_id, intent.get("minutes"), intent.get("message"))
        
        elif action == "google_calendar_add":
            success, msg = google_skills.create_event(intent.get("summary"), intent.get("start_time"), intent.get("end_time"), intent.get("description", ""))
            response_text = f"✅ {msg}" if success else f"❌ Erro: {msg}"

        elif action == "brave_search":
            results = brave_skill.search(intent.get("query"))
            if results:
                response_text = caio_persona.generate_message(f"Resuma: {results}", [])
            else:
                response_text = "🌐 Não encontrei resultados recentes."

        elif action == "google_drive_upload":
            success, link = drive_skill.upload_file(intent.get("file_path"))
            response_text = f"📁 Arquivo no Drive: {link}" if success else f"❌ Erro Drive: {link}"

        elif action == "document_process":
            content = doc_skill.process(intent.get("path"))
            response_text = caio_persona.generate_message(f"Analise este documento: {content[:2000]}", [])

        elif action == "chat":
            context_data = brain_memory.recall(user_text)
            response_text = caio_persona.generate_message(user_text, context_data)

        if response_text:
            await update.message.reply_text(response_text, parse_mode="Markdown")
            brain_memory.store(response_text, source="caio_response")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
