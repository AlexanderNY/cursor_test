#!/usr/bin/env bash
# Generates self-signed TLS certs for local / staging ui-edge.
# Production: replace with real certs (see docs/SSL_CERT_RENEWAL.md).
# Uses host openssl if available, otherwise docker image alpine/openssl.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CERTS="$ROOT/certs"

run_openssl() {
  if command -v openssl >/dev/null 2>&1; then
    openssl "$@"
    return
  fi
  docker run --rm -v "$CERTS:/certs" alpine/openssl "$@"
}

gen_site() {
  local site="$1"
  shift
  local dir="$CERTS/$site"
  mkdir -p "$dir"
  local key="$dir/privkey.pem"
  local crt="$dir/fullchain.pem"
  if [[ -f "$key" && -f "$crt" ]]; then
    echo "Skip $site (already has fullchain.pem + privkey.pem)"
    return
  fi
  local cn="$1"
  local san
  san=$(printf 'DNS:%s,' "$@" | sed 's/,$//')
  if command -v openssl >/dev/null 2>&1; then
    run_openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
      -keyout "$key" -out "$crt" \
      -subj "/CN=$cn" \
      -addext "subjectAltName=$san"
  else
    run_openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
      -keyout "/certs/$site/privkey.pem" -out "/certs/$site/fullchain.pem" \
      -subj "/CN=$cn" \
      -addext "subjectAltName=$san"
  fi
  echo "Created $site certs for: $*"
}

gen_site copyparse copyparse.ru www.copyparse.ru
gen_site 9to18 9to18.ru www.9to18.ru
echo "Done. Restart ui-edge after installing certs."
