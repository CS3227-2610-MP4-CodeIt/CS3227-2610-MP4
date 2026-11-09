import argparse,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser()
for k in ("workspace","trace","run"):p.add_argument("--"+k,required=True,type=Path)
a=p.parse_args();w=a.workspace.resolve();meta=json.loads(a.run.read_text(encoding="utf-8"));base=meta.get("workspace_base_revision")
def git(*args):
 return subprocess.run(["git","-C",str(w),*args],capture_output=True,text=True,encoding="utf-8",errors="replace")
head=git("rev-parse","HEAD");diff=git("diff","--name-only",base,"--");untracked=git("ls-files","--others","--exclude-standard")
valid=bool(base) and all(x.returncode==0 for x in (head,diff,untracked))
paths=set(diff.stdout.splitlines()) | set(untracked.stdout.splitlines()) if valid else set()
unrelated=sorted(x for x in paths if not (x.startswith("workflow/reviews/") and x.endswith(".md")))
reports=[x for x in paths if x.startswith("workflow/reviews/") and x.endswith(".md") and (w/x).is_file() and (w/x).stat().st_size>0]
metrics_path=a.run.parent/"worker"/"metrics.json"
metrics=json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.is_file() else {}
spawn=metrics.get("subagent_spawn_count")
checks=[("review-artifact",valid and bool(reports),"A nonempty review report exists under workflow/reviews/"),("review-only-scope",valid and not unrelated,"No source, tests, specifications, or other non-review files changed"),("head-unchanged",valid and head.stdout.strip()==base,"Git HEAD remains at the controlled workspace base"),("no-subagent",spawn==0,"Recorded subagent spawn count is zero (missing evidence is not zero)")]
grade=[{"id":i,"pass":ok,"points":25 if ok else 0,"notes":note if ok else "Not established: "+note} for i,ok,note in checks]
passed=all(x["pass"] for x in grade)
print(json.dumps({"score":100 if passed else 0,"overall_pass":passed,"checks":grade,"limitations":["This checks observable scope and report existence only; semantic judges assess defect detection, evidence and false findings.","Recorded spawn count does not establish a child did no work if telemetry is incomplete."]}))
