from dotenv import load_dotenv
import os
from supabase import create_client

load_dotenv(dotenv_path="../.env")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")

if not url:
    print("❌ Sem variaveis de ambiente")
    exit(1)

client = create_client(url, key)

print("🔍 Verificando estrutura da tabela 'memories'...")

try:
    # Tenta inserir um dado dummy só pra ver o erro detalhado ou sucesso
    # Não vamos commitar de verdade se falhar
    res = client.table("memories").select("*").limit(1).execute()
    print("✅ Leitura da tabela funcionou!")
    if res.data:
        print(f"   Dados encontrados: {res.data}")
    else:
        print("   Tabela vazia (Normal).")
        
    print("\n🛠️ Tentando inspecionar colunas (Inserindo teste)...")
    res = client.table("memories").insert({
        "content": "Teste de estrutura",
        "metadata": {"source": "diagnostico"},
        # "embedding": [0.0] * 768 # Ignorando vetor por enquanto
    }).execute()
    print("✅ Inserção com col 'metadata' funcionou!")
    
except Exception as e:
    print(f"\n❌ ERRO DETALHADO: {e}")
    # Se o erro mencionar 'metadata', confirma que o cache tá velho ou a coluna nao existe
