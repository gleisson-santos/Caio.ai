import os
from datetime import datetime, timezone
from supabase import create_client
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

class SchedulerSkill:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        if not url or not key:
            logger.error("❌ Credenciais Supabase ausentes no SchedulerSkill")
            self.supabase = None
        else:
            self.supabase = create_client(url, key)

    def schedule_task(self, description: str, scheduled_at_iso: str):
        """Agenda uma tarefa no Supabase."""
        if not self.supabase:
            return False, "Erro conexão DB"
        
        try:
            # Validar formato ISO
            datetime.fromisoformat(scheduled_at_iso)
            
            self.supabase.table("scheduled_tasks").insert({
                "description": description,
                "scheduled_at": scheduled_at_iso,
                "status": "pending"
            }).execute()
            return True, None
        except Exception as e:
            logger.error(f"Erro ao agendar: {e}")
            return False, str(e)

    def get_pending_tasks(self):
        """Retorna tarefas pendentes para execução imediata."""
        if not self.supabase:
            return []
            
        now = datetime.now(timezone.utc).isoformat()
        try:
            response = self.supabase.table("scheduled_tasks")\
                .select("*")\
                .eq("status", "pending")\
                .lte("scheduled_at", now)\
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Erro ao buscar tarefas: {e}")
            return []

    def find_tasks_smart(self, keyword=None, date_ref=None):
        """Busca inteligente: filtra por palavra-chave E/OU data."""
        if not self.supabase:
            return []
            
        try:
            # 1. Buscar TUDO que está pendente (Melhor filtrar em Python para complexidade de data)
            response = self.supabase.table("scheduled_tasks")\
                .select("*")\
                .eq("status", "pending")\
                .execute()
            all_tasks = response.data
            
            filtered = []
            for task in all_tasks:
                match_desc = True
                match_date = True
                
                # Check Descrição
                if keyword:
                    if keyword.lower() not in task['description'].lower():
                        match_desc = False
                
                # Check Data (Se date_ref for fornecida, ex: '03/02')
                if date_ref:
                    # date_ref pode vir como '03/02' ou '2026-02-03'
                    # task['scheduled_at'] é '2026-02-03T15:00:00+00:00'
                    task_date_iso = task['scheduled_at']
                    
                    # Tenta extrair dia/mês/ano da ISO
                    dt_task = datetime.fromisoformat(task_date_iso)
                    
                    # Normaliza date_ref para comparação simples
                    # Se date_ref for "03/02", checa se task dia=3 e mes=2
                    if "/" in date_ref:
                        parts = date_ref.split("/")
                        if len(parts) >= 2:
                            day, month = int(parts[0]), int(parts[1])
                            if dt_task.day != day or dt_task.month != month:
                                match_date = False
                    elif "-" in date_ref:
                         if date_ref not in task_date_iso:
                             match_date = False
                    
                if match_desc and match_date:
                    filtered.append(task)
                    
            return filtered

        except Exception as e:
            logger.error(f"Erro na busca inteligente: {e}")
            return []

    def cancel_task(self, task_id):
        """Cancela (remove) uma tarefa pelo ID."""
        try:
            # Opção 1: Deletar
            self.supabase.table("scheduled_tasks").delete().eq("id", task_id).execute()
            # Opção 2: Marcar como cancelled (melhor p/ histórico)
            # self.supabase.table("scheduled_tasks").update({"status": "cancelled"}).eq("id", task_id).execute()
            return True
        except Exception as e:
            logger.error(f"Erro ao cancelar tarefa: {e}")
            return False

    def get_future_tasks(self):
        """Retorna todas as tarefas agendadas futuras."""
        if not self.supabase:
            return []
            
        now = datetime.now(timezone.utc).isoformat()
        try:
            response = self.supabase.table("scheduled_tasks")\
                .select("*")\
                .eq("status", "pending")\
                .gt("scheduled_at", now)\
                .order("scheduled_at")\
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Erro ao buscar tarefas futuras: {e}")
            return []

    def mark_as_done(self, task_id):
        try:
            self.supabase.table("scheduled_tasks")\
                .update({"status": "done"})\
                .eq("id", task_id)\
                .execute()
        except Exception as e:
            logger.error(f"Erro ao concluir tarefa {task_id}: {e}")
