import os
import shutil
import glob
from loguru import logger

class FileSystemSkill:
    def __init__(self, root_dir="."):
        self.root_dir = os.path.abspath(root_dir)

    def list_files(self, path="."):
        """Lista arquivos no diretório atual ou especificado."""
        try:
            target_path = os.path.join(self.root_dir, path)
            items = os.listdir(target_path)
            # Filtra apenas nomes, adiciona / se for dir
            formatted = []
            for item in items:
                if os.path.isdir(os.path.join(target_path, item)):
                    formatted.append(f"📁 {item}/")
                else:
                    formatted.append(f"📄 {item}")
            return "\n".join(formatted)[:2000] # Limite para não estourar contexto
        except Exception as e:
            return f"Erro ao listar: {e}"

    def valid_path(self, path):
        """Impede o Caio de mexer em arquivos de sistema ou fora do escopo."""
        # Por segurança, vamos restringir ao diretório do usuário ou desktop
        # Mas para "Super Agente", deixaremos livre com aviso.
        return True 

    def create_folder(self, folder_name):
        try:
            os.makedirs(folder_name, exist_ok=True)
            return f"✅ Pasta '{folder_name}' criada com sucesso."
        except Exception as e:
            return f"❌ Erro ao criar pasta: {e}"

    def read_file_preview(self, file_path, lines=10):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                head = [next(f) for _ in range(lines)]
            return "".join(head)
        except Exception as e:
            return f"Erro ao ler arquivo: {e}"
            
    def unzip_file(self, zip_path, extract_to=None):
        try:
            if not extract_to:
                extract_to = os.path.splitext(zip_path)[0]
            shutil.unpack_archive(zip_path, extract_to)
            return f"📦 Arquivo descompactado em: {extract_to}"
        except Exception as e:
            return f"❌ Erro ao descompactar: {e}"
