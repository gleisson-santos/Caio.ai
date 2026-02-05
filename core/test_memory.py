from memory import MemorySystem
from dotenv import load_dotenv
import os

# Carregar variáveis
load_dotenv(dotenv_path="../.env")

brain = MemorySystem()

# 1. Simular salvar uma emoção/fato
print("\n📝 Teste 1: Salvando memórias...")
fatos = [
    "O usuário prefere reuniões apenas após as 10 da manhã.",
    "O usuário sente ansiedade quando tem muitos emails não lidos.",
    "O usuário está focado no projeto CaioStack e quer terminar hoje."
]

for fato in fatos:
    brain.store(fato, source="test_script", importance=5)

# 2. Simular recuperar contexto
print("\n🔎 Teste 2: Buscando contexto...")
queries = [
    "Marcar reunião as 8 da manhã",
    "Estou com a caixa de entrada cheia",
    "Qual o foco de hoje?"
]

for q in queries:
    print(f"\n🧠 Pergunta do Agente: '{q}'")
    contexto = brain.recall(q)
    for m in contexto:
        print(f"   └── 💡 Lembrei: {m['content']} (Sim: {m['similarity']})")

print("\n✅ Teste concluído!")
