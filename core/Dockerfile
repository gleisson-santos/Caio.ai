FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema necessárias para compilação (se houver)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro para aproveitar cache do Docker
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copiar o resto do código
COPY . .

# Comando padrão (será substituído pelo loop principal)
CMD ["python", "main.py"]
