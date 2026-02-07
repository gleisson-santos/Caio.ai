#!/bin/bash
# Script simples para iniciar o Caio

# Detecta onde está o script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Ativa o venv se existir
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Inicia o agente
python3 core/main.py
