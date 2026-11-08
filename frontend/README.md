# Frontend

React + Vite single-page app for admins, teachers and students.
See `../specs/frontend/frontend-spec.md`.

The primary backend URL comes from `VITE_API_BASE_URL`; optional `VITE_API_FALLBACK_URL` is used
when the primary backend or its executor is unavailable (spec §8). Copy `.env.example` to `.env`;
the default primary `http://localhost:8000` points at the backend running locally
(`../backend/README.md`), and the fallback is empty.

## Local dev (Vite)

```
npm install
npm run dev        # http://localhost:5173
```

## Tests

```
npm test
```

## Docker

Build and run from this folder (it is self-contained):

```
docker build -t frontend .
docker run -d -p 5173:80 frontend    # http://localhost:5173
```

The URLs are baked into the JS at build time, so rebuild the image after changing them. The build
reads `.env`; build args override it:

```
docker build \
  --build-arg VITE_API_BASE_URL=https://pi.example.com \
  --build-arg VITE_API_FALLBACK_URL=https://render-backend.example.com \
  -t frontend .
```

On the Render frontend service, set `VITE_API_BASE_URL` to the Pi Funnel HTTPS origin and
`VITE_API_FALLBACK_URL` to the Render backend HTTPS origin (Render passes both as build args); set
the Root Directory to `frontend`. The browser checks `GET /api/health/ready` on the Pi at startup.
That endpoint checks the Pi backend and executor. If unavailable, the frontend sticks to Render for
the current tab and shows a notice. Safe reads may retry once on Render after a Pi network or 5xx
failure. Writes are never replayed automatically because the Pi may have processed them; later
requests use Render. Since the databases are separate, accounts, data, and sessions can differ.
