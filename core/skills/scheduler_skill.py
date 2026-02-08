import schedule
import time
import threading
from loguru import logger
import asyncio

class SchedulerSkill:
    def __init__(self, send_message_async_callback):
        """
        :param send_message_async_callback: Função async que aceita (chat_id, text)
        """
        self.send_callback = send_message_async_callback
        self.running = True
        self.loop = None # Loop do asyncio onde o bot roda
        
        # Inicia loop do scheduler em thread separada
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.daemon = True
        
    def start(self, loop):
        self.loop = loop
        self.thread.start()
        logger.info("⏰ Scheduler System (Watchdog) Iniciado")

    def _run_loop(self):
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def _trigger(self, chat_id, message):
        """Chamado pelo schedule (thread secundária). Precisa agendar no loop principal."""
        if self.loop and self.send_callback:
            logger.info(f"⏰ Disparando Alerta para {chat_id}")
            # Thread-safe call to async loop
            asyncio.run_coroutine_threadsafe(
                self.send_callback(chat_id, f"🔔 **LEMBRETE:** {message}"), 
                self.loop
            )

    def set_reminder(self, chat_id, minutes, message):
        """Agenda um lembrete único (One-Shot)."""
        minutes = int(minutes)
        
        def job():
            self._trigger(chat_id, message)
            return schedule.CancelJob # Executa uma vez e morre

        schedule.every(minutes).minutes.do(job)
        return f"⏰ Combinado! Daqui a {minutes} minutos eu te aviso sobre: '{message}'"

    def set_daily(self, chat_id, time_str, message):
        """Agenda algo diário. Ex: '09:00'."""
        def job():
            self._trigger(chat_id, message)
        
        schedule.every().day.at(time_str).do(job)
        return f"📅 Agendado! Todo dia às {time_str}: '{message}'"
