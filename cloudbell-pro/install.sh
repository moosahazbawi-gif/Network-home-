#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ENV_FILE="$ROOT_DIR/.env"
EXAMPLE_FILE="$ROOT_DIR/.env.example"

if [ ! -f "$EXAMPLE_FILE" ]; then
  printf '%s\n' "خطا: فایل .env.example موجود نیست."
  exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
  cp "$EXAMPLE_FILE" "$ENV_FILE"
  
  # تولید رمزهای تصادفی
  SECRET=$(openssl rand -hex 32)
  POSTGRES_PASSWORD=$(openssl rand -hex 24)
  BOOTSTRAP_ADMIN_PASSWORD=$(openssl rand -hex 24)
  
  # اعمال تغییرات در فایل .env
  # الگو: s/^کلید=.*/کلید=مقدار جدید/
  sed -i "s/^SECRET_KEY=.*/SECRET_KEY=$SECRET/" "$ENV_FILE"
  sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$POSTGRES_PASSWORD/" "$ENV_FILE"
  sed -i "s/^BOOTSTRAP_ADMIN_PASSWORD=.*/BOOTSTRAP_ADMIN_PASSWORD=$BOOTSTRAP_ADMIN_PASSWORD/" "$ENV_FILE"
  
  # برای آدرس دیتابیس چون کاراکتر / دارد، از جداکننده # استفاده می‌کنیم
  sed -i "s#^DATABASE_URL=.*#DATABASE_URL=postgresql://user:password@db:5432/dbname#" "$ENV_FILE"
  
  printf '%s\n' "فایل .env ساخته شد. لطفاً BOOTSTRAP_ADMIN_EMAIL را قبل از اجرا چک کن."
else
  printf '%s\n' ".env از قبل موجود است."
fi

printf '%s\n' "آماده برای اجرا: docker compose up -d --build"
