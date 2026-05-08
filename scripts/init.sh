#!/bin/bash
# First-time setup helper

set -e

echo "🚀 Setting up ChatDoc..."

# Copy env if not exists
if [ ! -f .env ]; then
  cp .env.example .env
  echo "✅ Created .env from .env.example"
fi

# Generate JWT secret
JWT=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32)
sed -i "s/super_secret_jwt_key_change_in_production/$JWT/" .env
echo "✅ Generated JWT secret"

echo ""
echo "📋 Starting services..."
docker compose up -d postgres redis qdrant

echo "⏳ Waiting for services..."
sleep 5

echo ""
echo "✅ Done! Run: docker compose up"
echo ""
echo "   Chat:  http://localhost:3000"
echo "   Admin: http://localhost:3000/admin"
echo "   Docs:  http://localhost:8000/api/docs"
echo ""
echo "   Login: admin@example.com / admin123"
