import re

from app.schemas import FloatTolerance

NUMBER_RE = re.compile(r"[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?")


def normalize(text: str) -> list[str]:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def compare(actual: bytes, expected: str, tolerance: FloatTolerance | None) -> str | None:
    """Return None if the outputs match, otherwise a message naming the first mismatch."""
    actual_lines = normalize(actual.decode("utf-8", errors="replace"))
    expected_lines = normalize(expected)
    if len(actual_lines) != len(expected_lines):
        return f"Line count differs: expected {len(expected_lines)}, got {len(actual_lines)}"

    for line_no, (a_line, e_line) in enumerate(zip(actual_lines, expected_lines), start=1):
        if tolerance is None:
            if a_line != e_line:
                return f"Line {line_no} differs"
            continue

        a_tokens, e_tokens = a_line.split(), e_line.split()
        if len(a_tokens) != len(e_tokens):
            return f"Line {line_no}: expected {len(e_tokens)} tokens, got {len(a_tokens)}"
        for token_no, (a, e) in enumerate(zip(a_tokens, e_tokens), start=1):
            if a == e:
                continue
            if NUMBER_RE.fullmatch(a) and NUMBER_RE.fullmatch(e):
                diff = abs(float(a) - float(e))
                if diff <= tolerance.abs or diff <= tolerance.rel * abs(float(e)):
                    continue
                return (
                    f"Line {line_no}, token {token_no}: expected {e}, got {a} "
                    f"(|diff| {diff:.1e} exceeds tolerance)"
                )
            return f"Line {line_no}, token {token_no}: expected {e}, got {a}"
    return None
