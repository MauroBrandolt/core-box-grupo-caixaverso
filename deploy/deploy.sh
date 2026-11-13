#!/usr/bin/env bash
set -Eeuo pipefail

cd /opt/core-box

: "${IMAGEM:?A referencia IMAGEM e obrigatoria}"

case "$IMAGEM" in
  *@sha256:*)
    ;;
  *)
    echo "ERRO: deploy recusado porque a imagem nao usa digest."
    exit 1
    ;;
esac

export IMAGEM

docker compose \
  --file docker-compose.prod.yml \
  config --quiet

docker compose \
  --file docker-compose.prod.yml \
  pull

docker compose \
  --file docker-compose.prod.yml \
  up --detach --remove-orphans

for tentativa in $(seq 1 30); do
  STATUS="$(
    docker inspect \
      --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}sem-healthcheck{{end}}' \
      core-box 2>/dev/null || true
  )"

  if [ "$STATUS" = "healthy" ]; then
    docker inspect \
      --format='Imagem implantada: {{.Config.Image}}' \
      core-box

    echo "Deploy concluido com saude."
    exit 0
  fi

  echo "Aguardando saude: tentativa $tentativa, status=$STATUS"
  sleep 4
done

docker compose \
  --file docker-compose.prod.yml \
  ps

docker logs core-box || true

echo "ERRO: aplicacao nao ficou saudavel."
exit 1
