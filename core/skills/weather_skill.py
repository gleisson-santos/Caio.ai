import requests
from loguru import logger

class WeatherSkill:
    def __init__(self, default_city="Salvador"):
        self.default_city = default_city

    def get_current_weather(self, city=None):
        """Pega o clima atual simples usando wttr.in"""
        target_city = city if city else self.default_city
        try:
            # Formato 3: City: Condition Temp
            # Ex: Salvador: ⛅️ +30°C
            url = f"https://wttr.in/{target_city}?format=%l:+%c+%t"
            response = requests.get(url)
            if response.status_code == 200:
                return response.text.strip()
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar clima: {e}")
            return None

    def get_temperature_int(self, city=None):
        """Retorna apenas o valor inteiro da temperatura para lógica."""
        data = self.get_current_weather(city)
        if data:
            # Tenta extrair numero "Salvador: ⛅️ +30°C" -> 30
            try:
                # Basic string manipulation
                # Find + or - followed by digits
                import re
                match = re.search(r'([+-]?\d+)°C', data)
                if match:
                    return int(match.group(1))
            except:
                pass
        return None
