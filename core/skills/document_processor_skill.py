import os
from loguru import logger
import PyPDF2
from docx import Document
import openpyxl

class DocumentProcessorSkill:
    def read_pdf(self, path):
        try:
            text = ""
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text()
            return text
        except Exception as e:
            return f"Erro ao ler PDF: {e}"

    def read_docx(self, path):
        try:
            doc = Document(path)
            return "\n".join([p.text for p in doc.paragraphs])
        except Exception as e:
            return f"Erro ao ler DOCX: {e}"

    def read_xlsx(self, path):
        try:
            wb = openpyxl.load_dotenv(path)
            sheet = wb.active
            data = []
            for row in sheet.iter_rows(values_only=True):
                data.append("\t".join([str(c) for c in row if c is not None]))
            return "\n".join(data)
        except Exception as e:
            return f"Erro ao ler XLSX: {e}"

    def process(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext == ".pdf": return self.read_pdf(path)
        if ext == ".docx": return self.read_docx(path)
        if ext in [".xlsx", ".xls"]: return self.read_xlsx(path)
        return "Formato não suportado."
