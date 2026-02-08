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
import re

# Cores para terminal
BLUE = "\033[34m"
RESET = "\033[0m"

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/drive.file'
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
        self.creds = None
        creds_path = "credentials.json"
        if not os.path.exists(creds_path) and os.path.exists("core/credentials.json"):
            creds_path = "core/credentials.json"

        token_path = "token.json"
        if not os.path.exists(token_path) and os.path.exists("core/token.json"):
            token_path = "core/token.json"
        
        if os.path.exists(token_path):
            try:
                self.creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            except Exception:
                self.creds = None
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception:
                    self.creds = None
            
            if not self.creds:
                if not os.path.exists(creds_path):
                    logger.warning(f"⚠️ Google Skill desativada: '{creds_path}' não encontrado.")
                    return 

                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                try:
                    self.creds = flow.run_local_server(port=0)
                except Exception:
                    auth_url, _ = flow.authorization_url(prompt='consent')
                    print(f"\n🦁 MODO MANUAL: {BLUE}{auth_url}{RESET}\n")
                    code_url = input("Cole a URL de redirecionamento: ").strip()
                    flow.fetch_token(authorization_response=code_url)
                    self.creds = flow.credentials
        
        if self.creds:
            self.service_calendar = build('calendar', 'v3', credentials=self.creds)
            self.service_gmail = build('gmail', 'v1', credentials=self.creds)
            logger.success("✅ Google Services Conectados!")

    def _parse_datetime(self, dt_str):
        """Tenta converter strings de data da IA para o formato ISO do Google."""
        try:
            # Remove espaços extras e limpa a string
            dt_str = dt_str.strip().replace(" ", "T")
            # Se a IA mandou algo como 2026-02-09T12:00:00-0300 (sem os dois pontos no fuso)
            if re.search(r"-\d{4}$", dt_str):
                dt_str = dt_str[:-2] + ":" + dt_str[-2:]
            
            # Tenta parsear para validar
            dt_obj = datetime.datetime.fromisoformat(dt_str)
            return dt_obj.isoformat()
        except Exception as e:
            logger.error(f"Erro ao parsear data '{dt_str}': {e}")
            return None

    def get_upcoming_raw(self, max_results=10):
        if not self.service_calendar: return []
        try:
            now = datetime.datetime.utcnow().isoformat() + 'Z'
            events_result = self.service_calendar.events().list(
                calendarId='primary', timeMin=now, maxResults=max_results, singleEvents=True, orderBy='startTime').execute()
            return events_result.get('items', [])
        except Exception: return []

    def create_event(self, summary, start_datetime_iso, end_datetime_iso=None, description=""):
        if not self.service_calendar: return False, "Não autenticado."
        
        # Validação e Limpeza da Data
        clean_start = self._parse_datetime(start_datetime_iso)
        if not clean_start:
            return False, f"Formato de data inválido: {start_datetime_iso}"

        if not end_datetime_iso:
            dt_start = datetime.datetime.fromisoformat(clean_start)
            dt_end = dt_start + datetime.timedelta(hours=1)
            clean_end = dt_end.isoformat()
        else:
            clean_end = self._parse_datetime(end_datetime_iso)

        event_body = {
            'summary': summary, 
            'description': description,
            'start': {'dateTime': clean_start, 'timeZone': 'America/Sao_Paulo'}, 
            'end': {'dateTime': clean_end, 'timeZone': 'America/Sao_Paulo'}
        }
        
        try:
            self.service_calendar.events().insert(calendarId='primary', body=event_body).execute()
            dt_obj = datetime.datetime.fromisoformat(clean_start)
            weekdays = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
            wd = weekdays[dt_obj.weekday()]
            human_date = dt_obj.strftime(f"%d/%m ({wd}) às %H:%M")
            return True, f"Agendado: *{summary}* para {human_date}" 
        except HttpError as e:
            logger.error(f"Erro Google API: {e.content}")
            return False, f"Erro na Agenda: Verifique o fuso horário ou formato."
        except Exception as e:
            return False, str(e)

    def list_unread_emails(self, limit=5):
        if not self.service_gmail: return "Gmail não disponível."
        try:
            results = self.service_gmail.users().messages().list(userId='me', q='is:unread', maxResults=limit).execute()
            messages = results.get('messages', [])
            if not messages: return "📭 Nenhum e-mail novo."
            
            res = "📩 *E-mails não lidos:*\n"
            for m in messages:
                msg = self.service_gmail.users().messages().get(userId='me', id=m['id']).execute()
                headers = msg['payload']['headers']
                subject = next(h['value'] for h in headers if h['name'] == 'Subject')
                sender = next(h['value'] for h in headers if h['name'] == 'From').split('<')[0]
                res += f"• *{sender.strip()}*: {subject}\n"
            return res
        except Exception as e:
            return f"Erro ao ler e-mails: {e}"
