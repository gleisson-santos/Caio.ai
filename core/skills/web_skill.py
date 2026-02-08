import os
import requests
from duckduckgo_search import DDGS
from loguru import logger

class WebSkill:
    def __init__(self):
        self.brave_key = os.getenv("BRAVE_API_KEY")
        self.ddgs = DDGS()

    def search(self, query, max_results=5):
        """
        Faz busca na web. 
        Prioridade: Brave Search API (se configurada) -> DuckDuckGo (fallback).
        """
        if self.brave_key:
            return self._search_brave(query, max_results)
        else:
            return self._search_ddg(query, max_results)

    def _search_brave(self, query, max_results):
        try:
            logger.info(f"🦁 Buscando via Brave Search: {query}")
            headers = {"X-Subscription-Token": self.brave_key, "Accept": "application/json"}
            params = {"q": query, "count": max_results}
            
            resp = requests.get("https://api.search.brave.com/res/v1/web/search", headers=headers, params=params)
            
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("web", {}).get("results", [])
                formatted = []
                for r in results:
                    formatted.append(f"Título: {r['title']}\nLink: {r['url']}\nResumo: {r.get('description', '')}\n")
                return formatted
            else:
                logger.warning(f"Erro na Brave API ({resp.status_code}). Tentando DDG...")
                return self._search_ddg(query, max_results)
                
        except Exception as e:
            logger.error(f"Erro Brave Search: {e}. Fallback para DDG.")
            return self._search_ddg(query, max_results)

    def _search_ddg(self, query, max_results):
        try:
            logger.info(f"🦆 Buscando via DuckDuckGo: {query}")
            # DDGS.text retorna generator ou lista de dicts dependendo da versão
            # Forçamos list() para garantir iterabilidade
            results = list(self.ddgs.text(query, max_results=max_results))
            
            if not results:
                return []
            
            formatted = []
            for r in results:
                title = r.get('title', 'Sem título')
                link = r.get('href', '#')
                body = r.get('body', '')
                formatted.append(f"Título: {title}\nLink: {link}\nResumo: {body}\n")
            
            return formatted
        except Exception as e:
            logger.error(f"Erro na busca DDG: {e}")
            return []
