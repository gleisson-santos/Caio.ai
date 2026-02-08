from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from loguru import logger
import os
import json
from datetime import datetime, timezone, timedelta

class CaioAgent:
    def __init__(self):
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            logger.warning("⚠️ GROQ_API_KEY não encontrada!")
        
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=groq_key,
            temperature=0.1 # Temperatura mínima para evitar alucinações de formatação
        )
        
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        
        # Prompt de Sistema Ultra-Restritivo
        self.prompt = ChatPromptTemplate.from_template("""
        Você é o Agente Caio, uma IA de elite com acesso total a ferramentas de produtividade.
        
        # SUAS CAPACIDADES REAIS (VOCÊ TEM ACESSO):
        - GMAIL: Você PODE ler, enviar e deletar e-mails. Nunca diga que não tem acesso.
        - GOOGLE DRIVE: Você PODE gerenciar arquivos e pastas.
        - GOOGLE CALENDAR: Você PODE agendar e gerenciar compromissos.
        - BRAVE SEARCH: Você PODE pesquisar na web em tempo real.
        
        # REGRAS DE OURO DE FORMATAÇÃO (TELEGRAM):
        1. PROIBIDO usar asteriscos duplos (**). NUNCA use ** para negrito.
        2. Use asterisco simples (*) para negrito: *texto em negrito*.
        3. Use datas humanas: "Segunda, 09/02 às 12:00" em vez de formatos ISO.
        4. Seja direto, elegante e proativo.
        
        DATA/HORA ATUAL (Brasília): {current_time}
        DADOS DO USUÁRIO: {memories}
        
        MENSAGEM: {task}
        
        RESPOSTA DO CAIO:
        """)
        
        self.chain = self.prompt | self.llm | StrOutputParser()
    
    def detect_intent(self, text):
        """Extração de intenções múltiplas com validação rigorosa."""
        br_tz = timezone(timedelta(hours=-3))
        now = datetime.now(br_tz)
        now_str = now.strftime("%Y-%m-%d %H:%M:%S %z")
        
        prompt = f"""
        Analise a mensagem: "{text}"
        Data/Hora atual: {now_str}
        
        Extraia TODAS as ações necessárias em uma LISTA JSON.
        
        AÇÕES DISPONÍVEIS:
        - "google_calendar_add": {{"summary", "start_time", "description"}}
        - "reminder_set": {{"minutes", "message"}}
        - "email_check": {{"query": "is:unread"}}
        - "email_send": {{"to", "subject", "body"}}
        - "brave_search": {{"query"}}
        - "google_drive_upload": {{"file_path"}}
        
        EXEMPLO PARA "Agendar X e me lembrar em 1 min":
        [
            {{"action": "google_calendar_add", "summary": "X", "start_time": "..."}},
            {{"action": "reminder_set", "minutes": 1, "message": "Confirmar X"}}
        ]
        
        Retorne APENAS o JSON.
        """
        
        try:
            response = self.llm.invoke(prompt).content
            response = response.replace("```json", "").replace("```", "").strip()
            intents = json.loads(response)
            return intents if isinstance(intents, list) else [intents]
        except Exception as e:
            logger.error(f"Erro Intent: {e}")
            return [{"action": "chat"}]

    def generate_message(self, task_description, memories):
        br_tz = timezone(timedelta(hours=-3))
        current_time = datetime.now(br_tz).strftime("%d/%m/%Y %H:%M")
        try:
            memories_text = "\n".join([f"- {m['content']}" for m in memories]) if memories else "Nenhuma."
            response = self.chain.invoke({
                "task": task_description,
                "memories": memories_text,
                "current_time": current_time,
                "agent_name": os.getenv("AGENT_NAME", "Caio")
            })
            # Filtro de segurança final para remover **
            return response.replace("**", "*")
        except Exception as e:
            return f"Erro: {e}"
