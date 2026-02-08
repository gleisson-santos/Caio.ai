import os
import json
import subprocess
import sys

def colored_print(text, color_code):
    if sys.platform == "win32":
        try:
            print(text)
        except:
            print(text)
    else:
        print(f"\033[{color_code}m{text}\033[0m")

def print_header():
    print("\n" + "="*50)
    print("🦁  INSTALADOR DO CAIO.AI  🦁")
    print("   Intelligence. Autonomy. Connection.")
    print("="*50 + "\n")

def check_python_version():
    if sys.version_info < (3, 10):
        print("❌ Erro: Python 3.10 ou superior é necessário.")
        sys.exit(1)
    print("✅ Python versão OK.")

def install_dependencies():
    print("\n📦 Instalando dependências (pode demorar um pouco)...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependências instaladas!")
    except subprocess.CalledProcessError:
        print("❌ Erro ao instalar dependências. Verifique o pip.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado na instalação: {e}")
        sys.exit(1)

def setup_env():
    # Verifica se o .env já existe na raiz ou em core/
    env_exists = os.path.exists(".env") or os.path.exists(os.path.join("core", ".env"))
    
    if env_exists:
        print("\n🔑  CONFIGURAÇÃO DE SEGURANÇA")
        print("⚠️ Arquivo .env detectado. Deseja reconfigurar suas chaves?")
        reconfig = input("Pressione 's' para reconfigurar ou qualquer outra tecla para pular: ").lower()
        if reconfig != 's':
            print("✅ Usando configurações existentes. Pulando setup...")
            return

    print("\n🔑  CONFIGURAÇÃO DE SEGURANÇA")
    print("Vamos configurar suas chaves. Se não tiver alguma, deixe em branco.\n")
    
    telegram_token = input("1. Digite o TELEGRAM_BOT_TOKEN (BotFather): ").strip()
    google_key = input("2. Digite a GOOGLE_API_KEY (Google AI Studio): ").strip()
    groq_key = input("3. Digite a GROQ_API_KEY (Groq Console): ").strip()
    agent_name = input("4. Nome do seu Agente (padrão 'Caio'): ").strip() or "Caio"
    user_id = input("5. Seu ID numérico do Telegram (para segurança): ").strip()

    env_content = f"""TELEGRAM_BOT_TOKEN={telegram_token}
GOOGLE_API_KEY={google_key}
GROQ_API_KEY={groq_key}
AGENT_NAME={agent_name}
ALLOWED_USER_ID={user_id}
"""
    
    try:
        with open(".env", "w", encoding='utf-8') as f:
            f.write(env_content)
    except Exception as e:
        print(f"⚠️ Erro ao escrever .env na raiz: {e}")
    
    if not os.path.exists("core"):
        os.makedirs("core")
        
    try:
        with open(os.path.join("core", ".env"), "w", encoding='utf-8') as f:
            f.write(env_content)
        print("\n✅ Arquivo .env criado com sucesso!")
    except Exception as e:
        print(f"❌ Erro crítico ao salvar chaves: {e}")
        sys.exit(1)

def init_brain():
    print("\n🧠 Inicializando a memória do Agente...")
    brain_path = os.path.join("core", "brain_data.json")
    
    if not os.path.exists(brain_path):
        initial_memory = {
            "profile": {},
            "episodic": []
        }
        try:
            with open(brain_path, "w", encoding='utf-8') as f:
                json.dump(initial_memory, f, ensure_ascii=False, indent=4)
            print("✅ Memória nova criada (brain_data.json).")
        except Exception as e:
             print(f"❌ Erro ao criar memória: {e}")
    else:
        print("⚠️ Memória antiga encontrada. Mantendo dados existentes.")

def main():
    print_header()
    check_python_version()
    
    # Tenta instalar dependências automaticamente se não houver .env (primeira instalação)
    if not os.path.exists(".env"):
        install_dependencies()
        
    setup_env()
    init_brain()
    
    print("\n" + "="*50)
    print("✅ INSTALAÇÃO CONCLUÍDA!")
    print("="*50 + "\n")
    
    start_now = input("🦁 Deseja iniciar o Agente agora? (S/n): ").strip().lower()
    
    if start_now == '' or start_now == 's':
        print("\n🚀 Iniciando o Caio... (Pressione Ctrl+C para parar)\n")
        try:
            subprocess.run([sys.executable, "core/main.py"])
        except KeyboardInterrupt:
            print("\n👋 Agente parado. Até logo!")
    else:
        print("\nTudo bem! Para iniciar depois, basta rodar:")
        if sys.platform == "win32":
            print("   start.bat")
        else:
            print("   ./start.sh")

if __name__ == "__main__":
    main()
