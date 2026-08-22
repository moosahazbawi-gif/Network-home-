#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ENV_FILE="$ROOT_DIR/.env"
EXAMPLE_FILE="$ROOT_DIR/.env.example"

if [ ! -f "$EXAMPLE_FILE" ]; then
  printf '%s
' "ملف .env.example غير موجود."
  exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
  cp "$EXAMPLE_FILE" "$ENV_FILE"
  SECRET=$(openssl rand -hex 32)
  POSTGRES_PASSWORD=$(openssl rand -hex 24)
  sed -i "s/^SECRET_KEY=.*/SECRET_KEY=$SECRET/" "$ENV_FILE"
  sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$POSTGRES_PASSWORD/" "$ENV_FILE"
  sed -i "s#^DATABASE_URL=.*#DATABASE_URL=postgresql+psycopg2://cloudbell:$POSTGRES_PASSWORD@postgres:5432/cloudbell#" "$ENV_FILE"
  printf '%s
' "تم إنشاء .env. عدل BOOTSTRAP_ADMIN_EMAIL و BOOTSTRAP_ADMIN_PASSWORD قبل التشغيل."
else
  printf '%s
' ".env موجود بالفعل."
fi

printf '%s
' "الخطوة التالية: راجع .env ثم شغّل: docker compose up -d --build"
