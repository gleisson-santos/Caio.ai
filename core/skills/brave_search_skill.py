import os
import requests
from loguru import logger

class BraveSearchSkill:
    def __init__(self):
        self.api_key = os.getenv("BRAVE_SEARCH_API_KEY")
        self.base_url = "https://api.search.brave.com/res/v1/web/search"

    def search(self, query, count=5):
        if not self.api_key:
            logger.warning("⚠️ BRAVE_SEARCH_API_KEY não configurada.")
            return []

        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        }
        params = {"q": query, "count": count}

        try:
            response = requests.get(self.base_url, headers=headers, params=params)
            if response.status_status == 200:
                results = response.json().get("web", {}).get("results", [])
                return [f"{r['title']}: {r['url']}\n{r['description']}" for r in results]
            else:
                logger.error(f"Erro Brave Search: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Falha na busca Brave: {e}")
            return []
