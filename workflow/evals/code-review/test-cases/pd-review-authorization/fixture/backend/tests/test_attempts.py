import unittest
from attempts import read_result

class ResultTests(unittest.TestCase):
    def test_owner_can_read_submitted_result(self):
        self.assertEqual(read_result({"student_id": 7, "status": "submitted", "result": {"score": 1}}, 7), {"score": 1})
    def test_unsubmitted_result_is_denied(self):
        with self.assertRaises(PermissionError):
            read_result({"student_id": 7, "status": "in_progress", "result": {}}, 7)
