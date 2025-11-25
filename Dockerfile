# Playwright公式イメージを使用（Chromiumプリインストール済み）
# これにより初回起動が大幅に高速化される
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

WORKDIR /app

# Python依存関係のインストール（キャッシュ活用のため先にコピー）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# 環境変数設定
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# デフォルトコマンド (bashシェルを起動)
CMD ["bash"]
