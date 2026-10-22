from dataclasses import dataclass
from typing import Any

import aiosqlite

from app.db import Database

VERDICTS = ("ACCEPTED", "WRONG_ANSWER", "TIME_LIMIT_EXCEEDED", "MEMORY_LIMIT_EXCEEDED", "RUNTIME_ERROR")


@dataclass
class Submission:
    id: int
    user_id: int
    assignment_id: int
    question_id: int
    job_id: int | None
    verdict: str
    passed: int
    total: int
    created_at: str
    code: str | None  # None in list results


def _submission(row: aiosqlite.Row, with_code: bool) -> Submission:
    return Submission(
        row["id"], row["user_id"], row["assignment_id"], row["question_id"], row["job_id"], row["verdict"],
        row["passed"], row["total"], row["created_at"], row["code"] if with_code else None,
    )


async def create(
    db: Database,
    user_id: int,
    assignment_id: int,
    question_id: int,
    job_id: int | None,
    code: str,
    verdict: str,
    passed: int,
    total: int,
) -> int:
    """Returns the new submission id."""
    async with db.transaction() as conn:
        cursor = await conn.execute(
            "INSERT INTO submissions (user_id, assignment_id, question_id, job_id, code, verdict, passed, total) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, assignment_id, question_id, job_id, code, verdict, passed, total),
        )
        return cursor.lastrowid  # type: ignore[return-value]


async def list_for(db: Database, user_id: int, assignment_id: int, question_id: int) -> list[Submission]:
    """The student's submissions for one assignment question, newest first, without code."""
    async with db.connect() as conn:
        cursor = await conn.execute(
            "SELECT id, user_id, assignment_id, question_id, job_id, verdict, passed, total, created_at "
            "FROM submissions WHERE user_id = ? AND assignment_id = ? AND question_id = ? ORDER BY id DESC",
            (user_id, assignment_id, question_id),
        )
        return [_submission(row, False) for row in await cursor.fetchall()]


async def get(db: Database, submission_id: int) -> Submission | None:
    """One submission with code. The caller checks user_id / assignment_id / question_id."""
    async with db.connect() as conn:
        cursor = await conn.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,))
        row = await cursor.fetchone()
    return _submission(row, True) if row else None


async def solved_pairs(db: Database, user_id: int) -> set[tuple[int, int]]:
    """(assignment_id, question_id) pairs the student has an ACCEPTED submission for."""
    async with db.connect() as conn:
        cursor = await conn.execute(
            "SELECT DISTINCT assignment_id, question_id FROM submissions WHERE user_id = ? AND verdict = 'ACCEPTED'",
            (user_id,),
        )
        return {(r[0], r[1]) for r in await cursor.fetchall()}


async def assignment_stats(db: Database, assignment_id: int) -> dict[str, Any] | None:
    """Aggregate progress numbers for the admin summary (§7.3); current students of the class only.
    Returns None if the assignment does not exist. Contains no student names or code."""
    async with db.connect() as conn:
        cursor = await conn.execute(
            "SELECT a.title, a.due_at, a.class_id, c.name FROM assignments a JOIN classes c ON c.id = a.class_id "
            "WHERE a.id = ?",
            (assignment_id,),
        )
        head = await cursor.fetchone()
        if head is None:
            return None
        students = (
            "SELECT m.user_id FROM class_members m JOIN users u ON u.id = m.user_id "
            "WHERE m.class_id = :class_id AND u.role = 'student'"
        )
        params = {"aid": assignment_id, "class_id": head["class_id"]}

        cursor = await conn.execute(f"SELECT count(*) FROM ({students})", params)
        students_in_class = (await cursor.fetchone())[0]  # type: ignore[index]

        cursor = await conn.execute(
            f"SELECT count(DISTINCT user_id) FROM submissions WHERE assignment_id = :aid AND user_id IN ({students})",
            params,
        )
        attempted_any = (await cursor.fetchone())[0]  # type: ignore[index]

        cursor = await conn.execute(
            f"""SELECT count(*) FROM (
                  SELECT user_id FROM submissions
                  WHERE assignment_id = :aid AND verdict = 'ACCEPTED' AND user_id IN ({students})
                  GROUP BY user_id
                  HAVING count(DISTINCT question_id) =
                         (SELECT count(*) FROM assignment_questions WHERE assignment_id = :aid))""",
            params,
        )
        solved_all = (await cursor.fetchone())[0]  # type: ignore[index]

        cursor = await conn.execute(
            f"""SELECT aq.position, aq.question_id, q.title, q.difficulty,
                  count(DISTINCT s.user_id) AS attempted,
                  count(DISTINCT CASE WHEN s.verdict = 'ACCEPTED' THEN s.user_id END) AS correct,
                  count(s.id) AS total_submissions
                FROM assignment_questions aq
                JOIN questions q ON q.id = aq.question_id
                LEFT JOIN submissions s ON s.assignment_id = aq.assignment_id AND s.question_id = aq.question_id
                     AND s.user_id IN ({students})
                WHERE aq.assignment_id = :aid
                GROUP BY aq.position, aq.question_id, q.title, q.difficulty
                ORDER BY aq.position""",
            params,
        )
        question_rows = await cursor.fetchall()

        cursor = await conn.execute(
            f"""SELECT question_id, verdict, count(*) FROM submissions
                WHERE assignment_id = :aid AND user_id IN ({students})
                GROUP BY question_id, verdict""",
            params,
        )
        verdicts: dict[int, dict[str, int]] = {}
        for question_id, verdict, n in await cursor.fetchall():
            verdicts.setdefault(question_id, {})[verdict] = n

    return {
        "assignment": {"title": head["title"], "due_at": head["due_at"], "class_name": head["name"]},
        "students_in_class": students_in_class,
        "students_attempted_any": attempted_any,
        "students_solved_all": solved_all,
        "questions": [
            {
                "position": r["position"],
                "title": r["title"],
                "difficulty": r["difficulty"],
                "attempted": r["attempted"],
                "correct": r["correct"],
                "total_submissions": r["total_submissions"],
                "verdicts": {v: verdicts.get(r["question_id"], {}).get(v, 0) for v in VERDICTS},
            }
            for r in question_rows
        ],
    }
