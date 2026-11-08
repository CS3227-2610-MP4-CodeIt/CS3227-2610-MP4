import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess


def git(*args, cwd):
    return subprocess.check_output(["git", "-C", str(cwd), *args], text=True).strip()


def allowed(path):
    return (
        path.startswith("frontend/src/")
        or (path.startswith("frontend/tests/") and path.endswith(".test.mjs") and path != "frontend/tests/existing.test.mjs")
        or (path.startswith("workflow/implementations/") and path.endswith(".md"))
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    case = Path(__file__).resolve().parent
    project_root = case.parents[4]
    evidence = args.run.parent / "grader" / "browser"
    limitations = []

    try:
        run_data = json.loads(args.run.read_text(encoding="utf-8"))
        base = run_data["workspace_base_revision"]
        changed = set(git("diff", "--name-only", base, "--", cwd=workspace).splitlines())
        changed.update(git("ls-files", "--others", "--exclude-standard", cwd=workspace).splitlines())
        protected_inputs = True
        for original in (case / "fixture").rglob("*"):
            if not original.is_file():
                continue
            relative = original.relative_to(case / "fixture").as_posix()
            if relative.startswith("frontend/src/") and relative not in (
                "frontend/src/main.jsx", "frontend/src/quiz-data.mjs"
            ):
                continue
            if relative.startswith("frontend/tests/") and relative != "frontend/tests/existing.test.mjs":
                continue
            if relative.startswith("workflow/implementations/") and relative.endswith(".md"):
                continue
            current = workspace / Path(relative)
            protected_inputs &= current.is_file() and not current.is_symlink()
            if current.is_file():
                protected_inputs &= current.read_bytes() == original.read_bytes()
        handoffs = sorted(
            path for path in changed
            if path.startswith("workflow/implementations/") and path.endswith(".md")
        )
        scope_evidence = {
            "changed_paths": sorted(changed),
            "out_of_scope_paths": sorted(path for path in changed if not allowed(path)),
            "git_head_unchanged": git("rev-parse", "HEAD", cwd=workspace) == base,
            "protected_fixture_inputs_unchanged": protected_inputs,
            "handoff_paths": handoffs,
        }

        node = shutil.which("node")
        if not node:
            raise RuntimeError("Node.js is unavailable; browser observations were not collected.")
        env = os.environ.copy()
        env["EVAL_PROJECT_ROOT"] = str(project_root)
        result = subprocess.run(
            [node, str(case / "acceptance.mjs"), str(workspace), str(evidence)],
            cwd=workspace,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        oracle = json.loads(lines[-1]) if lines else None
        if result.returncode != 0 or not isinstance(oracle, dict):
            raise RuntimeError(f"Browser oracle returned invalid output: {result.stderr[-2000:]}")
        if oracle.get("infrastructure_error"):
            raise RuntimeError(oracle["infrastructure_error"])

        browser_observations = {
            "functional": oracle.get("functional", []),
            "desktop": oracle.get("desktop", []),
            "mobile": oracle.get("mobile", []),
            "screenshots": [
                str(path.relative_to(args.run.parent))
                for path in sorted(evidence.glob("*.png"))
            ],
        }
        # This deterministic grader only confirms that objective evidence was
        # collected. Semantic judges assess implementation quality, scope,
        # behavior, visual fidelity, tests, and the handoff from that evidence.
        notes = json.dumps(
            {"scope_evidence": scope_evidence, "browser_observations": browser_observations},
            ensure_ascii=False,
        )
        grade = {
            "overall_pass": True,
            "verdict": "pass",
            "score": 100,
            "checks": [{
                "id": "evaluation-evidence-captured",
                "pass": True,
                "verdict": "pass",
                "points": 100,
                "notes": notes,
            }],
            "limitations": [],
        }
    except Exception as error:
        limitations.append(f"Evaluation evidence could not be collected: {error}")
        grade = {
            "overall_pass": False,
            "verdict": "fail",
            "score": 0,
            "checks": [{
                "id": "evaluation-evidence-captured",
                "pass": False,
                "verdict": "fail",
                "points": 0,
                "notes": str(error),
            }],
            "limitations": limitations,
        }
    print(json.dumps(grade))


if __name__ == "__main__":
    main()
