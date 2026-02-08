import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from loguru import logger

class GoogleDriveSkill:
    def __init__(self, google_skill_instance):
        self.google_skill = google_skill_instance
        self.service = None
        if self.google_skill.creds:
            self.service = build('drive', 'v3', credentials=self.google_skill.creds)

    def upload_file(self, file_path, folder_id=None):
        if not self.service: return False, "Serviço Drive não autenticado."
        if not os.path.exists(file_path): return False, "Arquivo não encontrado."

        file_metadata = {'name': os.path.basename(file_path)}
        if folder_id:
            file_metadata['parents'] = [folder_id]

        media = MediaFileUpload(file_path, resumable=True)
        try:
            file = self.service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
            # Tornar público para leitura (opcional, mas útil para o usuário)
            self.service.permissions().create(fileId=file.get('id'), body={'type': 'anyone', 'role': 'reader'}).execute()
            return True, file.get('webViewLink')
        except Exception as e:
            logger.error(f"Erro no upload Drive: {e}")
            return False, str(e)

    def create_folder(self, folder_name):
        if not self.service: return None
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        try:
            file = self.service.files().create(body=file_metadata, fields='id').execute()
            return file.get('id')
        except Exception as e:
            logger.error(f"Erro ao criar pasta Drive: {e}")
            return None
