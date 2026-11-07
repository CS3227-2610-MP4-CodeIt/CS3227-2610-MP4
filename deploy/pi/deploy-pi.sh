#!/usr/bin/env bash
# Fixed Pi staging command. In SSH mode accepts only: staging <full-master-sha>.
set -Eeuo pipefail

REPO_DIR="${PI_REPO_DIR:-$HOME/Documents/code-projs/CodeIt}"
CONFIG_DIR="${PI_CONFIG_DIR:-$HOME/.config/codeit-staging}"
RELEASE_DIR="$CONFIG_DIR/releases"
STATE_DIR="$CONFIG_DIR/state"
COMPOSE_ENV="$CONFIG_DIR/compose.env"
PROJECT="codeit-staging"
HEALTH_URL="http://127.0.0.1:8001/api/health"
HEALTH_ATTEMPTS=60
HEALTH_DELAY=2

die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
say() { printf '%s\n' "$*"; }

if [[ -n "${SSH_ORIGINAL_COMMAND:-}" ]]; then
    read -r -a remote_args <<<"$SSH_ORIGINAL_COMMAND"
    [[ ${#remote_args[@]} -eq 2 && "${remote_args[0]}" == staging ]] \
        || die "Only the fixed staging command is allowed."
    TARGET_SHA="${remote_args[1]}"
    [[ "$TARGET_SHA" =~ ^[0-9a-fA-F]{40}$ ]] || die "Deploy requires a full commit SHA."
else
    [[ $# -eq 1 ]] || die "Usage: $0 <full-master-sha>"
    TARGET_SHA="$1"
    [[ "$TARGET_SHA" =~ ^[0-9a-fA-F]{40}$ ]] || die "Deploy requires a full commit SHA."
fi
TARGET_SHA="$(printf '%s' "$TARGET_SHA" | tr 'A-F' 'a-f')"

command -v docker >/dev/null || die "Docker is required."
command -v git >/dev/null || die "Git is required."
command -v flock >/dev/null || die "flock is required."
[[ -f "$COMPOSE_ENV" ]] || die "Pi Compose environment is missing; run bootstrap-pi.sh first."
git -C "$REPO_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "App checkout not found."

install -d -m 700 "$RELEASE_DIR" "$STATE_DIR"
exec 9>"$STATE_DIR/deploy.lock"
flock -n 9 || die "Another Pi deployment is already running."

git -C "$REPO_DIR" fetch --quiet origin master
LATEST_SHA="$(git -C "$REPO_DIR" rev-parse --verify origin/master^{commit})"
[[ "$TARGET_SHA" == "$LATEST_SHA" ]] || die "Refusing stale deployment; master is now $LATEST_SHA."
git -C "$REPO_DIR" cat-file -e "$TARGET_SHA^{commit}" 2>/dev/null || die "Commit is not available locally."

PREVIOUS_SHA=""
[[ -f "$STATE_DIR/current-sha" ]] && PREVIOUS_SHA="$(cat "$STATE_DIR/current-sha")"
if [[ -z "$PREVIOUS_SHA" ]]; then
    PREVIOUS_SHA="$(git -C "$REPO_DIR" rev-parse --verify HEAD^{commit})"
fi
[[ "$PREVIOUS_SHA" =~ ^[0-9a-f]{40}$ ]] || die "Recorded previous deployment SHA is invalid."

make_release() {
    local sha="$1" path="$RELEASE_DIR/$1"
    if [[ ! -d "$path" ]]; then
        git -C "$REPO_DIR" worktree add --detach "$path" "$sha" >/dev/null
    fi
    [[ -f "$path/docker-compose.yml" ]] || die "Commit $sha is missing docker-compose.yml."
    ln -sfn "$REPO_DIR/backend/.env" "$path/backend/.env"
    ln -sfn "$REPO_DIR/code-execution/.env" "$path/code-execution/.env"
}

compose() {
    local source="$1" overlay="$2"
    docker compose --project-name "$PROJECT" --env-file "$COMPOSE_ENV" \
        --file "$source/docker-compose.yml" --file "$overlay/docker-compose.pi.yml" "${@:3}"
}

wait_healthy() {
    local n
    for ((n = 1; n <= HEALTH_ATTEMPTS; n++)); do
        if python3 - "$HEALTH_URL" <<'PY' >/dev/null 2>&1 \
            && [[ "$(docker inspect codeit-staging-code-executor-1 --format '{{.State.Health.Status}}' 2>/dev/null || true)" == healthy ]] \
            && docker exec codeit-staging-backend-1 python -c \
                'import httpx; r=httpx.get("https://executor-https:8443/health", verify="/run/executor-ca/ca.crt", timeout=3); r.raise_for_status()' \
                >/dev/null 2>&1
import sys
import urllib.request
try:
    with urllib.request.urlopen(sys.argv[1], timeout=3) as response:
        raise SystemExit(0 if response.status == 200 else 1)
except Exception:
    raise SystemExit(1)
PY
        then
            return 0
        fi
        sleep "$HEALTH_DELAY"
    done
    return 1
}

deploy_source() {
    local sha="$1" overlay_sha="$2" source="$RELEASE_DIR/$1" overlay="$RELEASE_DIR/$2"
    make_release "$sha"
    [[ -f "$overlay/docker-compose.pi.yml" && -f "$overlay/deploy/pi/Caddyfile" ]] \
        || die "Commit $overlay_sha is missing the Pi staging configuration."
    install -m 644 "$overlay/deploy/pi/Caddyfile" "$CONFIG_DIR/Caddyfile"
    say "Building backend and executor for $sha."
    compose "$source" "$overlay" build backend code-executor || return 1
    compose "$source" "$overlay" pull executor-https || return 1
    compose "$source" "$overlay" config --quiet || return 1

    # SQLite's online backup API provides a consistent snapshot while the old
    # backend is still serving requests. Keep it in the persistent data volume.
    if docker inspect codeit-staging-backend-1 >/dev/null 2>&1; then
        docker exec codeit-staging-backend-1 python -c \
          'import sqlite3,sys; src=sqlite3.connect("/data/app.db"); dst=sqlite3.connect("/data/predeploy-"+sys.argv[1]+".db"); src.backup(dst); dst.close(); src.close()' \
          "$sha" || return 1
    fi

    say "Starting Pi backend, HTTPS executor proxy, and executor."
    compose "$source" "$overlay" up --detach --no-deps backend code-executor executor-https || return 1
    if wait_healthy; then
        printf '%s\n' "$sha" >"$STATE_DIR/current-sha.tmp"
        chmod 600 "$STATE_DIR/current-sha.tmp"
        mv "$STATE_DIR/current-sha.tmp" "$STATE_DIR/current-sha"
        say "Health check passed for $sha."
        return 0
    fi
    return 1
}

deploy_source "$TARGET_SHA" "$TARGET_SHA" && exit 0
say "Deployment of $TARGET_SHA failed its build or health check."

if [[ "$PREVIOUS_SHA" != "$TARGET_SHA" ]]; then
    say "Rolling back to $PREVIOUS_SHA."
    if deploy_source "$PREVIOUS_SHA" "$TARGET_SHA"; then
        say "Rollback succeeded; the previous app is serving again."
        exit 1
    fi
    say "Rollback did not pass its health check. Inspect Docker logs on the Pi." >&2
else
    say "No previous deployment is recorded. The original container state was left for inspection." >&2
fi
exit 1
