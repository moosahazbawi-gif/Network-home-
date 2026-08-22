#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$ROOT_DIR"

python -m compileall backend/app

docker compose config >/dev/null
printf '%s
' "التحقق انتهى بنجاح."
