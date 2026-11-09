import unittest
from attempts import save_answer

class AnswerTests(unittest.TestCase):
    def test_valid_save(self):
        record = {"student_id": 7, "status": "in_progress", "answers": {}}
        save_answer(record, 7, "q1", 1)
        self.assertEqual(record["answers"], {"q1": 1})
    def test_invalid_range(self):
        record = {"student_id": 7, "status": "in_progress", "answers": {}}
        with self.assertRaises(ValueError):
            save_answer(record, 7, "q1", 5)
