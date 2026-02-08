import os.path
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from loguru import logger
import datetime

# Cores para terminal
BLUE = "\033[34m"
RESET = "\033[0m"

# PERMITE HTTP EM LOCALHOST (Correção para o erro 'insecure_transport')
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Escopos necessários
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.modify' # Permite ler, enviar e deletar
]

class GoogleSkill:
    def __init__(self, credentials_path="credentials.json", token_path="token.json"):
        self.creds = None
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service_calendar = None
        self.service_gmail = None
        
        self._authenticate()

    def _authenticate(self):
        """Gerencia o ciclo de vida de autenticação (OAuth2)."""
        self.creds = None
        
        # Localizar arquivos (flexibilidade para rodar da raiz ou de core/)
        creds_path = "credentials.json"
        if not os.path.exists(creds_path) and os.path.exists("core/credentials.json"):
            creds_path = "core/credentials.json"

        token_path = "token.json"
        if not os.path.exists(token_path) and os.path.exists("core/token.json"):
            token_path = "core/token.json"
        
        # Tenta carregar token existente
        if os.path.exists(token_path):
            try:
                self.creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            except Exception:
                logger.warning("Token inválido ou corrompido.")
                self.creds = None
        
        # Se não temos credenciais válidas
        if not self.creds or not self.creds.valid:
            # Tentar refresh
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    logger.warning(f"Erro ao atualizar token: {e}. Necessário novo login.")
                    self.creds = None
            
            # Se ainda não temos credenciais, precisamos fazer login
            if not self.creds:
                # Se não tem o arquivo Client ID, não podemos logar. Desativamos a skill.
                if not os.path.exists(creds_path):
                    logger.warning(f"⚠️ Google Skill (Gmail/Calendar) desativada: '{creds_path}' não encontrado.")
                    # Não retornamos erro, apenas deixamos self.creds como None
                    return 

                # Inicializa o fluxo ANTES do try para estar disponível no except
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                
                try:
                    # Tenta método automático primeiro (abre navegador)
                    # Se estiver em VPS sem X11, isso vai falhar
                    logger.info("Tentando abrir navegador para autenticação...")
                    self.creds = flow.run_local_server(port=0)
                except Exception as e:
                    logger.warning(f"Navegador automático falhou ({e}). Iniciando modo manual (VPS)...")
                    
                    # Modo Manual (Inspirado no OpenClaw / GCloud CLI)
                    auth_url, _ = flow.authorization_url(prompt='consent')
                    
                    print("\n" + "="*60)
                    print("🦁 MODO DE AUTENTICAÇÃO MANUAL (VPS)")
                    print("="*60)
                    print("1. Abra este link no seu navegador (PC/Celular):")
                    print(f"{BLUE}{auth_url}{RESET}")
                    print("-" * 60)
                    print("2. Faça login e autorize o app.")
                    print("3. Você será redirecionado para uma página (provavelmente com erro 'Não foi possível conectar').")
                    print("4. COPIE A URL INTEIRA da barra de endereços dessa página de erro.")
                    print("5. Cole a URL abaixo:")
                    print("="*60 + "\n")
                    
                    code_url = input("Cole a URL de redirecionamento aqui: ").strip()
                    
                    try:
                        # O google-auth-oauthlib consegue extrair o código da URL completa
                        # Precisamos garantir que o flow saiba que o redirect_uri é localhost (ou o que estiver no JSON)
                        flow.fetch_token(authorization_response=code_url)
                        self.creds = flow.credentials
                    except Exception as token_error:
                        logger.error(f"Erro ao trocar código por token: {token_error}")
                        return
        
        # Inicializar Serviços
        try:
            self.service_calendar = build('calendar', 'v3', credentials=self.creds)
            self.service_gmail = build('gmail', 'v1', credentials=self.creds)
            logger.success("✅ Conectado ao Google Calendar e Gmail!")
        except Exception as e:
            logger.error(f"Erro ao conectar serviços Google: {e}")

    # === CALENDAR ===
    def list_upcoming_events(self, max_results=10):
        """Lista os próximos eventos formatados."""
        if not self.service_calendar:
            return "⚠️ Serviço de Calendário não disponível."

        try:
            now = datetime.datetime.utcnow().isoformat() + 'Z' 
            events_result = self.service_calendar.events().list(
                calendarId='primary', timeMin=now,
                maxResults=max_results, singleEvents=True,
                orderBy='startTime').execute()
            events = events_result.get('items', [])

            if not events:
                return "📅 **Agenda Tranquila:** Nenhum compromisso futuro encontrado."

            result_text = "📅 **Agenda do Google:**\n\n"
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                # Formatar data se for ISO (2026-02-05T14:00:00-03:00)
                try:
                    # Tenta parsear para deixar bonito
                    dt = datetime.datetime.fromisoformat(start)
                    start_fmt = dt.strftime('%d/%m às %H:%M')
                    # Se for dia todo (não tem hora), ajusta
                    if len(start) == 10: # YYYY-MM-DD
                        start_fmt = dt.strftime('%d/%m (Dia todo)')
                except:
                    start_fmt = start

                result_text += f"🗓️ *{start_fmt}* — {event['summary']}\n"
            
            return result_text

        except HttpError as error:
            logger.error(f"Erro na API do Calendar: {error}")
            return f"❌ Erro ao buscar eventos: {error}"

    def create_event(self, summary, start_datetime_iso, end_datetime_iso=None, description=""):
        if not self.service_calendar: return False, "Serviço Google não autenticado."
        
        # Garante end_time se não houver
        if not end_datetime_iso:
            try:
                dt_start = datetime.datetime.fromisoformat(start_datetime_iso)
                dt_end = dt_start + datetime.timedelta(hours=1)
                end_datetime_iso = dt_end.isoformat()
            except ValueError: return False, "Formato de data inválido. Use ISO 8601."

        event_body = {
            'summary': summary, 
            'description': description,
            'start': {'dateTime': start_datetime_iso, 'timeZone': 'America/Sao_Paulo'}, 
            'end': {'dateTime': end_datetime_iso, 'timeZone': 'America/Sao_Paulo'}
        }
        
        try:
            created_event = self.service_calendar.events().insert(calendarId='primary', body=event_body).execute()
            
            # Formatação Humana Obrigatória (Modo Clawbot)
            try:
                dt_obj = datetime.datetime.fromisoformat(start_datetime_iso)
                # Formato: 09/02 (Seg) às 14:00
                weekdays = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
                wd = weekdays[dt_obj.weekday()]
                human_date = dt_obj.strftime(f"%d/%m ({wd}) às %H:%M")
            except:
                # Fallback de Emergência (Tenta limpar a string na força bruta)
                human_date = str(start_datetime_iso).replace('T', ' ').split('.')[0]
                
            return True, f"Agendado: **{summary}** para {human_date}" 
            
        except HttpError as error: return False, str(error)

    def delete_event(self, event_id):
        if not self.service_calendar: return False, "Serviço não autenticado."
        try:
            self.service_calendar.events().delete(calendarId='primary', eventId=event_id).execute()
            return True, "Evento deletado com sucesso."
        except HttpError as error: return False, str(error)

    def find_event(self, query):
        if not self.service_calendar: return []
        try:
            now = datetime.datetime.utcnow().isoformat() + 'Z'
            events_result = self.service_calendar.events().list(
                calendarId='primary', timeMin=now, q=query, maxResults=5, singleEvents=True, orderBy='startTime').execute()
            return events_result.get('items', [])
        except HttpError as error: return []

    # === GMAIL (NOVO: READ/DELETE) ===
    def list_unread_emails(self, limit=50):
        """Lista e analisa e-mails não lidos (Formatação Limpa)."""
        try:
            if not self.creds: return "Não autenticado."
            if not self.service_gmail: return "Serviço Gmail não disponível."
            
            results = self.service_gmail.users().messages().list(userId='me', q='is:unread', maxResults=limit).execute()
            messages = results.get('messages', [])
            
            if not messages:
                return "📭 Tudo limpo! Nenhum e-mail novo."
            
            summary = {
                "total": len(messages),
                "urgentes": [],
                "bancos": [],
                "destaques": []
            }
            
            keywords_urgente = ["urgente", "vencimento", "atraso", "importante", "fatura", "atenção"]
            keywords_banco = ["inter", "picpay", "nubank", "bradesco", "itaú", "santander", "caixa", "banco"]

            count = 0
            for msg in messages:
                txt = self.service_gmail.users().messages().get(userId='me', id=msg['id']).execute()
                headers = txt['payload']['headers']
                
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "Sem Assunto")
                raw_sender = next((h['value'] for h in headers if h['name'] == 'From'), "Desconhecido")
                
                # Limpeza do Remetente (Remove <email@...>)
                sender = raw_sender.split('<')[0].strip().replace('"', '')
                if len(sender) > 20: sender = sender[:20] + "..." # Trunca nomes gigantes
                
                # Categorização
                lower_subj = subject.lower()
                lower_sender = sender.lower()
                
                is_urgent = any(k in lower_subj for k in keywords_urgente)
                is_bank = any(k in lower_sender for k in keywords_banco)
                
                item = f"• *{sender}*: {subject}"
                
                if is_urgent:
                    summary["urgentes"].append(item)
                elif is_bank:
                    summary["bancos"].append(item)
                else:
                    # Adiciona aos destaques (apenas os primeiros 5 gerais)
                    if len(summary["destaques"]) < 5:
                        summary["destaques"].append(item)

            # --- Construção da Resposta (Estilo Clean) ---
            response = [f"📬 **Resumo do Email**"]
            response.append(f"Você tem **{summary['total']}** emails não lidos.")
            
            if summary["urgentes"]:
                response.append(f"\n🚨 **{len(summary['urgentes'])} Urgentes:**")
                response.extend(summary["urgentes"])
            
            if summary["bancos"]:
                response.append(f"\n💰 **{len(summary['bancos'])} Financeiros:**")
                response.extend(summary["bancos"])
                
            if summary["destaques"]:
                response.append(f"\n📝 **Recentes:**")
                response.extend(summary["destaques"])
                
            remaining = summary['total'] - (len(summary["urgentes"]) + len(summary["bancos"]) + len(summary["destaques"]))
            if remaining > 0:
                response.append(f"\n... e mais {remaining} outros.")

            return "\n".join(response)

        except Exception as e:
            return f"Erro ao ler e-mails: {e}"

    def search_emails(self, query, max_results=5):
        """Busca emails por query livre."""
        if not self.service_gmail: return []
        try:
            results = self.service_gmail.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
            messages = results.get('messages', [])
            
            email_data = []
            for msg in messages:
                txt = self.service_gmail.users().messages().get(userId='me', id=msg['id'], format='metadata').execute()
                headers = txt.get('payload', {}).get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(Sem Assunto)')
                email_data.append({'id': msg['id'], 'subject': subject})
            return email_data
        except HttpError as error: return []

    def delete_email(self, msg_id):
        """Move para lixeira (Trash)."""
        if not self.service_gmail: return False, "Auth Error"
        try:
            self.service_gmail.users().messages().trash(userId='me', id=msg_id).execute()
            return True, "Email movido para lixeira."
        except HttpError as error: return False, str(error)

    def send_email(self, to, subject, body_text):
        if not self.service_gmail: return False, "Serviço Gmail não autenticado."
        try:
            message = MIMEText(body_text)
            message['to'] = to
            message['subject'] = subject
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            body = {'raw': raw}
            message = self.service_gmail.users().messages().send(userId='me', body=body).execute()
            return True, f"✅ E-mail enviado! ID: {message['id']}"
        except HttpError as error: return False, f"Erro ao enviar email: {error}"
