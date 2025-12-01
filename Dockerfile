# ========================
# Image de base
# ========================
FROM python:3.12-slim

# ========================
# Dépendances système pour Chromium / Playwright
# ========================
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libnss3 \
    libxss1 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    libglib2.0-0 \
    libexpat1 \
    libxcb1 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libpango-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    libdbus-1-3 \
    libnspr4 \
    libsmime3 \
    libnssutil3 \
    libxkbcommon0 \
 && rm -rf /var/lib/apt/lists/*

# ========================
# Créer le dossier de travail
# ========================
WORKDIR /app

# ========================
# Copier les fichiers Python
# ========================
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# ========================
# Lancer le bot
# ========================
CMD ["python", "bot.py"]
