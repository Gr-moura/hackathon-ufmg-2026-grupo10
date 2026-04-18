#!/bin/bash
set -e

# Esperar o banco de dados ficar pronto
echo "Aguardando PostgreSQL..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "db" -U "enteros" -d "enteros" -c '\q'; do
  >&2 echo "Postgres indisponível - aguardando..."
  sleep 1
done

echo "Postgres pronto!"

# Habilitar a extensão pgvector diretamente no banco
echo "Habilitando extensão pgvector..."
PGPASSWORD=$POSTGRES_PASSWORD psql -h "db" -U "enteros" -d "enteros" -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Executar o comando original (migrações + uvicorn)
exec "$@"
