# Raspberry Pi staging deployment

Every push to `master` runs the backend and executor checks. A successful run
joins the tailnet temporarily, then asks the Pi to deploy that exact commit to
the isolated `codeit-staging` Compose project. The existing Funnel-facing
service and database remain on the existing Compose project and port 8000.

The staging backend binds to `127.0.0.1:8001`, uses its own database volume,
runs with `APP_ENV=prod`, and talks to the executor through an internal HTTPS
proxy. The Pi override limits the executor to 3 GiB RAM, 2 CPUs, 128 processes,
and 2 concurrent jobs. The local Compose configuration is unchanged apart from
environment-variable defaults that preserve its existing values.

## Pi bootstrap

`bootstrap-pi.sh` has been run on the Pi. It creates a separate staging token,
an internal certificate authority and executor certificate, and a protected
Compose environment file under `~/.config/codeit-staging`. It does not change
the existing backend or executor env files. Re-running it preserves the
staging token and certificates.

The deploy command lives outside the repository at
`~/.local/bin/deploy-codeit-staging`. Its SSH key is restricted in
`authorized_keys` to `staging <full-commit-sha>`; it rejects any other command
or SHA that is no longer the current `master` commit. After a deploy it checks
the backend, executor container health, and the HTTPS executor connection. A
failure triggers rollback to the previous source revision.

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

This workflow deploys staging only. Production promotion remains a separate
manual approval step, as previously selected. The production stack stays on
port 8000 and continues to be served by the existing Funnel configuration.
