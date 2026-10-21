-- Backend database schema (SQLite 3.x). See specs/backend-spec.md.
--
-- Run on every new connection (not persisted by SQLite):
--   PRAGMA foreign_keys = ON;
--   PRAGMA busy_timeout = 5000;
-- Run once when the database is created (persisted):
--   PRAGMA journal_mode = WAL;
--
-- Timestamps are ISO-8601 UTC text, e.g. '2026-10-21T08:30:00.123Z'.
-- Booleans are INTEGER 0/1.

-- ---------------------------------------------------------------------------
-- Accounts and sessions
-- ---------------------------------------------------------------------------

CREATE TABLE users (
    id            INTEGER PRIMARY KEY,
    username      TEXT    NOT NULL UNIQUE COLLATE NOCASE
                          CHECK (length(username) BETWEEN 3 AND 32),
    display_name  TEXT    NOT NULL CHECK (length(display_name) BETWEEN 1 AND 100),
    password_hash TEXT    NOT NULL,                       -- argon2id
    role          TEXT    NOT NULL CHECK (role IN ('admin', 'teacher', 'student')),
    created_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- Opaque bearer tokens. Only the SHA-256 of the token is stored.
CREATE TABLE sessions (
    token_hash TEXT    PRIMARY KEY,                       -- hex sha256(token)
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    expires_at TEXT    NOT NULL
);
CREATE INDEX sessions_user ON sessions(user_id);

-- ---------------------------------------------------------------------------
-- Classes and roster
-- ---------------------------------------------------------------------------

CREATE TABLE classes (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE COLLATE NOCASE CHECK (length(name) BETWEEN 1 AND 100),
    description TEXT NOT NULL DEFAULT '' CHECK (length(description) <= 2000),
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- Teachers and students in a class. The member's role comes from users.role.
-- The app rejects admins as members.
CREATE TABLE class_members (
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    user_id  INTEGER NOT NULL REFERENCES users(id)   ON DELETE CASCADE,
    added_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (class_id, user_id)
);
CREATE INDEX class_members_user ON class_members(user_id);

-- ---------------------------------------------------------------------------
-- Questions and test cases
-- ---------------------------------------------------------------------------

CREATE TABLE questions (
    id              INTEGER PRIMARY KEY,
    created_by      INTEGER REFERENCES users(id) ON DELETE SET NULL,   -- teacher
    title           TEXT    NOT NULL CHECK (length(title) BETWEEN 1 AND 200),
    statement_md    TEXT    NOT NULL CHECK (length(statement_md) BETWEEN 1 AND 20000),
    difficulty      TEXT    NOT NULL CHECK (difficulty IN ('easy', 'medium', 'hard')),
    topics_json     TEXT    NOT NULL DEFAULT '[]'
                            CHECK (json_valid(topics_json) AND json_type(topics_json) = 'array'),
    time_limit_ms   INTEGER NOT NULL DEFAULT 2000 CHECK (time_limit_ms BETWEEN 100 AND 10000),
    memory_limit_mb INTEGER NOT NULL DEFAULT 256  CHECK (memory_limit_mb BETWEEN 16 AND 1024),
    -- Both NULL = exact comparison. Otherwise both set, in [0, 1], at least one > 0
    -- (same rules as the executor's float_tolerance).
    float_abs       REAL,
    float_rel       REAL,
    -- The question_gen job this question was approved from (NULL if written by hand).
    -- UNIQUE stops the same draft from being approved twice.
    source_job_id   INTEGER UNIQUE REFERENCES jobs(id) ON DELETE SET NULL,
    created_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    CHECK (
        (float_abs IS NULL AND float_rel IS NULL)
        OR (float_abs IS NOT NULL AND float_rel IS NOT NULL
            AND float_abs BETWEEN 0 AND 1 AND float_rel BETWEEN 0 AND 1
            AND (float_abs > 0 OR float_rel > 0))
    )
);
CREATE INDEX questions_created_by ON questions(created_by);

-- "At least 1 visible and 1 hidden test case" is enforced by the app on every write.
CREATE TABLE test_cases (
    id              INTEGER PRIMARY KEY,
    question_id     INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    position        INTEGER NOT NULL CHECK (position >= 1),    -- order sent to the executor
    is_hidden       INTEGER NOT NULL CHECK (is_hidden IN (0, 1)),
    stdin           TEXT    NOT NULL CHECK (length(CAST(stdin AS BLOB)) <= 1048576),
    expected_stdout TEXT    NOT NULL CHECK (length(CAST(expected_stdout AS BLOB)) <= 1048576),
    UNIQUE (question_id, position)
);

-- ---------------------------------------------------------------------------
-- Assignments
-- ---------------------------------------------------------------------------

CREATE TABLE assignments (
    id             INTEGER PRIMARY KEY,
    class_id       INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    created_by     INTEGER REFERENCES users(id) ON DELETE SET NULL,     -- teacher
    title          TEXT    NOT NULL CHECK (length(title) BETWEEN 1 AND 200),
    description_md TEXT    NOT NULL DEFAULT '' CHECK (length(description_md) <= 5000),
    due_at         TEXT,                                                -- NULL = no deadline
    created_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
CREATE INDEX assignments_class ON assignments(class_id);

-- 1 to 3 questions per assignment. position 1..3 plus UNIQUE caps it at 3;
-- the app enforces the minimum of 1.
CREATE TABLE assignment_questions (
    assignment_id INTEGER NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
    question_id   INTEGER NOT NULL REFERENCES questions(id)   ON DELETE RESTRICT,
    position      INTEGER NOT NULL CHECK (position BETWEEN 1 AND 3),
    PRIMARY KEY (assignment_id, question_id),
    UNIQUE (assignment_id, position)
);
CREATE INDEX assignment_questions_question ON assignment_questions(question_id);

-- ---------------------------------------------------------------------------
-- Long-running jobs (state machine, see spec §6)
-- ---------------------------------------------------------------------------

CREATE TABLE jobs (
    id          INTEGER PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kind        TEXT    NOT NULL
                        CHECK (kind IN ('run', 'submit', 'hint', 'question_gen', 'assignment_summary')),
    -- What the job is about, e.g. 'a12:q7' (assignment 12, question 7), 'a12', or '-'.
    target_key  TEXT    NOT NULL,
    status      TEXT    NOT NULL DEFAULT 'in_process'
                        CHECK (status IN ('in_process', 'success', 'failed')),
    input_json  TEXT    NOT NULL CHECK (json_valid(input_json)),
    result_json TEXT    CHECK (result_json IS NULL OR json_valid(result_json)),
    error       TEXT,                                 -- user-safe message when failed
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    finished_at TEXT,
    CHECK ((status = 'in_process') = (finished_at IS NULL)),
    CHECK ((status = 'success') = (result_json IS NOT NULL)),
    CHECK ((status = 'failed')  = (error IS NOT NULL))
);

-- At most one in-process job per (user, kind, target). Inserting a second one fails
-- with a UNIQUE error, which the job runner turns into "return the existing job".
CREATE UNIQUE INDEX jobs_one_in_process
    ON jobs(user_id, kind, target_key)
    WHERE status = 'in_process';

-- "Latest job for (user, kind, target)" lookups.
CREATE INDEX jobs_latest ON jobs(user_id, kind, target_key, id DESC);

-- ---------------------------------------------------------------------------
-- Graded submissions (written when a 'submit' job finishes)
-- ---------------------------------------------------------------------------

CREATE TABLE submissions (
    id            INTEGER PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,   -- student
    assignment_id INTEGER NOT NULL,
    question_id   INTEGER NOT NULL,
    job_id        INTEGER UNIQUE REFERENCES jobs(id) ON DELETE SET NULL,
    code          TEXT    NOT NULL CHECK (length(CAST(code AS BLOB)) <= 65536),
    verdict       TEXT    NOT NULL CHECK (verdict IN ('ACCEPTED', 'WRONG_ANSWER',
                          'TIME_LIMIT_EXCEEDED', 'MEMORY_LIMIT_EXCEEDED', 'RUNTIME_ERROR')),
    passed        INTEGER NOT NULL CHECK (passed >= 0),
    total         INTEGER NOT NULL CHECK (total >= 1),
    created_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (assignment_id, question_id)
        REFERENCES assignment_questions(assignment_id, question_id) ON DELETE CASCADE
);
CREATE INDEX submissions_lookup ON submissions(assignment_id, question_id, user_id);
CREATE INDEX submissions_user   ON submissions(user_id, created_at DESC);
