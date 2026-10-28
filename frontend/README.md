# Frontend

React + Vite single-page app for admins, teachers and students.
See `../specs/frontend/frontend-spec.md`.

The backend URL comes from `VITE_API_BASE_URL` (spec §8). Copy `.env.example` to `.env` and set it;
the default `http://localhost:8000` points at the backend running locally (`../backend/README.md`).

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

The URL is baked into the JS at build time, so rebuild the image after changing it. The build reads
`.env`; a `VITE_API_BASE_URL` build arg overrides it:

```
docker build --build-arg VITE_API_BASE_URL=https://my-backend.example.com -t frontend .
```

On Render, set `VITE_API_BASE_URL` in the service's Environment tab (Render passes it as a build
arg) and set the Root Directory to `frontend`.
