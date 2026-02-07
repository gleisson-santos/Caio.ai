import os
import sys
import time
import subprocess
import signal

# Cores
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
CYAN = "\033[36m"

PID_FILE = "caio.pid"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    clear_screen()
    print(f"{CYAN}{BOLD}")
    print("   🦁 CAIO.AI - COMMAND CENTER")
    print("   Intelligence. Autonomy. Connection.")
    print(f"======================================={RESET}")

def get_status():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            # Check if running
            os.kill(pid, 0)
            return f"{GREEN}ONLINE (PID: {pid}){RESET}"
        except (OSError, ValueError):
            os.remove(PID_FILE)
    return f"{RED}OFFLINE{RESET}"

def start_agent():
    print(f"\n{GREEN}🚀 Iniciando o Caio...{RESET}")
    # Rodar direto (Foreground) para ver logs na hora, ou nohup para background?
    # Vamos rodar em foreground por padrão para simplicidade, igual ao 'npm run dev'
    try:
        subprocess.run([sys.executable, "core/main.py"])
    except KeyboardInterrupt:
        print(f"\n{YELLOW}👋 Parando...{RESET}")

def view_logs():
    print(f"\n{BLUE}📜 Exibindo logs (Ctrl+C para sair)...{RESET}")
    if os.path.exists("logs/caio.log"):
        # Tail -f
        if os.name == 'nt':
             os.system("type logs\\caio.log")
        else:
             os.system("tail -f logs/caio.log")
    else:
        print(f"{YELLOW}⚠️ Nenhum arquivo de log encontrado.{RESET}")
        input("Pressione Enter...")

def stop_agent():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
            os.remove(PID_FILE)
            print(f"{RED}🛑 Agente parado com sucesso.{RESET}")
        except Exception as e:
            print(f"{RED}Erro ao parar: {e}{RESET}")
            if os.path.exists(PID_FILE): os.remove(PID_FILE)
    else:
        print(f"{YELLOW}⚠️ O agente não parece estar rodando.{RESET}")
    time.sleep(1)

def update_agent():
    print(f"\n{BLUE}⬇️ Verificando atualizações (Git)...{RESET}")
    os.system("git pull")
    print(f"{GREEN}✅ Atualizado!{RESET}")
    input("Pressione Enter...")

def main_menu():
    while True:
        print_header()
        print(f"STATUS: {get_status()}")
        print("\n[1] 🚀 Iniciar Agente (Foreground)")
        print("[2] 🧠 Configurar Chaves (.env)")
        print("[3] ⬇️ Atualizar (Git Pull)")
        print("[0] 🚪 Sair")
        
        choice = input(f"\n{CYAN}caio > {RESET}")
        
        if choice == '1':
            start_agent()
        elif choice == '2':
            subprocess.run([sys.executable, "setup.py"])
            input("\nPressione Enter...")
        elif choice == '3':
            update_agent()
        elif choice == '0':
            print("Até logo!")
            sys.exit(0)
        else:
            pass

if __name__ == "__main__":
    main_menu()
