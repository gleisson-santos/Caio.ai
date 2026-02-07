$ErrorActionPreference = "Stop"

function Write-Color($text, $color) {
    Write-Host $text -ForegroundColor $color
}

Write-Color "🦁 CAIO.AI - INSTALADOR WINDOWS (PowerShell)" "Cyan"
Write-Color "----------------------------------------" "White"

# 1. Verifica Python
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Color "❌ Erro: Python não encontrado! Instale Python 3.10+ do site oficial e tente novamente." "Red"
    Exit
} else {
    python --version
}

# 2. Clona ou Atualiza
$repoUrl = "https://github.com/gleisson-santos/Caio.ai.git"
$installDir = "$HOME\caio-agent"

if (Test-Path $installDir) {
    Write-Color "📂 Pasta 'caio-agent' já existe. Atualizando..." "Yellow"
    Set-Location $installDir
    git pull
} else {
    Write-Color "📦 Baixando Caio Agent..." "Green"
    git clone $repoUrl $installDir
    Set-Location $installDir
}

# 3. Entra na pasta do stack (Repo raiz já contém o código)
# Set-Location "$installDir\caio-stack"

# 4. Cria e Ativa VENV
Write-Color "🔧 Configurando ambiente virtual Python..." "Green"
if (!(Test-Path ".venv")) {
    python -m venv .venv
}
.\.venv\Scripts\Activate.ps1

# 5. Instala Deps
Write-Color "🧠 Instalando dependências..." "Green"
pip install --upgrade pip
pip install -r requirements.txt

# 6. Wizard
Write-Color "⚙️ Configuração Iniciada..." "Cyan"
python setup.py

Write-Color "✅ TUDO PRONTO!" "Green"
Write-Color "Para iniciar, abra um terminal e rode:" "White"
Write-Color "cd $installDir\caio-stack; .\.venv\Scripts\Activate.ps1; python core\main.py" "Cyan"
