#!/usr/bin/env bash
# Fixed Pi release command. In SSH mode accepts only: staging <full-master-sha>.
set -Eeuo pipefail

REPO_DIR="${PI_REPO_DIR:-$HOME/Documents/code-projs/CodeIt}"
CONFIG_DIR="${PI_CONFIG_DIR:-$HOME/.config/codeit-staging}"
RELEASE_DIR="$CONFIG_DIR/releases"
STATE_DIR="$CONFIG_DIR/state"
REPORT_DIR="$CONFIG_DIR/reports"
COMPOSE_ENV="$CONFIG_DIR/compose.env"
STAGING_PROJECT="codeit-staging"
PRODUCTION_PROJECT="codeit"
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

install -d -m 700 "$RELEASE_DIR" "$STATE_DIR" "$REPORT_DIR"
rm -f "$REPORT_DIR/$TARGET_SHA-promotion.md"
exec 9>"$STATE_DIR/deploy.lock"
flock -n 9 || die "Another Pi deployment is already running."

git -C "$REPO_DIR" fetch --quiet origin master
LATEST_SHA="$(git -C "$REPO_DIR" rev-parse --verify origin/master^{commit})"
[[ "$TARGET_SHA" == "$LATEST_SHA" ]] || die "Refusing stale deployment; master is now $LATEST_SHA."
git -C "$REPO_DIR" cat-file -e "$TARGET_SHA^{commit}" 2>/dev/null || die "Commit is not available locally."

make_release() {
    local sha="$1" path="$RELEASE_DIR/$1"
    if [[ ! -d "$path" ]]; then
        git -C "$REPO_DIR" worktree add --detach "$path" "$sha" >/dev/null
    fi
    [[ -f "$path/docker-compose.yml" ]] || die "Commit $sha is missing docker-compose.yml."
    ln -sfn "$REPO_DIR/backend/.env" "$path/backend/.env"
    ln -sfn "$REPO_DIR/code-execution/.env" "$path/code-execution/.env"
}

staging_compose() {
    local source="$1" overlay="$2"
    docker compose --project-name "$STAGING_PROJECT" --env-file "$COMPOSE_ENV" \
        --file "$source/docker-compose.yml" --file "$overlay/docker-compose.pi.yml" "${@:3}"
}

production_compose() {
    local source="$1"
    MP4_BACKEND_BIND_ADDRESS=0.0.0.0 MP4_BACKEND_PUBLISHED_PORT=8000 \
        docker compose --project-name "$PRODUCTION_PROJECT" --env-file "$COMPOSE_ENV" \
            --file "$source/docker-compose.yml" "${@:2}"
}

wait_healthy() {
    local target="$1" n health_url backend_container executor_container
    if [[ "$target" == staging ]]; then
        health_url="http://127.0.0.1:8001/api/health"
        backend_container="codeit-staging-backend-1"
        executor_container="codeit-staging-code-executor-1"
    else
        health_url="http://127.0.0.1:8000/api/health"
        backend_container="codeit-backend-1"
        executor_container="codeit-code-executor-1"
    fi
    for ((n = 1; n <= HEALTH_ATTEMPTS; n++)); do
        if python3 -c 'import sys,urllib.request; r=urllib.request.urlopen(sys.argv[1], timeout=3); sys.exit(0 if r.status == 200 else 1)' "$health_url" >/dev/null 2>&1 \
            && [[ "$(docker inspect "$executor_container" --format '{{.State.Status}}' 2>/dev/null || true)" == running ]] \
            && docker exec "$backend_container" python -c \
                'import sys,httpx; stage=sys.argv[1] == "staging"; url="https://executor-https:8443/health" if stage else "http://code-executor:8001/health"; verify="/run/executor-ca/ca.crt" if stage else True; r=httpx.get(url, verify=verify, timeout=3); r.raise_for_status()' \
                "$target" >/dev/null 2>&1
        then
            if [[ "$target" != staging ]] || \
                [[ "$(docker inspect "$executor_container" --format '{{.State.Health.Status}}' 2>/dev/null || true)" == healthy ]]; then
                return 0
            fi
        fi
        sleep "$HEALTH_DELAY"
    done
    return 1
}

write_report() {
    local status="$1" staging="$2" production="$3" report="$REPORT_DIR/$TARGET_SHA-promotion.md"
    cat >"$report" <<EOF
# Pi deployment report

- Commit: \`$TARGET_SHA\`
- Deployment: **$status**
- Staging post-deploy health check: $staging
- Production health check: $production
- Automatic rollback: disabled; inspect the Pi containers if deployment failed.
EOF
    chmod 600 "$report"
    cat "$report"
}

deploy_staging() {
    local source="$RELEASE_DIR/$TARGET_SHA" overlay="$RELEASE_DIR/$TARGET_SHA"
    make_release "$TARGET_SHA"
    [[ -f "$overlay/docker-compose.pi.yml" && -f "$overlay/deploy/pi/Caddyfile" ]] \
        || die "Commit $TARGET_SHA is missing the Pi staging configuration."
    install -m 644 "$overlay/deploy/pi/Caddyfile" "$CONFIG_DIR/Caddyfile"
    say "Building staging backend and executor for $TARGET_SHA."
    staging_compose "$source" "$overlay" build backend code-executor || return 1
    staging_compose "$source" "$overlay" pull executor-https || return 1
    staging_compose "$source" "$overlay" config --quiet || return 1

    local backend_state
    backend_state="$(docker inspect codeit-staging-backend-1 --format '{{.State.Status}}' 2>/dev/null || true)"
    if [[ "$backend_state" == running ]]; then
        docker exec codeit-staging-backend-1 python -c \
          'import sqlite3,sys; src=sqlite3.connect("/data/app.db"); dst=sqlite3.connect("/data/predeploy-"+sys.argv[1]+".db"); src.backup(dst); dst.close(); src.close()' \
          "$TARGET_SHA" || return 1
    elif [[ -n "$backend_state" ]]; then
        say "Skipping predeploy database snapshot because the staging backend is $backend_state."
    fi

    say "Starting staging backend, HTTPS executor proxy, and executor."
    staging_compose "$source" "$overlay" up --detach --no-deps --force-recreate \
        backend code-executor executor-https || return 1
    printf '%s\n' "$TARGET_SHA" >"$STATE_DIR/current-sha.tmp"
    chmod 600 "$STATE_DIR/current-sha.tmp"
    mv "$STATE_DIR/current-sha.tmp" "$STATE_DIR/current-sha"
    say "Staging containers started for $TARGET_SHA; health is checked after production promotion."
}

promote_production() {
    local source="$RELEASE_DIR/$TARGET_SHA"
    say "Building production backend and executor for $TARGET_SHA."
    production_compose "$source" build backend code-executor || return 1
    production_compose "$source" config --quiet || return 1
    say "Updating production backend and executor."
    production_compose "$source" up --detach --no-deps --force-recreate backend code-executor || return 1
    printf '%s\n' "$TARGET_SHA" >"$STATE_DIR/production-sha.tmp"
    chmod 600 "$STATE_DIR/production-sha.tmp"
    mv "$STATE_DIR/production-sha.tmp" "$STATE_DIR/production-sha"
}

if ! deploy_staging; then
    write_report FAILED "not available" "not run; staging deployment failed" >&2
    die "Staging deployment could not be started."
fi

if ! promote_production; then
    write_report FAILED "not checked" "production build or update failed; inspect production containers" >&2
    die "Production deployment could not be completed."
fi

staging_result=failed
production_result=failed
wait_healthy staging && staging_result=passed || true
wait_healthy production && production_result=passed || true

if [[ "$staging_result" == passed && "$production_result" == passed ]]; then
    write_report DEPLOYED "passed" "passed for backend and executor"
else
    write_report DEPLOYED_WITH_HEALTH_ISSUES "$staging_result" "$production_result; inspect containers and logs" >&2
    exit 1
fi
