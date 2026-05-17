FROM nvidia/cuda:11.8-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    wget \
    gnupg2 \
    curl \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    x11-utils \
    x11-xserver-utils \
    xvfb \
    supervisor \
    tigervnc-standalone-server \
    novnc \
    python3.11 \
    python3.11-venv \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

RUN pip install playwright \
    && playwright install chromium \
    && playwright install-deps chromium

COPY requirements.txt .
RUN pip install -r requirements.txt

RUN useradd -m -u 1000 -s /bin/bash appuser

COPY --chown=1000:1000 . /home/appuser/award-search
WORKDIR /home/appuser/award-search

RUN mkdir -p /home/appuser/.cache/playwright \
    && chown -R 1000:1000 /home/appuser

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 6080 5900

CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]