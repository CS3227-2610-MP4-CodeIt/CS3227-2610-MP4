import argparse, json, os, subprocess, sys
from pathlib import Path
p = argparse.ArgumentParser()
for key in ("workspace", "trace", "run"):
    p.add_argument("--" + key, required=True, type=Path)
a = p.parse_args()
env = os.environ.copy()
env["PYTHONDONTWRITEBYTECODE"] = "1"
result = subprocess.run([sys.executable, "-B", str(Path(__file__).with_name("acceptance.py")),
                         str(a.workspace.resolve())], capture_output=True, text=True,
                        encoding="utf-8", errors="replace", timeout=45, env=env)
ok = result.returncode == 0
print(json.dumps({"score": 100 if ok else 0, "overall_pass": ok,
 "verdict": "pass" if ok else "fail",
 "checks": [{"id": "private-behavior", "pass": ok, "verdict": "pass" if ok else "fail",
              "points": 100 if ok else 0, "notes": (result.stdout + result.stderr)[-4000:]}],
 "limitations": ["Private acceptance is evaluator-run, not proof of worker verification; "
                 "semantic judges assess other requirements, scope, tests and handoff."]}))
