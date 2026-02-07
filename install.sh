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

# 5. Iniciar o Wizard de Configuração
echo -e "${BLUE}--> Iniciando Configuração Interativa...${NC}"
python3 setup.py

echo -e "${GREEN}"
echo "=================================================="
echo "   🦁 INSTALAÇÃO CONCLUÍDA COM SUCESSO!"
echo "   Para rodar o agente use:"
echo "   cd ~/caio-agent/caio-stack && source venv/bin/activate && python core/main.py"
echo "=================================================="
echo -e "${NC}"
