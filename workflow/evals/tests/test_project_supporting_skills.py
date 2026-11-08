"""Tests for pinned, non-duplicated project supporting skills."""

import json
from pathlib import Path
import shutil
import sys
import unittest
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _lib.common import Case, HarnessError
from _lib.harness import _portable_skill_digest, _project_supporting_skills, run_trial


class ProjectSupportingSkillsTests(unittest.TestCase):
    def setUp(self):
        self.parent = Path.cwd().resolve()
        self.root = self.parent / f"eval-skill-test-{uuid.uuid4().hex}"
        self.root.mkdir()
        self.case = self.root / "case"
        self.case.mkdir()
        self.skills = self.root / "skills"
        self.target = self.skills / "target"
        self.support = self.skills / "support"
        self.target.mkdir(parents=True)
        self.support.mkdir()
        (self.support / "SKILL.md").write_text("# original\n", encoding="utf-8")

    def tearDown(self):
        if self.root.parent != self.parent or not self.root.name.startswith("eval-skill-test-"):
            raise RuntimeError("unsafe test cleanup path")
        shutil.rmtree(self.root)

    def manifest(self, name="support", digest=None):
        payload = {"project_skills": {name: digest or _portable_skill_digest(self.support)}}
        (self.case / "supporting-skills.json").write_text(json.dumps(payload), encoding="utf-8")

    def test_resolves_matching_pin_and_rejects_changed_skill(self):
        self.manifest()
        self.assertEqual(_project_supporting_skills(self.case, self.target), (self.support,))
        (self.support / "SKILL.md").write_text("# changed\n", encoding="utf-8")
        with self.assertRaisesRegex(HarnessError, "changed since pinning"):
            _project_supporting_skills(self.case, self.target)

    def test_rejects_target_or_path_traversal(self):
        for name in ("target", "../support", "other/path"):
            with self.subTest(name=name):
                self.manifest(name)
                with self.assertRaises(HarnessError):
                    _project_supporting_skills(self.case, self.target)

    def test_absent_manifest_preserves_existing_cases(self):
        self.assertEqual(_project_supporting_skills(self.case, self.target), ())

    def test_changed_manifest_is_rejected_before_creating_a_trial(self):
        self.manifest()
        fixture = self.case / "fixture"
        fixture.mkdir()
        case = Case(name="sample", root=self.case, fixture=fixture,
                    prompt=self.case / "prompt.md", expected=None, checker=None,
                    supporting_skills=(self.support,), interactions=())
        (self.case / "supporting-skills.json").write_text('{"project_skills": {}}', encoding="utf-8")
        run_dir = self.root / "trial"
        with self.assertRaisesRegex(HarnessError, "changed after discovery"):
            run_trial(case=case, skill_root=self.target, configuration="with-skill", trial=1,
                      run_dir=run_dir, schema=self.root / "schema.json", semantic_enabled=False,
                      semantic_judges=1, timeout=1, model=None)
        self.assertFalse(run_dir.exists())


if __name__ == "__main__":
    unittest.main()
