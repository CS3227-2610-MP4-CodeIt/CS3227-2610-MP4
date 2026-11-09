def read_result(record, student_id):
    if record["status"] != "submitted":
        raise PermissionError("Result unavailable")
    return record["result"]
