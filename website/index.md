<frontmatter>
  title: "CodeIt"
</frontmatter>

<div class="hero">

# CodeIt

<p class="tagline">
A Python programming assignment platform: teachers build questions, students solve them with automated judging and AI hints, and administrators manage classes and review progress.
</p>

<!-- TODO: replace with the deployed frontend URL -->
<a class="btn btn-primary btn-lg" href="#try-codeit">Try CodeIt</a>
<a class="btn btn-outline-primary btn-lg" href="https://github.com/CS3227-2610-MP4-CodeIt/CS3227-2610-MP4/blob/master/docs/UserGuide.md">User Guide</a>
<a class="btn btn-outline-secondary btn-lg" href="https://github.com/CS3227-2610-MP4-CodeIt/CS3227-2610-MP4/blob/master/docs/DeveloperGuide.md">Developer Guide</a>

</div>

## One platform, three roles

Every role has its own AI feature, powered by SoCLaaS.

<div class="roles">
<div class="role-card">

### Student

- Solve assigned Python questions in an in-browser editor
- **Run** against visible sample tests
- **Submit** against visible and hidden tests
- Revisit and reload previous submissions

<div class="ai">

**AI hints** — ask for guidance on your current code, optionally with a specific question. Hints never reveal hidden tests.
</div>
</div>
<div class="role-card">

### Teacher

- Maintain a personal question bank with visible and hidden tests
- Set time, memory and float-tolerance limits
- Create class assignments with up to three questions and a due date

<div class="ai">

**AI question drafts** — generate a question from a topic and prompt, revise it with feedback, then approve it into your bank.
</div>
</div>
<div class="role-card">

### Admin

- Create and manage teacher and student accounts
- Create classes and manage their memberships
- Inspect per-assignment statistics

<div class="ai">

**AI progress summaries** — turn aggregate assignment statistics into a narrative summary, without sharing student names or code.
</div>
</div>
</div>

## How it works

- **Frontend** — React and TypeScript single-page app, served by Nginx.
- **Backend** — FastAPI service with SQLite storage, role-based access control and live updates over server-sent events.
- **Code executor** — a separate FastAPI service that judges each test in its own Python subprocess with time and memory limits.
- **AI** — SoCLaaS calls are made server-side only, with prompt-injection guards and rate-limit handling.

## Try CodeIt

<!-- TODO: add the deployed app URL and peer-test accounts -->
The hosted deployment runs on Render's free tier, so it can be slow to wake up. For the best experience, run CodeIt locally with Docker:

```bash
git clone https://github.com/CS3227-2610-MP4-CodeIt/CS3227-2610-MP4.git
cd CS3227-2610-MP4
docker compose up --build
```

Then open <http://localhost:5173>. See the [User Guide](https://github.com/CS3227-2610-MP4-CodeIt/CS3227-2610-MP4/blob/master/docs/UserGuide.md) for demo accounts and a peer-testing walkthrough.

## Built with

React · TypeScript · Tailwind CSS · CodeMirror · FastAPI · Pydantic · SQLite · Docker · Render · SoCLaaS
