# Historical MP2/MP3 eval import

Prior eval artifacts are imported into the normal per-skill `runs/` and
`comparisons/` directories so `eval.py compare` can use them without rerunning
workers or judges. Imported run IDs use `mp2-` and `mp3-` prefixes to avoid
collisions with MP4 experiment IDs. Each imported `experiment.json` records its
source under `historical_import`.

For example, compare the MP3 poisoned-comment result with the existing MP4 run:

```powershell
python workflow/evals/eval.py compare implement-task mp3-experiment-006 experiment-001
```

The command reads persisted experiment summaries and writes a Markdown report
under that skill's `comparisons/` directory. It makes no model calls. Historical
skills that are no longer installed can also be compared from their imported
manifests, for example:

```powershell
python workflow/evals/eval.py compare javadoc-writing mp2-experiment-001 mp2-experiment-008
```

## Imported artifact coverage

- **MP2:** 17 experiment manifests and reports where present, including the
  archived trial workspaces and traces. One dangling `.agents/skills` entry in
  an archived workspace was skipped because its source path no longer exists.
- **MP3:** 17 experiment manifests (including grading recovery), their reports,
  one manual-run report, and three existing comparison reports. Only the
  grading-recovery import has archived `trials/`; the other MP3 experiments
  contain persisted per-cell and per-trial summaries without raw traces or
  workspace snapshots.

Imported cases whose MP4 harness case is explicitly prefixed `mp3-` use that
same name in the imported MP3 manifest, allowing the comparator to find shared
cases. The imported manifest records its source archive and case-name mapping;
the original report preserves the original case names.
