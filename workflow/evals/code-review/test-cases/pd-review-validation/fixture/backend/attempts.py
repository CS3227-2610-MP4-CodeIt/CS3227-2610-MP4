def save_answer(record, student_id, question_id, answer):
    if record["student_id"] != student_id or record["status"] != "in_progress":
        raise PermissionError("Not allowed")
    if question_id not in ("q1", "q2") or not isinstance(answer, int) or not 1 <= answer <= 4:
        raise ValueError("Invalid answer")
    record["answers"][question_id] = answer
