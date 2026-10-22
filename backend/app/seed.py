"""Dev-only demo accounts and classes (spec §4). Safe to run on every startup."""

from app.auth import hash_password
from app.db import Database
from app.repos import classes as classes_repo
from app.repos import users as users_repo

DEMO_PASSWORD = "demo1234"

# (class name, teacher, students)
DEMO_CLASSES = [
    ("Demo Class A", "teacher1", [f"student{i:02d}" for i in range(1, 11)]),
    ("Demo Class B", "teacher2", [f"student{i:02d}" for i in range(11, 21)]),
]


async def seed_demo(db: Database) -> None:
    password_hash = await hash_password(DEMO_PASSWORD)  # one hash for all demo users (dev only)

    async def ensure_user(username: str, display_name: str, role: str) -> int:
        found = await users_repo.get_with_password_hash(db, username)
        if found is not None:
            return found[0].id
        return (await users_repo.create(db, username, display_name, password_hash, role)).id

    if await users_repo.count_admins(db) == 0:
        await ensure_user("admin", "Demo Admin", "admin")

    for class_name, teacher, students in DEMO_CLASSES:
        teacher_id = await ensure_user(teacher, f"Teacher {teacher[-1]}", "teacher")
        student_ids = [await ensure_user(s, f"Student {s[-2:]}", "student") for s in students]
        if await classes_repo.get_by_name(db, class_name) is None:
            demo_class = await classes_repo.create(db, class_name, "Demo class (dev only)")
            await classes_repo.add_members(db, demo_class.id, [teacher_id, *student_ids])
