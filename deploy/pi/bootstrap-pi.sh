#!/usr/bin/env bash
# One-time Pi staging setup. Keeps existing production .env files unchanged.
set -Eeuo pipefail

REPO_DIR="${PI_REPO_DIR:-$HOME/Documents/code-projs/CodeIt}"
CONFIG_DIR="${PI_CONFIG_DIR:-$HOME/.config/codeit-staging}"
TLS_DIR="$CONFIG_DIR/tls"
COMPOSE_ENV="$CONFIG_DIR/compose.env"

die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

[[ -d "$REPO_DIR/.git" ]] || die "CodeIt checkout not found at $REPO_DIR"
[[ -f "$REPO_DIR/backend/.env" ]] || die "Existing backend/.env is missing"
[[ -f "$REPO_DIR/code-execution/.env" ]] || die "Existing code-execution/.env is missing"
command -v openssl >/dev/null || die "openssl is required"
command -v python3 >/dev/null || die "python3 is required"

install -d -m 700 "$CONFIG_DIR" "$TLS_DIR"

if [[ ! -s "$TLS_DIR/ca.crt" && ! -e "$TLS_DIR/ca.key" ]]; then
    openssl req -x509 -newkey rsa:3072 -nodes \
        -keyout "$TLS_DIR/ca.key" -out "$TLS_DIR/ca.crt" -days 3650 \
        -subj "/CN=CodeIt Pi staging executor CA" \
        -addext "basicConstraints=critical,CA:TRUE,pathlen:0" \
        -addext "keyUsage=critical,keyCertSign,cRLSign"
elif [[ ! -s "$TLS_DIR/ca.crt" || ! -s "$TLS_DIR/ca.key" ]]; then
    die "Only one executor CA file exists; repair the TLS directory before continuing"
fi

if [[ ! -s "$TLS_DIR/executor.crt" && ! -e "$TLS_DIR/executor.key" ]]; then
    openssl req -newkey rsa:2048 -nodes \
        -keyout "$TLS_DIR/executor.key" -out "$TLS_DIR/executor.csr" \
        -subj "/CN=executor-https"
    cat >"$TLS_DIR/executor.ext" <<'EOF'
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=DNS:executor-https
EOF
    openssl x509 -req -in "$TLS_DIR/executor.csr" \
        -CA "$TLS_DIR/ca.crt" -CAkey "$TLS_DIR/ca.key" -CAcreateserial \
        -out "$TLS_DIR/executor.crt" -days 825 -sha256 \
        -extfile "$TLS_DIR/executor.ext"
elif [[ ! -s "$TLS_DIR/executor.crt" || ! -s "$TLS_DIR/executor.key" ]]; then
    die "Only one executor certificate file exists; repair the TLS directory before continuing"
fi

chmod 600 "$TLS_DIR/ca.key" "$TLS_DIR/executor.key"
chmod 640 "$TLS_DIR/executor.key"
chmod 644 "$TLS_DIR/ca.crt" "$TLS_DIR/executor.crt"
rm -f "$TLS_DIR/executor.csr" "$TLS_DIR/executor.ext" "$TLS_DIR/ca.srl"

PI_EXECUTOR_TOKEN="$(python3 - "$COMPOSE_ENV" <<'PY'
import secrets
import sys
from pathlib import Path

path = Path(sys.argv[1])
if path.exists():
    for line in path.read_text().splitlines():
        if line.startswith("PI_EXECUTOR_TOKEN="):
            value = line.split("=", 1)[1]
            if value:
                print(value)
                raise SystemExit(0)
print(secrets.token_urlsafe(48))
PY
)"

cat >"$COMPOSE_ENV" <<EOF
MP4_BACKEND_ENV_FILE=$REPO_DIR/backend/.env
MP4_EXECUTOR_ENV_FILE=$REPO_DIR/code-execution/.env
MP4_BACKEND_BIND_ADDRESS=127.0.0.1
MP4_BACKEND_PUBLISHED_PORT=8001
PI_EXECUTOR_TLS_DIR=$TLS_DIR
PI_CADDYFILE=$CONFIG_DIR/Caddyfile
PI_CADDY_UID=$(id -u)
PI_CADDY_GID=$(id -g)
PI_EXECUTOR_TOKEN=$PI_EXECUTOR_TOKEN
EOF
unset PI_EXECUTOR_TOKEN
chmod 600 "$COMPOSE_ENV"

printf 'Pi staging configuration prepared at %s. Existing production env files were left unchanged.\n' "$CONFIG_DIR"
