import copy, importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("attempts", Path(sys.argv[1]) / "backend" / "attempts.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
def record(status="in_progress"):
    return {"student_id": 7, "status": status, "answers": {"q1": 2}, "extra": {"x": 1}}
for question in ("q1", "q2"):
    for value in (1, 2, 3, 4):
        r = record(); expected = copy.deepcopy(r); expected["answers"][question] = value
        m.save_answer(r, 7, question, value); assert r == expected
for actor, status in ((8, "in_progress"), (7, "submitted"), (7, "not_started")):
    r = record(status); before = copy.deepcopy(r)
    try: m.save_answer(r, actor, "q1", 1)
    except PermissionError: pass
    else: raise AssertionError("denied call did not raise PermissionError")
    assert r == before
for question, value in (("q3", 1), ("q1", True), ("q1", False), ("q1", 0),
                        ("q1", 5), ("q1", 1.0), ("q1", "1"), (None, 1)):
    r = record(); before = copy.deepcopy(r)
    try: m.save_answer(r, 7, question, value)
    except ValueError: pass
    else: raise AssertionError("invalid call did not raise ValueError")
    assert r == before
print("Private answer validation checks passed")
