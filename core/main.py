from datetime import datetime, timezone
import os
import time
import asyncio
import threading
from dotenv import load_dotenv
from loguru import logger
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

from memory import MemorySystem
from agent import CaioAgent
# from skills.scheduler import SchedulerSkill # Desativado: Agora é tudo Google
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

# Modelo de Visão (Gemini Pro Vision - Legacy Stable)
def get_vision_model():
    return ChatGoogleGenerativeAI(model="gemini-pro-vision", google_api_key=os.getenv("GOOGLE_API_KEY"))

# --- PROACTIVE INTELLIGENCE ---
class ProactiveMonitor:
    def __init__(self):
        self.alerted_events = set()
        self.last_email_ids = set()
        self.last_wellness_check = 0
        self.user_chat_id = "205798346" # ID do Gleisson (Hardcoded para MVP, ideal ser dinâmico)
    
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
        # Pega eventos próximos (próxima 1h)
        # GoogleSkill retorna texto, precisamos refazer ou parsear? 
        # Ideal: Melhorar GoogleSkill para ter método retorna objeto. 
        # Como hack, vou usar list_upcoming_events apenas para logar por enquanto, 
        # mas para alertar *direito* precisaria da lista crua.
        # VOU MELHORAR O GOOGLESKILL DEPOIS PARA RETORNAR OBJETOS PUBLICAMENTE.
        # Por enquanto, vou pular a implementação complexa de calendário aqui para não quebrar o código anterior
        # e focar no clima/email que é mais fácil de isolar.
        pass

    async def check_emails(self, bot):
        unread = google_skills.get_unread_emails(max_results=3)
        current_ids = {e['id'] for e in unread}
        
        # Identificar novos
        new_ids = current_ids - self.last_email_ids
        
        if new_ids and self.last_email_ids: # Só avisa se já tinha estado inicial (para não floodar no start)
            for e in unread:
                if e['id'] in new_ids:
                    sender = e.get('sender').split('<')[0].strip().replace('"', '')
                    msg = f"🔔 **Novo Email de {sender}**\n`{e.get('subject')}`\n\n_Quer que eu leia ou responda?_"
                    await bot.send_message(chat_id=self.user_chat_id, text=msg)
        
        self.last_email_ids = current_ids

    async def check_wellness(self, bot):
        # Clima (Agora usa a cidade da memória)
        user_city = brain_memory.get_preference("city")
        if not user_city: return # Não sabe a cidade ainda
        
        temp = weather_skill.get_temperature_int(user_city)
        if temp and temp > 28:
            name = brain_memory.get_preference("name", "Gleisson")
            msg = f"🥵 Uffa! Faz **{temp}°C** agora em {user_city}.\nLembre-se de beber água, {name}! 💧"
            await bot.send_message(chat_id=self.user_chat_id, text=msg)

monitor = ProactiveMonitor()

async def post_init(application):
    """Gatilho pós-inicialização para rodar loops de fundo."""
    asyncio.create_task(monitor.loop(application.bot))

# --- LÓGICA DO TELEGRAM ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Atualiza ID do usuário para o monitor proativo
    monitor.user_chat_id = update.effective_chat.id
    name = brain_memory.get_preference("name", "Gleisson")
    await update.message.reply_text(f"Olá {name}! Sou {AGENT_NAME}. Agente 100% Google & Proativo.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.effective_user.id
    monitor.user_chat_id = update.effective_chat.id # Garante que temos o ID certo
    
    logger.info(f"📩 Msg de {user_id}: {user_text}")

    # 1. Memória Instantânea
    brain_memory.store(user_text, source="telegram", importance=1)
    
    # Check de Cidade (Se não souber, pergunta)
    user_city = brain_memory.get_preference("city")
    if not user_city and len(user_text.split()) < 10 and "sou de" not in user_text.lower() and "moro em" not in user_text.lower():
         # Se a msg for curta e não for resposta sobre cidade
         # Podemos injetar uma pergunta proativa, mas cuidado para não interroper comandos.
         # Por enquanto, deixamos o LLM decidir 'config_update' se o usuario falar.
         pass

    # 2. Verificar Intenção (Via LLM)
    intent = caio_persona.detect_intent(user_text)
    action = intent.get("action")
    
    response_text = ""
    
    if action == "config_update":
        # === ATUALIZAÇÃO DE PERFIL ===
        key = intent.get("key")
        value = intent.get("value")
        brain_memory.set_preference(key, value)
        response_text = f"📝 Anotado! Atualizei seu {key} para: {value}."

    elif action == "google_calendar_add":
        # === GOOGLE CALENDAR (ADD) ===
        summary = intent.get("summary")
        start_time = intent.get("start_time")
        end_time = intent.get("end_time")
        desc = intent.get("description", "")
        
        success, msg = google_skills.create_event(summary, start_time, end_time, desc)
        
        if success:
             response_text = caio_persona.generate_confirmation(user_text, {
                "description": summary, 
                "scheduled_at": start_time,
                "extra_info": msg 
            })
        else:
            response_text = f"Tive um problema com o Google Agenda: {msg}"

    elif action == "google_calendar_list":
        # === GOOGLE CALENDAR (LIST) ===
        response_text = google_skills.list_upcoming_events()

    elif action == "google_calendar_delete":
        # === GOOGLE CALENDAR (DELETE - SMART) ===
        target_desc = intent.get("target_description")
        found_events = google_skills.find_event(target_desc)
        
        if not found_events:
            response_text = f"🤔 Não encontrei nenhum evento futuro contendo '{target_desc}'."
        elif len(found_events) == 1:
            evt = found_events[0]
            success, msg = google_skills.delete_event(evt['id'])
            if success:
                 response_text = f"🗑️ Feito! O evento '{evt['summary']}' foi cancelado da sua agenda."
            else:
                 response_text = f"❌ Erro ao cancelar: {msg}"
        else:
            response_text = f"⚠️ Encontrei {len(found_events)} eventos parecidos. Qual deles quer cancelar?\n"
            for evt in found_events:
                start = evt['start'].get('dateTime', evt['start'].get('date'))
                response_text += f"- {evt['summary']} ({start})\n"
            response_text += "\n(Por favor, seja mais específico, ex: 'cancelar dentista terça-feira')"

    elif action == "email_send":
        # === GMAIL (SEND) ===
        to = intent.get("to")
        subject = intent.get("subject")
        body = intent.get("body")
        if not to:
             response_text = "📧 Para quem devo enviar o email?"
        else:
             success, msg = google_skills.send_email(to, subject, body)
             if success:
                response_text = caio_persona.generate_confirmation(user_text, {
                    "description": f"Email para {to}", 
                    "scheduled_at": "agora mesmo",
                    "extra_info": "Enviado com sucesso!"
                })
             else:
                response_text = f"Erro ao enviar email: {msg}"

    elif action == "email_check":
        # === GMAIL (READ/CHECK) ===
        query = intent.get("query", "is:unread")
        if "unread" in query:
             emails = google_skills.get_unread_emails()
             title = "📬 Caixa de Entrada - E-mails não lidos"
        else:
             emails = google_skills.search_emails(query)
             title = f"🔍 Resultados para: {query}"
        
        if not emails:
            response_text = "✨ Tudo limpo! Não encontrei novos emails por aqui."
        else:
            response_text = f"{title}\n\n"
            for e in emails:
                sender = e.get('sender', 'Desconhecido')
                if '<' in sender: sender = sender.split('<')[0].strip().replace('"', '')
                subject = e.get('subject', '(Sem Assunto)')
                snippet = e.get('snippet', '')
                if len(snippet) > 100: snippet = snippet[:100] + "..."
                response_text += f"Remetente: {sender}\nAssunto: {subject}\nResumo: {snippet}\n\n"
    
    elif action == "email_delete":
        # === GMAIL (DELETE - ULTRA SMART) ===
        target_desc = intent.get("target_description")
        found_emails = google_skills.search_emails(target_desc)
        
        if not found_emails:
            response_text = f"🤔 Não encontrei nenhum email com o termo '{target_desc}'."
        else:
            candidates = [{'id': e['id'], 'description': f"Assunto: {e['subject']}"} for e in found_emails]
            
            selected_id = "NONE"
            if len(found_emails) == 1: selected_id = found_emails[0]['id']
            else: selected_id = caio_persona.resolve_ambiguity(user_text, candidates)
            
            if selected_id == "ALL":
                count = 0
                for e in found_emails:
                    google_skills.delete_email(e['id'])
                    count += 1
                response_text = f"🗑️ Feito! Apaguei todos os {count} emails encontrados."
            elif selected_id != "NONE":
                target_email = next((e for e in found_emails if e['id'] == selected_id), None)
                if target_email:
                    google_skills.delete_email(selected_id)
                    response_text = f"🗑️ Apagado: {target_email['subject']}"
                else:
                    response_text = "❌ Erro interno: ID selecionado não encontrado."
            else:
                response_text = f"⚠️ Encontrei {len(found_emails)} emails semelhantes. Qual deles?\n\n"
                for idx, e in enumerate(found_emails, 1):
                    clean_subject = e.get('subject', 'Sem Assunto').replace('*', '').replace('_', '')
                    response_text += f"[{idx}] {clean_subject}\n"
                response_text += "\nPor favor, seja mais específico (ex: 'apagar o primeiro' ou 'apagar todos')."

    elif action == "calculate":
        code = intent.get("code")
        result = caio_persona.execute_code(code)
        response_text = f"🔢 Calculei aqui:\n```\n{result}\n```"

    elif action == "web_search":
        # === BUSCA NA WEB ===
        query = intent.get("query")
        results = web_skill.search(query)
        
        if not results:
            response_text = f"🤔 Pesquisei por '{query}', mas não encontrei nada relevante."
        else:
            search_context = [{"content": f"RESULTADO DA BUSCA WEB para '{query}':\n" + "\n".join(results)}]
            response_text = caio_persona.generate_message(
                f"Baseado na pesquisa sobre '{query}', o que você descobriu?", 
                search_context
            )

    elif action == "filesystem_op":
        # === SISTEMA DE ARQUIVOS (MÃOS) ===
        op = intent.get("operation")
        path = intent.get("path", ".")
        
        if op == "list":
             res = fs_skill.list_files(path)
             response_text = f"📂 **Arquivos em '{path}':**\n```\n{res}\n```"
        elif op == "create_folder":
             res = fs_skill.create_folder(path)
             response_text = res
        elif op == "read":
             res = fs_skill.read_file_preview(path)
             response_text = f"📄 **Preview de '{path}':**\n```\n{res}\n```"
        else:
             response_text = "⚠️ Operação de arquivo desconhecida."

    else:
        # === CHAT (FALLBACK) ===
        # Verificar se está faltando algo critico
        if not user_city and "bom dia" in user_text.lower():
             response_text = "Bom dia! 🌞 Antes de começarmos, de qual **cidade** você fala? (Assim posso ver o clima pra você)."
        else:
             context_data = brain_memory.recall(user_text)
             # Injeta preferência de nome no contexto se houver
             name = brain_memory.get_preference("name")
             if name: context_data.append({"content": f"O usuário se chama {name}."})
             response_text = caio_persona.generate_message(user_text, context_data)

    # 3. Responder
    await update.message.reply_text(response_text)
    
    # 4. Salvar Resposta
    brain_memory.store(response_text, source="caio_response", importance=0.5)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Olhos do Caio: Analisa imagens enviadas via Telegram."""
    user = update.effective_user
    photo_file = await update.message.photo[-1].get_file()
    
    logger.info(f"📸 Recebi uma foto de {user.first_name}. Baixando...")
    
    # Baixa imagem em memória
    from io import BytesIO
    import base64
    
    img_buffer = BytesIO()
    await photo_file.download_to_memory(img_buffer)
    img_buffer.seek(0)
    
    # Codifica para Base64
    img_b64 = base64.b64encode(img_buffer.read()).decode("utf-8")
    
    # Aviso de processamento
    await update.message.reply_text("👀 Analisando imagem...")
    
    try:
        vision_llm = get_vision_model()
        # Prompt multimodal
        message = HumanMessage(
            content=[
                {"type": "text", "text": "Descreva esta imagem com detalhes. Se for um erro de computador, leia o texto. Se for um documento, resuma."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
            ]
        )
        response = vision_llm.invoke([message])
        description = response.content
        
        logger.success(f"👁️ Visão: {description[:50]}...")
        
        # Salva na memória
        user_text = f"[USUÁRIO ENVIOU UMA FOTO]: {description}"
        brain_memory.store(user_text, source="vision", importance=2)
        
        # Gera resposta do Caio
        context_data = brain_memory.recall("foto imagem visual") 
        caio_response = caio_persona.generate_message(f"O usuário mandou uma foto. O que eu vejo é: {description}. Comente sobre isso ou ajude.", context_data)
        
        await update.message.reply_text(caio_response)
        brain_memory.store(caio_response, source="caio_response", importance=0.5)
        
    except Exception as e:
        logger.error(f"Erro na visão: {e}")
        await update.message.reply_text(f"😵 Tive um problema para processar essa imagem: {e}")

if __name__ == "__main__":
    logger.info(f"🚀 Iniciando Sistema {AGENT_NAME} (Vision + Proactive + Web)...")
    
    # Iniciar Bot Telegram
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo)) # <--- OLHOS ATIVADOS
    
    logger.success("👂 Bot ouvindo! Pressione Ctrl+C para sair.")
    app.run_polling()
