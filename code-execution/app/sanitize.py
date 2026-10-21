MAX_MESSAGE_BYTES = 4 * 1024


def tail(text: str, limit: int) -> str:
    """Keep the last `limit` bytes of text (the exception line is at the end)."""
    data = text.encode()
    if len(data) <= limit:
        return text
    return data[-limit:].decode(errors="ignore")


def head(text: str, limit: int) -> str:
    return text.encode()[:limit].decode(errors="ignore")


def _strip_harness_frames(text: str) -> str:
    out: list[str] = []
    skipping = False
    for line in text.splitlines():
        if line.startswith('  File "'):
            skipping = 'harness.py"' in line
        elif not line.startswith("    "):
            skipping = False
        if not skipping:
            out.append(line)
    return "\n".join(out)


def sanitize_traceback(stderr: bytes, workdir: str) -> str:
    text = stderr.decode("utf-8", errors="replace")
    text = _strip_harness_frames(text)
    text = text.replace(workdir + "/", "").replace(workdir, "")
    return tail(text, MAX_MESSAGE_BYTES)
