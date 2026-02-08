import schedule
import time
import threading
from loguru import logger
import asyncio

class SchedulerSkill:
    def __init__(self, send_message_async_callback):
        self.send_callback = send_message_async_callback
        self.running = True
        self.loop = None 
        
    def start(self, loop):
        self.loop = loop
        # Cria task asyncio ao invés de Thread
        loop.create_task(self._async_loop())
        logger.info("⏰ Scheduler System (Async Native) Iniciado")

    async def _async_loop(self):
        """Loop principal do agendador rodando dentro do asyncio."""
        while self.running:
            # schedule.run_pending() é rápido o suficiente para não bloquear
            schedule.run_pending()
            await asyncio.sleep(1)

    def _trigger(self, chat_id, message):
        """Dispara o callback. Como já estamos no loop, basta criar task."""
        if self.loop and self.send_callback:
            clean_msg = f"🔔 {message}"
            # Não precisa de threadsafe, já estamos no loop
            self.loop.create_task(self.send_callback(chat_id, clean_msg))

    def set_reminder(self, chat_id, minutes, message):
        minutes = int(minutes)
        def job():
            self._trigger(chat_id, message)
            return schedule.CancelJob
        
        schedule.every(minutes).minutes.do(job)
        return f"⏰ Combinado! Daqui a {minutes} min te aviso."

    def set_daily(self, chat_id, time_str, message):
        def job():
            self._trigger(chat_id, message)
        
        schedule.every().day.at(time_str).do(job)
        return f"📅 Agendado! Todo dia às {time_str}: '{message}'"
