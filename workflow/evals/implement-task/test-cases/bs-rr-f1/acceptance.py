import copy, importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("attempts", Path(sys.argv[1]) / "backend" / "attempts.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
for result in ({"score": 3, "explanations": ["explanation"], "nested": {"v": 1}},
               {"score": 3, "nested": {"v": 1}}):
    r = {"student_id": 7, "status": "submitted", "result": copy.deepcopy(result)}
    assert m.read_result(r, 7) == result
    assert m.read_result(r, 7, True) == result
    output = m.read_result(r, 7, False)
    assert output == {k: v for k, v in result.items() if k != "explanations"}
    assert output is not r["result"] and r["result"] == result
    for actor, status in ((8, "submitted"), (7, "in_progress")):
        rejected = copy.deepcopy(r); rejected["status"] = status
        for flag in (True, False):
            try: m.read_result(rejected, actor, flag)
            except PermissionError: pass
            else: raise AssertionError("denied call did not raise PermissionError")
print("Private result-redaction checks passed")
