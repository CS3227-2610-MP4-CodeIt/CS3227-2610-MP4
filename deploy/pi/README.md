# Raspberry Pi staging deployment

Every push to `master` runs the backend and executor checks. A successful run
joins the tailnet temporarily, then asks the Pi to deploy that exact commit to
the isolated `codeit-staging` Compose project. The Pi then rebuilds and
recreates the existing production backend and executor from the same commit,
without waiting for staging health to pass. It runs health checks on both
stacks after production has been updated.
The Funnel-facing service remains on port 8000 and keeps its existing database
volume and production environment files.

Production and staging both load `docker-compose.pi.yml`, which sets the Pi
executor concurrency to 8. Staging also loads
`docker-compose.pi.staging.yml`: its backend binds to `127.0.0.1:8001`, uses a
separate database volume, runs with `APP_ENV=prod`, and reaches its executor
through an internal HTTPS proxy. Staging limits the executor to 3 GiB RAM,
2 CPUs, and 128 processes. The local Compose configuration does not load either
Pi override and keeps its existing settings.

## Pi bootstrap

`bootstrap-pi.sh` has been run on the Pi. It creates a separate staging token,
an internal certificate authority and executor certificate, and a protected
Compose environment file under `~/.config/codeit-staging`. It does not change
the existing backend or executor env files. Re-running it preserves the
staging token and certificates.

The deploy command lives outside the repository at
`~/.local/bin/deploy-codeit-staging`. Its SSH key is restricted in
`authorized_keys` to `staging <full-commit-sha>`; it rejects any other command
or SHA that is no longer the current `master` commit. The command starts the
staging containers, then promotes the same commit to the existing `codeit`
production Compose project regardless of staging health. It checks both stacks
after production is updated. A Markdown report is saved in
`~/.config/codeit-staging/reports/` and printed into the GitHub Actions run
log. Failed post-deploy checks are reported after promotion, do not block the
production update, and do not automatically roll it back. The deployed
production SHA is recorded in
`~/.config/codeit-staging/state/production-sha`.

## Tailscale one-time setup

In the Tailscale admin console, create a workload identity credential for
GitHub Actions with:

- Issuer: `https://token.actions.githubusercontent.com`
- Subject: `repo:CS3227-2610-MP4-CodeIt/CS3227-2610-MP4:environment:pi-staging`
- Tag: `tag:github-actions`
- Scope sufficient to register an ephemeral tagged device

Ensure the tailnet policy allows `tag:github-actions` to reach the Pi on TCP
port 22. Review existing broad rules before adding or changing grants; a
narrow allow rule does not override a broader allow-all rule. Copy the
credential's Client ID and Audience into the `pi-staging` GitHub environment
as variables named `TAILSCALE_OAUTH_CLIENT_ID` and `TAILSCALE_AUDIENCE`.

The `pi-staging` GitHub environment is already restricted to the `master`
branch. It already contains the deploy-only SSH private key and the Pi host
key. The workflow does not expose these credentials to pull-request jobs.

## Production promotion

Promotion is automatic after staging containers start. It updates only
the existing Pi `codeit` Compose backend and executor; it does not change the
Render frontend or the Tailscale Funnel configuration. The production
database volume and environment files remain in place.
