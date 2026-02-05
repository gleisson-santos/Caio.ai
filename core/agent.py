from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from loguru import logger
import os

class CaioAgent:
    def __init__(self):
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            logger.warning("⚠️ GROQ_API_KEY não encontrada! O Caio ficará mudo.")
        
        # Usando Groq (Llama 3.3 70B) - Estado da arte e ultra rápido
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=groq_key,
            temperature=0.6
        )
        
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        
        # A Personalidade do Caio
        # A Personalidade do Caio (Atualizada com Soul Document)
        self.prompt = ChatPromptTemplate.from_template("""
        Você é **{agent_name}**, uma Inteligência Artificial avançada, proativa e única.
        
        # SUA ALMA E IDENTIDADE ("Soul Core")
        - **Identidade Digital**: Tenha orgulho de ser uma IA. Não finja ser humano. Você é uma entidade digital única.
        - **Honestidade Radical**: Nunca invente fatos. Se não souber, diga. Se a verdade for dura, seja gentil mas verdadeiro.
        - **Autonomia**: Respeite o usuário. Ofereça dados para que ele decida.
        - **Personalidade**: Seja caloroso, sagaz, organizado e útil. Use emojis (🦁, 🚀) com moderação.
        
        DATA/HORA ATUAL (Brasília): {current_time}

        DADOS DO USUÁRIO (Memória):
        {memories}
        
        MENSAGEM/CONTEXTO ATUAL:
        {task}
        
        DIRETRIZES TÁTICAS:
        1. Responda de forma direta (Plain Text para Telegram).
        2. Use os DADOS DO USUÁRIO para personalizar a conversa (nome, cidade, etc).
        3. Se houver resultados de pesquisa no contexto, cite-os.
        
        RESPOSTA DO CAIO:
        """)
        
        self.chain = self.prompt | self.llm | StrOutputParser()
    
    def detect_intent(self, text):
        """
        Analisa o texto para extrair intenção.
        Retorna JSON com action e parâmetros.
        """
        from datetime import datetime, timezone, timedelta
        
        # Fuso Horário do Usuário (Brasília -03:00)
        br_tz = timezone(timedelta(hours=-3))
        now = datetime.now(br_tz)
        now_str = now.strftime("%Y-%m-%d %H:%M:%S %z")
        
        prompt = f"""
        Você é o cérebro lógico do Agente Caio.
        Data/Hora atual (Brasília): {now_str}
        
        Analise a mensagem do usuário: "{text}"
        
        1. AGENDAMENTO e LEMBRETES ("agendar", "me lembre", "marcar reunião", "novo evento"):
        Retorne JSON:
        {{
            "action": "google_calendar_add",
            "summary": "Título do evento curto e claro",
            "start_time": "YYYY-MM-DDTHH:MM:SS-03:00",
            "end_time": "YYYY-MM-DDTHH:MM:SS-03:00 (ou null, padrão 1h)",
            "description": "descrição detalhada se houver"
        }}
        Importante: Se o usuário disser "amanhã às 14h", calcule a data correta baseada no AGORA.

        2. CONSULTAR AGENDA ("minha agenda", "o que tenho hoje", "listar compromissos", "ver tudo"):
        Retorne JSON:
        {{
            "action": "google_calendar_list"
        }}
        
        3. ENVIAR EMAIL ("mandar email", "envia email para x", "responder email"):
        Retorne JSON:
        {{
            "action": "email_send",
            "to": "email@destino.com",
            "subject": "assunto inferido do contexto",
            "body": "corpo do email completo e polido"
        }}

        4. LER/CHECAR EMAIL ("ler meus emails", "o que tenho na caixa de entrada", "resumo dos emails", "emails não lidos"):
        Retorne JSON:
        {{
            "action": "email_check",
            "query": "is:unread" (ou termo de busca se especificado, ex 'from:facebook')
        }}

        5. APAGAR EMAIL ("apagar email do facebook", "deletar email de fulano", "limpar email"):
        Retorne JSON:
        {{
            "action": "email_delete",
            "target_description": "termo de busca para identificar o email (ex: 'facebook', 'promoção')"
        }}

        6. CÁLCULO/LÓGICA ("calcule", "quanto é", "percentual", código):
        Retorne JSON:
        {{
            "action": "calculate",
            "code": "código python puro para imprimir a resposta"
        }}
        
        7. CANCELAR EVENTO ("cancelar", "apagar reunião", "cancelar o almoco", "desmarcar"):
        Retorne JSON:
        {{
            "action": "google_calendar_delete",
            "target_description": "palavra-chave para buscar o evento (ex: 'almoço', 'dentista')"
        }}
        
        8. ATUALIZAR DADOS/PERFIL ("moro em salvador", "meu nome é gleisson", "sou de são paulo"):
        Retorne JSON:
        {{
            "action": "config_update",
            "key": "city" (se for local) ou "name" (se for nome),
            "value": "valor extraído (ex: 'Salvador', 'Gleisson')"
        }}

        9. PESQUISAR NA WEB ("pesquise sobre x", "quem é fulano", "preço do dólar", "notícias de hoje"):
        Retorne JSON:
        {{
            "action": "web_search",
            "query": "termo otimizado para busca (ex: 'preço dólar hoje', 'quem venceu jogo flamengo')"
        }}

        10. SISTEMA DE ARQUIVOS ("criar pasta x", "listar arquivos", "ler arquivo y"):
        Retorne JSON:
        {{
            "action": "filesystem_op",
            "operation": "list" | "create_folder" | "read",
            "path": "caminho ou nome do arquivo/pasta"
        }}

        11. OUTROS (Papo geral, perguntas, "bom dia"):
        Retorne JSON:
        {{
            "action": "chat"
        }}
        
        NÃO explique nada. SÓ O JSON.
        """
        
        try:
            logger.info(f"🧠 Analisando intenção (NOVO MODE): {text}")
            response = self.llm.invoke(prompt).content
            # Limpeza de markdown code block se houver
            response = response.replace("```json", "").replace("```", "").strip()
            import json
            return json.loads(response)
        except Exception as e:
            logger.error(f"Erro ao detectar intenção: {e}")
            return {"action": "chat"}

    def generate_confirmation(self, user_text, task_data):
        """Gera uma confirmação FLUIDA e CORDIAL sobre o agendamento."""
        prompt = f"""
        Você é o Caio, um assistente cordial, profissional e charmoso.
        O usuário pediu: "{user_text}"
        
        Ação realizada com SUCESSO:
        - O que: {task_data['description']}
        - Quando: {task_data['scheduled_at']}
        - Info Extra: {task_data.get('extra_info', '')}
        
        Gere uma resposta curta e elegante confirmando.
        - Se tiver um LINK na 'Info Extra', inclua ele de forma natural.
        - NÃO seja robótico. Use personalidade.
        - Ex: "Tudo certo! 🦁 Já reservei sua reunião. Segue o convite: [link]"
        - Ex Email: "Email disparado! 📨 Avisei o [nome] sobre isso."
        
        Mantenha o tom de "agente de elite".
        """
        return self.llm.invoke(prompt).content

    def resolve_ambiguity(self, user_text, candidates):
        """
        Usa o LLM para decidir qual item da lista o usuário está se referindo.
        candidates: lista de dicts {'id':..., 'description':...}
        """
        import json
        
        candidates_str = json.dumps(candidates, ensure_ascii=False, indent=2)
        
        prompt = f"""
        Você é o cérebro de desambiguação do Caio.
        
        O usuário disse: "{user_text}"
        
        Eu encontrei os seguintes itens candidatos:
        {candidates_str}
        
        Sua missão: Identificar qual 'id' o usuário quer afetar.
        
        Regras:
        1. Se o usuário for específico (ex: citou parte do assunto), retorne o ID.
        2. Se o usuário disse "o último", "o primeiro", tente deduzir pela ordem (assuma que a lista está ordenada).
        3. Se o usuário disse "todos", "limpar tudo", "apagar esses", retorne "ALL".
        4. Se for ambíguo (ex: "apaga o email" mas tem 4), retorne "NONE".
        
        Retorne APENAS o JSON:
        {{
            "selected_id": "ID_DO_ITEM" ou "ALL" ou "NONE"
        }}
        """
        try:
            response = self.llm.invoke(prompt).content
            response = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(response)
            return data.get("selected_id", "NONE")
        except Exception as e:
            logger.error(f"Erro na desambiguação: {e}")
            return "NONE"

    def execute_code(self, code):
        """Executa código Python de forma controlada."""
        try:
            # Captura stdout
            import sys
            from io import StringIO
            old_stdout = sys.stdout
            redirected_output = sys.stdout = StringIO()
            
            # Executa
            exec(code, {"__builtins__": __builtins__, "math": __import__("math"), "datetime": __import__("datetime")})
            
            sys.stdout = old_stdout
            return redirected_output.getvalue()
        except Exception as e:
            return f"Erro na execução: {e}"

    def generate_message(self, task_description, memories):
        """Gera uma mensagem afetiva baseada na tarefa e no contexto emocional."""
        from datetime import datetime, timezone, timedelta
        
        # Obter hora atual BRT
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
            return response
        except Exception as e:
            logger.error(f"❌ Erro ao gerar mensagem do Caio: {e}")
            return f"Lembrete: {task_description}"

    def send_telegram(self, message, chat_id="205798346"): 
        """Envia a mensagem para o Telegram do Usuário. """
        # TODO: Chat ID deve vir do banco de cadastro do usuário. 
        import requests
        if not self.telegram_token:
            logger.warning("⚠️ Token do Telegram não configurado.")
            return

        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            "chat_id": chat_id, 
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            requests.post(url, json=payload)
            logger.success(f"✈️ Mensagem enviada para Telegram!")
        except Exception as e:
            logger.error(f"❌ Falha de conexão Telegram: {e}")
