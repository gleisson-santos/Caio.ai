import os
import sys
from datetime import datetime, timedelta

# Carregar variáveis ANTES de importar módulos que o usam
print(f"DEBUG CWD: {os.getcwd()}")
try:
    from dotenv import load_dotenv
    env_path = os.path.abspath(os.path.join(os.getcwd(), "../.env"))
    load_dotenv(dotenv_path=env_path)
except Exception as e:
    print(f"❌ Erro loading dotenv: {e}")

from supabase import create_client
import main  # Importar o modulo main
from memory import MemorySystem
from agent import CaioAgent

print("🚀 Iniciando Teste Completo (Versão API)...")

# Configurar Globais do main (Injection)
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")

if not url:
    print("❌ SUPABASE_URL não encontrada.")
    exit(1)

client = create_client(url, key)
main.supabase = client  # Injetar cliente no modulo main
main.brain_memory = MemorySystem()
main.caio_persona = CaioAgent()

try:
    print("1️⃣ Criando uma tarefa agendada para AGORA (Via API)...")
    
    # Data no passado (1 min atrás) em formato ISO
    past_time = (datetime.now() - timedelta(minutes=1)).isoformat()
    
    res = client.table("scheduled_tasks").insert({
        "description": "Reunião de Alinhamento do Projeto CaioStack",
        "scheduled_at": past_time,
        "status": "pending"
    }).execute()
    
    if res.data:
        print(f"   ✅ Tarefa Criada: {res.data[0]['id']}")
    else:
        print("   ⚠️ Tarefa criada mas sem retorno de dados.")

    print("\n2️⃣ Executando o Cérebro (check_schedule)...")
    print("   (Verifique seu Telegram agora!)")
    
    # Executa a função do main (que agora usa a API)
    main.check_schedule()
    
    print("\n✅ Teste Finalizado! Se recebeu a mensagem, o Caio está VIVO.")

except Exception as e:
    print(f"\n❌ Erro no teste: {e}")
    import traceback
    traceback.print_exc()
