#!/bin/bash
set -e

POSTGRES_HOST="${POSTGRES_HOST:-db}"
POSTGRES_USER="${POSTGRES_USER:-enteros}"
POSTGRES_DB="${POSTGRES_DB:-enteros}"

echo "Aguardando PostgreSQL..."
until PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q'; do
  >&2 echo "Postgres indisponivel - aguardando..."
  sleep 1
done

echo "Postgres pronto!"
echo "Habilitando extensao pgvector..."
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "CREATE EXTENSION IF NOT EXISTS vector;"

exec "$@"
