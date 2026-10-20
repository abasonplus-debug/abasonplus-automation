import copy, pathlib, sys, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from reviewed_video_timing import validate_reviewed_timing

class ReviewedTimingTests(unittest.TestCase):
    def setUp(self):
        self.meta = dict(slides=5, slide_seconds=2, slide_durations=[2]*5)
        self.approval = dict(date="2026-10-20", preview_run_id=39347549614,
                             preview_head_sha="a"*40, format=dict(slides=5, slide_seconds=2))
        self.run = dict(id=39347549614, head_sha="a"*40, conclusion="success",
                        head_branch="main", created_at="2026-10-20T00:25:26Z")
        self.policy = "SLIDE_SECONDS=2\n"

    def check(self, duration=10):
        return validate_reviewed_timing(self.meta, duration, self.approval, self.run, self.policy)

    def test_existing_pre_update_exact_approved_artifact(self):
        self.assertEqual(self.check(), 10)

    def test_two_second_run_at_or_after_change_rejected(self):
        for stamp in ("2026-10-20T00:31:03Z", "2026-10-21T00:25:26Z"):
            with self.subTest(stamp=stamp), self.assertRaises(ValueError):
                self.run["created_at"] = stamp
                self.check()

    def test_wrong_run_commit_status_branch_or_missing_commit_rejected(self):
        for field, value in (("id", 9), ("head_sha", "b"*40), ("conclusion", "failure"),
                             ("head_branch", "other")):
            run = copy.deepcopy(self.run)
            self.run[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError): self.check()
            self.run = run
        self.approval.pop("preview_head_sha")
        with self.assertRaises(ValueError): self.check()

    def test_mixed_or_different_approved_timing_rejected(self):
        self.meta["slide_durations"][-1] = 3
        with self.assertRaises(ValueError): self.check()
        self.meta["slide_durations"][-1] = 2
        self.approval["format"]["slide_seconds"] = 3
        with self.assertRaises(ValueError): self.check()

    def test_new_three_second_policy_and_ceiling(self):
        self.policy = "SLIDE_SECONDS=3\n"
        self.run["created_at"] = "2026-10-20T00:35:00Z"
        self.meta = dict(slides=16, slide_seconds=3, slide_durations=[3]*16)
        self.approval["format"] = dict(slides=16, slide_seconds=3)
        self.assertEqual(self.check(48), 48)
        self.meta = dict(slides=17, slide_seconds=3, slide_durations=[3]*17)
        self.approval["format"]["slides"] = 17
        with self.assertRaises(ValueError): self.check(51)

    def test_duration_date_and_unknown_policy_fail_closed(self):
        with self.assertRaises(ValueError): self.check(15)
        self.run["created_at"] = "2026-10-18T23:00:00Z"
        with self.assertRaises(ValueError): self.check()
        self.run["created_at"] = "2026-10-20T00:25:26Z"
        for policy in ("SLIDE_SECONDS=1.5", "SLIDE_SECONDS=2\nSLIDE_SECONDS=3",
                       "SLIDE_SECONDS=unknown", "SLIDE_SECONDS=True"):
            self.policy = policy
            with self.subTest(policy=policy), self.assertRaises(ValueError): self.check()
