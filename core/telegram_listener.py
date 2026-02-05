import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from loguru import logger
import os
from dotenv import load_dotenv
from agent import CaioAgent
from memory import MemorySystem
import dateparser
from datetime import datetime
from supabase import create_client

# Carregar variáveis
load_dotenv(dotenv_path="../.env")

# Configuração
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Inicializa Sistemas
caio = CaioAgent()
memory = MemorySystem()
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Olá! Sou o Caio. Como posso ajudar?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.effective_chat.id
    logger.info(f"📩 Mensagem recebida de {user_id}: {user_text}")

    # 1. Salvar Memória (User)
    memory.store(user_text, source="telegram_user", importance=1)

    # 2. Recuperar Contexto
    context_memories = memory.recall(user_text)

    # 3. Analisar Intenção (Simplificada via Regex/Keywords por enquanto, depois LLM)
    # Procurar por intenção de agendamento: "lembre-me", "agendar", "marcar"
    lower_text = user_text.lower()
    if any(keyword in lower_text for keyword in ["lembre", "agendar", "marcar", "reunião"]):
        # Tentar extrair data
        dt = dateparser.parse(user_text, settings={'PREFER_DATES_FROM': 'future', 'DATE_ORDER': 'DMY'})
        
        if dt:
            # Agendar
            # Se a data for no passado, assumir amanhã (ajuste básico)
            if dt < datetime.now():
                 dt = dateparser.parse("amanhã " + user_text, settings={'PREFER_DATES_FROM': 'future'})

            description = user_text # Pode melhorar removendo a data do texto
            
            try:
                supabase.table("scheduled_tasks").insert({
                    "description": description,
                    "scheduled_at": dt.isoformat(),
                    "status": "pending"
                }).execute()
                
                response_text = f"✅ Agendado: '{description}' para {dt.strftime('%d/%m às %H:%M')}."
            except Exception as e:
                logger.error(f"Erro ao agendar: {e}")
                response_text = "Tentei agendar, mas houve um erro no banco de dados."
        else:
            response_text = "Entendi que quer agendar, mas não identifiquei a data/hora. Pode repetir?"
    else:
        # Conversa normal usando LLM
        response_text = caio.generate_message(user_text, context_memories)

    # 4. Enviar Resposta
    await context.bot.send_message(chat_id=user_id, text=response_text)
    
    # 5. Salvar Memória (Agent)
    memory.store(response_text, source="telegram_agent", importance=0.5)

if __name__ == '__main__':
    if not TELEGRAM_TOKEN:
        logger.error("Token do Telegram não encontrado!")
        exit(1)
        
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    msg_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    
    application.add_handler(start_handler)
    application.add_handler(msg_handler)
    
    logger.info("👂 Caio ouvindo no Telegram...")
    application.run_polling()
