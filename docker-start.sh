#!/bin/bash
# Docker環境起動スクリプト (WSL/Linux用)

set -e

echo "🐳 Keibabook Docker環境を起動します..."

# プロジェクトディレクトリに移動
cd "$(dirname "$0")"

# Dockerイメージが存在しない場合はビルド
if ! docker images | grep -q "keibabook-dev"; then
    echo "📦 Dockerイメージをビルドしています..."
    docker-compose build
fi

# コンテナを起動
echo "🚀 コンテナを起動しています..."
docker-compose up -d

# コンテナの状態を確認
if docker-compose ps | grep -q "Up"; then
    echo "✅ コンテナが起動しました！"
    echo ""
    echo "📝 次のコマンドでコンテナに入れます:"
    echo "   docker-compose exec app bash"
    echo ""
    echo "🛑 終了する場合:"
    echo "   docker-compose down"
    echo ""
    
    # 自動的にコンテナに入る
    read -p "コンテナに入りますか? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose exec app bash
    fi
else
    echo "❌ コンテナの起動に失敗しました"
    docker-compose logs
    exit 1
fi
