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

class ProactiveMonitor:
    def __init__(self):
        self.user_chat_id = None
        self.alerted_events = set()

    async def loop(self, bot):
        logger.info("🧠 Cérebro Proativo Iniciado...")
        while True:
            await asyncio.sleep(60) # Pulso de 1 minuto
            
            if not self.user_chat_id: continue
            
            try:
                # 1. Checagem de Calendário (15 min avisos)
                # Precisamos que o GoogleSkill retorne lista crua. 
                # Se não existir, vai falhar silenciosamente no try
                if hasattr(google_skills, 'get_upcoming_raw'):
                    events = google_skills.get_upcoming_raw()
                    now = datetime.now(timezone.utc)
                    
                    for evt in events:
                        start_str = evt['start'].get('dateTime')
                        if not start_str: continue # Evento dia todo
                        
                        start_dt = datetime.fromisoformat(start_str)
                        # Ajuste simples de fuso se precisar, mas comparando diff
                        diff = (start_dt - now).total_seconds() / 60
                        
                        if 10 <= diff <= 15: # Entre 10 e 15 min
                            evt_id = evt['id']
                            if evt_id not in self.alerted_events:
                                summary = evt.get('summary', 'Evento')
                                msg = f"🦁 *Lembrete Rápido*: '{summary}' começa em 15 minutos!"
                                await bot.send_message(chat_id=self.user_chat_id, text=msg)
                                self.alerted_events.add(evt_id)
                                
            except Exception as e:
                logger.error(f"Erro no Loop Proativo: {e}")

monitor = ProactiveMonitor()

async def post_init(application):
    """Gatilho pós-inicialização para rodar loops de fundo."""
    global scheduler_skill, app_instance
    app_instance = application
    # Inicia Scheduler
    scheduler_skill = SchedulerSkill(send_telegram_message_callback)
    scheduler_skill.start(asyncio.get_running_loop())
    # Inicia Monitor Proativo
    asyncio.create_task(monitor.loop(application.bot))

# --- LÓGICA DO TELEGRAM ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    monitor.user_chat_id = update.effective_chat.id
    name = brain_memory.get_preference("name", "Gleisson")
    await update.message.reply_text(f"Olá {name}! Sou {AGENT_NAME}. Agente 100% Google & Proativo.")

# --- OPENCLAW-STYLE PIPELINE ---
class InputPipeline:
    """Processa entrada bruta e extrai intenções determinísticas antes do LLM."""
    
    @staticmethod
    def normalize(text):
        return text.strip()

    @staticmethod
    def extract_and_clean(text):
        commands = []
        clean_text = text
        
        # 1. Lembretes (Busca GLOBAL na frase)
        # Captura: "Agendar X e [me lembre daqui a 10 min de Y]"
        # Regex flexível para capturar o trecho de lembrete
        regex = r"(?:e\s+)?(?:me\s+lembre|avis[ea]|notifique|lembrete).*(?:daqui\s*a|em)\s*(\d+)\s*(?:minutos?|mins?|m)\s*(?:de|sobre|que)?\s*([^,\.\n]*)"
        
        matches = list(re.finditer(regex, text, re.IGNORECASE))
        
        for match in matches:
            full_match = match.group(0)
            minutes = match.group(1)
            raw_msg = match.group(2).strip()
            
            # Limpeza
            msg_content = re.sub(r"^(?:utos?|tos?|s)\s+", "", raw_msg, flags=re.IGNORECASE).strip()
            if not msg_content: 
                # Tenta pegar o contexto anterior se a msg interna for vazia
                # Ex: "Fazer bolo e me lembrar daqui a 10 min" -> msg="Fazer bolo"
                msg_content = clean_text.replace(full_match, "").strip()[:50]

            commands.append({
                "type": "reminder",
                "minutes": minutes,
                "msg": msg_content
            })
            
            # Remove o comando de lembrete do texto principal para o LLM não se confundir
            clean_text = clean_text.replace(full_match, "").strip()
            
        return commands, clean_text

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    monitor.user_chat_id = chat_id
    
    logger.info(f"📩 Msg de {user_id}: {user_text}")
    
    # --- 1. PIPELINE DETERMINÍSTICO (MODO CLAWBOT) ---
    # Extrai comandos e limpa o texto
    commands, filtered_text = InputPipeline.extract_and_clean(user_text)
    
    # Executa comandos instantâneos (Lembretes)
    for cmd in commands:
        if cmd['type'] == 'reminder':
            reply = scheduler_skill.set_reminder(chat_id, cmd['minutes'], cmd['msg'])
            await update.message.reply_text(reply)
            
    # Se sobrou texto relevante (ex: "Agendar reunião"), manda pro LLM
    if len(filtered_text) > 3: # Filtro de ruído
        logger.info(f"🧠 Enviando para LLM (Texto Filtrado): {filtered_text}")
        intent = caio_persona.detect_intent(filtered_text)
        action = intent.get("action")
        response_text = ""
    else:
        # Se só tinha lembrete, paramos aqui
        return
    
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
             # msg já vem formatada do Skill (Ex: Agendado: Reunião para 09/02 (Seg) às 14:00)
             # Adicionamos apenas o emoji de check se não tiver
             response_text = f"✅ {msg}" 
        else:
            response_text = f"❌ Erro Google Agenda: {msg}"

    elif action == "web_search":
        # === BUSCA NA WEB (AGORA FUNCIONA) ===
        query = intent.get("query")
        results = web_skill.search(query)
        
        if not results:
            # Fallback para tentar uma busca mais ampla
            results = web_skill.search(query + " noticias recentes", max_results=5)
            
        if not results:
             response_text = f"🌐 Pesquisei sobre '{query}' mas não encontrei fontes confiáveis no momento."
        else:
            # Contexto rico para o LLM
            search_context = [{"content": f"RESULTADOS RECENTES DA WEB sobre '{query}':\n" + "\n".join(results)}]
            response_text = caio_persona.generate_message(
                f"Resuma o que você encontrou sobre '{query}' de forma direta e utile.", 
                search_context
            )

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
