import os
import json
import time
from loguru import logger

class MemorySystem:
    """
    Sistema de Memória Local Híbrido (JSON-based).
    Substitui o Supabase temporariamente para garantir robustez local ("Runs on your machine").
    """
    def __init__(self, file_path="brain_data.json"):
        self.file_path = file_path
        self.data = {
            "profile": {},       # Preferências (Cidade, Nome, etc.)
            "episodic": []       # Histórico de conversas/fatos
        }
        self.load()

    def load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                # Garante estrutura
                if "profile" not in self.data: self.data["profile"] = {}
                if "episodic" not in self.data: self.data["episodic"] = []
            except Exception as e:
                logger.error(f"Erro ao carregar memória: {e}")

    def save(self):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar memória: {e}")

    # === PREFERÊNCIAS (PERFIL) ===
    def set_preference(self, key, value):
        """Salva um dado estruturado do usuário (ex: city: Salvador)."""
        self.data["profile"][key] = value
        self.save()
        logger.success(f"🧠 Perfil Atualizado: {key} = {value}")

    def get_preference(self, key, default=None):
        return self.data["profile"].get(key, default)

    # === MEMÓRIA EPISÓDICA (BUSCA) ===
    def store(self, content, source="chat", importance=1):
        """Guarda uma memória episódica."""
        entry = {
            "content": content,
            "source": source,
            "importance": importance,
            "timestamp": time.time(),
            "date": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.data["episodic"].append(entry)
        # Mantém apenas as últimas 1000 memórias para não explodir o JSON
        if len(self.data["episodic"]) > 1000:
            self.data["episodic"] = self.data["episodic"][-1000:]
            
        self.save()
        logger.debug(f"💾 Memória salva: {content[:30]}...")
        return True

    def recall(self, query, limit=5):
        """
        Recuperação simples baseada em palavras-chave (Keyword Matching).
        Para um sistema local avançado, usaríamos ChromaDB ou FAISS aqui depois.
        """
        query_terms = query.lower().split()
        results = []
        
        # Busca reversa (mais recentes primeiro)
        for mem in reversed(self.data["episodic"]):
            score = 0
            content_lower = mem["content"].lower()
            
            for term in query_terms:
                if term in content_lower:
                    score += 1
            
            if score > 0:
                results.append({
                    "content": mem["content"],
                    "similarity": score, # Mock de score
                    "created_at": mem["date"]
                })
                
            if len(results) >= limit:
                break
                
        logger.info(f"🧠 Memórias recuperadas: {len(results)}")
        return results
