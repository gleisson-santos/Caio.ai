#!/bin/bash

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "=================================================="
echo "   🦁 CAIO.AI - INSTALADOR AUTOMÁTICO (VPS/LINUX)"
echo "   Intelligence. Autonomy. Connection."
echo "=================================================="
echo -e "${NC}"

# 1. Verificar/Instalar Dependências de Sistema
echo -e "${GREEN}--> Verificando sistema...${NC}"
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip python3-venv git

# 2. Clonar Repositório
if [ -d "caio-agent" ]; then
    echo -e "${RED}Pasta 'caio-agent' já existe. Atualizando...${NC}"
    cd caio-agent
    git pull
else
    echo -e "${GREEN}--> Baixando o Caio...${NC}"
    git clone https://github.com/gleisson-santos/Caio.ai.git caio-agent
    cd caio-agent
fi

# Entrar na pasta correta (Repo raiz já contém o código)
# cd caio-stack (Removido pois o repo é flat)

# 3. Criar Ambiente Virtual (Venv)
echo -e "${GREEN}--> Criando ambiente virtual isolado...${NC}"
python3 -m venv venv
source venv/bin/activate

# 4. Instalar Dependências Python
echo -e "${GREEN}--> Instalando bibliotecas do Cérebro...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# 6. Criar Comando Global 'caio' (Wrapper robusto)
echo -e "${GREEN}--> Configurando comando 'caio'...${NC}"
INSTALL_DIR="$(pwd)"
WRAPPER_PATH="/usr/local/bin/caio"

# Remove link antigo se existir
if [ -L "$WRAPPER_PATH" ]; then
    sudo rm "$WRAPPER_PATH"
fi

# Cria script wrapper que força o CD para a pasta correta
echo "#!/bin/bash" | sudo tee "$WRAPPER_PATH" > /dev/null
echo "cd \"$INSTALL_DIR\"" | sudo tee -a "$WRAPPER_PATH" > /dev/null
echo "./start.sh" | sudo tee -a "$WRAPPER_PATH" > /dev/null
sudo chmod +x "$WRAPPER_PATH"

echo -e "${GREEN}"
echo "=================================================="
echo "   🦁 INSTALAÇÃO CONCLUÍDA COM SUCESSO!"
echo "   Agora você pode iniciar o agente de qualquer lugar digitando:"
echo "   caio"
echo "=================================================="
echo -e "${NC}"

# Iniciar o Wizard
python3 setup.py
