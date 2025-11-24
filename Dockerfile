FROM python:3.12-slim

WORKDIR /app

# システム依存関係のインストール
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係のインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright (ブラウザ自動化) のインストール
RUN playwright install chromium
RUN playwright install-deps chromium

# アプリケーションコードをコピー
COPY . .

# デフォルトコマンド (bashシェルを起動)
CMD ["bash"]
