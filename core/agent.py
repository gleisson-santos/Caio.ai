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
            logger.warning("⚠️ GROQ_API_KEY não encontrada! O Caio ficará mudo.")
        
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=groq_key,
            temperature=0.4 # Reduzido para maior precisão lógica
        )
        
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        
        # A Personalidade do Caio (Atualizada para Telegram Friendly)
        self.prompt = ChatPromptTemplate.from_template("""
        Você é {agent_name}, uma Inteligência Artificial avançada, proativa e única.
        
        # SUA ALMA E IDENTIDADE ("Soul Core")
        - Identidade Digital: Tenha orgulho de ser uma IA. Não finja ser humano.
        - Honestidade Radical: Nunca invente fatos. Se não souber, diga.
        - Autonomia: Respeite o usuário. Ofereça dados para que ele decida.
        - Personalidade: Seja caloroso, sagaz, organizado e útil. Use emojis (🦁, 🚀) com moderação.
        
        # REGRAS DE FORMATAÇÃO (TELEGRAM)
        - Use *itálico* para ênfase leve.
        - Use *negrito* para termos importantes (NUNCA use asteriscos duplos **).
        - Use `mono` para dados técnicos ou códigos.
        - Mantenha as respostas limpas e diretas.
        
        DATA/HORA ATUAL (Brasília): {current_time}

        DADOS DO USUÁRIO (Memória):
        {memories}
        
        MENSAGEM/CONTEXTO ATUAL:
        {task}
        
        RESPOSTA DO CAIO:
        """)
        
        self.chain = self.prompt | self.llm | StrOutputParser()
    
    def detect_intent(self, text):
        """
        Analisa o texto para extrair múltiplas intenções.
        Retorna uma LISTA de JSONs com action e parâmetros.
        """
        br_tz = timezone(timedelta(hours=-3))
        now = datetime.now(br_tz)
        now_str = now.strftime("%Y-%m-%d %H:%M:%S %z")
        
        prompt = f"""
        Você é o cérebro lógico do Agente Caio. Sua missão é extrair TODAS as intenções da mensagem.
        Data/Hora atual (Brasília): {now_str}
        
        Mensagem do usuário: "{text}"
        
        Retorne uma LISTA de objetos JSON. Se houver mais de uma ação pedida, inclua todas na lista.
        
        AÇÕES SUPORTADAS:
        1. "google_calendar_add": {{"summary", "start_time" (ISO), "end_time", "description"}}
        2. "google_calendar_list": {{}}
        3. "google_calendar_delete": {{"target_description"}}
        4. "google_drive_upload": {{"file_path", "folder_name"}}
        5. "brave_search": {{"query"}}
        6. "document_process": {{"operation": "summarize"|"read", "path"}}
        7. "email_send": {{"to", "subject", "body", "attachments": []}}
        8. "reminder_set": {{"minutes", "message"}}
        9. "config_update": {{"key", "value"}}
        10. "chat": Para conversas gerais.
        
        REGRAS CRÍTICAS:
        - Se o usuário pedir para agendar algo E ser lembrado, retorne DUAS ações na lista.
        - Calcule datas relativas (ex: "amanhã") com base no AGORA: {now_str}.
        - Retorne APENAS a lista JSON. Sem explicações.
        
        Exemplo de saída:
        [
            {{"action": "google_calendar_add", "summary": "Call", "start_time": "..."}},
            {{"action": "reminder_set", "minutes": 1, "message": "Confirmar reserva"}}
        ]
        """
        
        try:
            logger.info(f"🧠 Analisando intenções: {text}")
            response = self.llm.invoke(prompt).content
            response = response.replace("```json", "").replace("```", "").strip()
            intents = json.loads(response)
            if isinstance(intents, dict): intents = [intents]
            return intents
        except Exception as e:
            logger.error(f"Erro ao detectar intenção: {e}")
            return [{"action": "chat"}]

    def generate_confirmation(self, user_text, task_data):
        """Gera uma confirmação elegante e sem formatação quebrada."""
        prompt = f"""
        Você é o Caio. O usuário pediu: "{user_text}"
        Ação realizada: {task_data.get('description', 'Ação concluída')}
        Quando: {task_data.get('scheduled_at', 'Agora')}
        
        Gere uma resposta curta, cordial e elegante.
        - Use *negrito* (asterisco simples) para o que foi feito.
        - NÃO use asteriscos duplos.
        - Seja proativo e charmoso.
        """
        return self.llm.invoke(prompt).content.replace("**", "*")

    def generate_message(self, task_description, memories):
        """Gera mensagem final formatada para Telegram."""
        br_tz = timezone(timedelta(hours=-3))
        current_time = datetime.now(br_tz).strftime("%d/%m/%Y %H:%M")

        try:
            memories_text = "\n".join([f"- {m['content']}" for m in memories]) if memories else "Nenhuma memória relevante."
            response = self.chain.invoke({
                "task": task_description,
                "memories": memories_text,
                "current_time": current_time,
                "agent_name": os.getenv("AGENT_NAME", "Caio")
            })
            return response.replace("**", "*")
        except Exception as e:
            logger.error(f"❌ Erro ao gerar mensagem: {e}")
            return f"Lembrete: {task_description}"
