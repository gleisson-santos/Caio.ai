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
        if not end_datetime_iso:
            try:
                dt_start = datetime.datetime.fromisoformat(start_datetime_iso)
                dt_end = dt_start + datetime.timedelta(hours=1)
                end_datetime_iso = dt_end.isoformat()
            except: return False, "Data inválida."

        event_body = {
            'summary': summary, 
            'description': description,
            'start': {'dateTime': start_datetime_iso, 'timeZone': 'America/Sao_Paulo'}, 
            'end': {'dateTime': end_datetime_iso, 'timeZone': 'America/Sao_Paulo'}
        }
        
        try:
            self.service_calendar.events().insert(calendarId='primary', body=event_body).execute()
            dt_obj = datetime.datetime.fromisoformat(start_datetime_iso)
            weekdays = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
            wd = weekdays[dt_obj.weekday()]
            human_date = dt_obj.strftime(f"%d/%m ({wd}) às %H:%M")
            return True, f"Agendado: *{summary}* para {human_date}" 
        except Exception as e: return False, str(e)
