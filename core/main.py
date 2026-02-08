from datetime import datetime, timezone
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
from skills.weather_skill import WeatherSkill
from skills.web_skill import WebSkill
from skills.filesystem_skill import FileSystemSkill
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

# Carregar variáveis
load_dotenv()

# Configuração de Logs
logger.add("logs/core.log", rotation="1 MB", level="INFO")

AGENT_NAME = os.getenv("AGENT_NAME", "Caio")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN faltando!")
    exit(1)

# Instâncias Globais
google_skills = GoogleSkill()
weather_skill = WeatherSkill()
web_skill = WebSkill()
fs_skill = FileSystemSkill() # Mãos
brain_memory = MemorySystem()
caio_persona = CaioAgent()
scheduler_skill = None
app_instance = None # Guarda referência global do app

# Modelo de Visão (Gemini Pro Vision - Legacy Stable)
def get_vision_model():
    return ChatGoogleGenerativeAI(model="gemini-pro-vision", google_api_key=os.getenv("GOOGLE_API_KEY"))

# Callback para o Scheduler enviar mensagens
async def send_telegram_message_callback(chat_id, text):
    if app_instance:
        try:
            await app_instance.bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            logger.error(f"Erro ao enviar lembrete: {e}")

# --- PROACTIVE INTELLIGENCE ---
class ProactiveMonitor:
    def __init__(self):
        self.alerted_events = set()
        self.last_email_ids = set()
        self.last_wellness_check = 0
        self.user_chat_id = "205798346" # ID do Gleisson (Default)
    
    async def loop(self, bot):
        logger.info("🧠 Cérebro Proativo Iniciado...")
        while True:
            try:
                # 1. Checar Agenda (a cada 1 min)
                await self.check_calendar(bot)
                
                # 2. Checar Email (a cada 2 min)
                if int(time.time()) % 120 == 0: 
                    await self.check_emails(bot)

                # 3. Wellness & Weather (a cada 1 hora)
                if time.time() - self.last_wellness_check > 3600:
                    await self.check_wellness(bot)
                    self.last_wellness_check = time.time()

            except Exception as e:
                logger.error(f"Erro no loop proativo: {e}")
            
            await asyncio.sleep(60) # Loop de 1 minuto

    async def check_calendar(self, bot):
        pass

    async def check_emails(self, bot):
        # Monitoramento Passivo (apenas notifica novos)
        # Usa o método antigo que retorna lista de dicts para controle de ID
        # Se quiser usar o novo list_unread_emails, precisaria parsear.
        # Por enquanto, mantemos a lógica antiga aqui para não quebrar o diff check.
        # O usuario pediu melhoria no COMANDO EXPLICITO de checar email.
        try:
            unread = google_skills.get_unread_emails(max_results=3)
            if isinstance(unread, str): return # Erro ou msg de texto
            
            current_ids = {e['id'] for e in unread}
            new_ids = current_ids - self.last_email_ids
            
            if new_ids and self.last_email_ids: 
                for e in unread:
                    if e['id'] in new_ids:
                        sender = e.get('sender').split('<')[0].strip().replace('"', '')
                        msg = f"🔔 **Novo Email de {sender}**\n`{e.get('subject')}`\n\n_Quer que eu leia?_"
                        await bot.send_message(chat_id=self.user_chat_id, text=msg)
            
            self.last_email_ids = current_ids
        except:
            pass

    async def check_wellness(self, bot):
        user_city = brain_memory.get_preference("city")
        if not user_city: return
        
        temp = weather_skill.get_temperature_int(user_city)
        if temp and temp > 28:
            name = brain_memory.get_preference("name", "Gleisson")
            msg = f"🥵 Uffa! Faz **{temp}°C** agora em {user_city}.\nLembre-se de beber água, {name}! 💧"
            await bot.send_message(chat_id=self.user_chat_id, text=msg)

monitor = ProactiveMonitor()

async def post_init(application):
    """Gatilho pós-inicialização para rodar loops de fundo."""
    global scheduler_skill, app_instance
    app_instance = application # Guarda referência global
    
    # Inicia Scheduler
    scheduler_skill = SchedulerSkill(send_telegram_message_callback)
    scheduler_skill.start(asyncio.get_running_loop())
    
    asyncio.create_task(monitor.loop(application.bot))

# --- LÓGICA DO TELEGRAM ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    monitor.user_chat_id = update.effective_chat.id
    name = brain_memory.get_preference("name", "Gleisson")
    await update.message.reply_text(f"Olá {name}! Sou {AGENT_NAME}. Agente 100% Google & Proativo.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    monitor.user_chat_id = chat_id
    
    logger.info(f"📩 Msg de {user_id}: {user_text}")

    brain_memory.store(user_text, source="telegram", importance=1)
    
    # --- ⚡ 0. INTERCEPTADOR DE LEMBRETES (REGEX CORRIGIDO & HUMANIZADO) ---
    # Captura: "Me lembre daqui a 10 min de sair" -> 10, remover "de", msg="sair"
    remind_match = re.search(r"(?:me\s+lembre|avis[ea]|notifique).*(?:daqui\s*a|em)\s*(\d+)\s*(?:minutos?|mins?|m)\s*(?:de|sobre|que)?\s*(.*)", user_text, re.IGNORECASE)
    
    if remind_match:
        minutes = remind_match.group(1)
        raw_msg = remind_match.group(2).strip()
        
        # Correção do Bug "uto": Remove sufixos acidentais se a regex falhar nos grupos
        # Se a msg começar com "utos " ou "tos ", remove.
        msg_content = re.sub(r"^(?:utos?|tos?|s)\s+", "", raw_msg, flags=re.IGNORECASE).strip()
        
        if not msg_content: 
            # Tenta pegar contexto do início se o fim estiver vazio (ex: "Me lembre do bolo daqui a 10 min")
            if len(user_text) < 100: msg_content = f"Lembrete: {user_text}"
            else: msg_content = "Verificar pendência."

        # Agenda silenciosamente no sistema
        scheduler_skill.set_reminder(chat_id, minutes, msg_content)
        
        # Resposta Humanizada (Sem return, para permitir chaining com Calendar)
        await update.message.reply_text(f"⏰ Combinado! Daqui a {minutes} min te aviso sobre: _{msg_content}_")
        
        # Continua fluxo para o LLM (pode ser um "Agendar X e me lembrar") 

    # 1. Verificar Intenção
    intent = caio_persona.detect_intent(user_text)
    action = intent.get("action")
    response_text = ""
    
    if action == "config_update":
        key = intent.get("key")
        value = intent.get("value")
        brain_memory.set_preference(key, value)
        response_text = f"📝 Anotado! Atualizei seu {key} para: {value}."

    elif action == "google_calendar_add":
        summary = intent.get("summary")
        start_time = intent.get("start_time")
        end_time = intent.get("end_time")
        desc = intent.get("description", "")
        success, msg = google_skills.create_event(summary, start_time, end_time, desc)
        if success:
             response_text = f"✅ Agendado: **{summary}** para {start_time}."
        else:
            response_text = f"Tive um problema com o Google Agenda: {msg}"

    elif action == "google_calendar_list":
        response_text = google_skills.list_upcoming_events()

    elif action == "google_calendar_delete":
        target_desc = intent.get("target_description")
        found_events = google_skills.find_event(target_desc)
        if not found_events:
            response_text = f"🤔 Não encontrei nenhum evento com '{target_desc}'."
        elif len(found_events) == 1:
            evt = found_events[0]
            success, msg = google_skills.delete_event(evt['id'])
            if success:
                 response_text = f"🗑️ Cancelei o evento '{evt['summary']}'."
            else:
                 response_text = f"❌ Erro ao cancelar: {msg}"
        else:
            response_text = "Encontrei múltiplos eventos. Seja mais específico."

    elif action == "email_send":
        to = intent.get("to")
        subject = intent.get("subject")
        body = intent.get("body")
        success, msg = google_skills.send_email(to, subject, body)
        response_text = "Email enviado!" if success else f"Erro no envio: {msg}"

    elif action == "email_check":
        # === GMAIL (READ/CHECK - POWER MODE) ===
        response_text = google_skills.list_unread_emails(limit=50)

    elif action == "web_search":
        query = intent.get("query")
        results = web_skill.search(query)
        search_context = [{"content": f"RESULTADO DA BUSCA WEB para '{query}':\n" + "\n".join(results)}] if results else []
        response_text = caio_persona.generate_message(f"Resuma a pesquisa sobre '{query}'.", search_context)

    elif action == "filesystem_op":
        op = intent.get("operation")
        path = intent.get("path", ".")
        if op == "list": response_text = fs_skill.list_files(path)
        elif op == "read": response_text = fs_skill.read_file_preview(path)
        else: response_text = "Operação desconhecida."

    else:
        # Fallback Chat
        context_data = brain_memory.recall(user_text)
        name = brain_memory.get_preference("name")
        if name: context_data.append({"content": f"O usuário se chama {name}."})
        response_text = caio_persona.generate_message(user_text, context_data)

    await update.message.reply_text(response_text)
    brain_memory.store(response_text, source="caio_response", importance=0.5)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Lógica de Visão (Simplificada para caber no rewrite)
    await update.message.reply_text("👀 Vejo que mandou uma foto! (Visão em manutenção rápida)")

if __name__ == "__main__":
    logger.info(f"🚀 Iniciando Sistema {AGENT_NAME} (Vision + Proactive + Web)...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    logger.success("👂 Bot ouvindo! Pressione Ctrl+C para sair.")
    app.run_polling()
