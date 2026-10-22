"""In-process per-user notification hub for the SSE stream (spec §6.6)."""

import asyncio

from app.repos.jobs import Job

QUEUE_SIZE = 100

# user_id → one queue per open stream. None in a queue means "close the stream" (shutdown).
_subscribers: dict[int, set[asyncio.Queue[dict | None]]] = {}


def subscribe(user_id: int) -> asyncio.Queue[dict | None]:
    queue: asyncio.Queue[dict | None] = asyncio.Queue(maxsize=QUEUE_SIZE)
    _subscribers.setdefault(user_id, set()).add(queue)
    return queue


def unsubscribe(user_id: int, queue: asyncio.Queue[dict | None]) -> None:
    queues = _subscribers.get(user_id)
    if queues is None:
        return
    queues.discard(queue)
    if not queues:
        del _subscribers[user_id]


def subscriber_count(user_id: int) -> int:
    return len(_subscribers.get(user_id, ()))


def publish(job: Job) -> None:
    """Notifies only the job owner's streams. Never blocks; a full queue drops the notification."""
    for queue in _subscribers.get(job.user_id, ()):
        try:
            queue.put_nowait({"job_id": job.id, "kind": job.kind, "target_key": job.target_key})
        except asyncio.QueueFull:
            pass  # the client resyncs on its next `ready`


def close_all() -> None:
    """Ends every open stream (lifespan shutdown)."""
    for queues in _subscribers.values():
        for queue in queues:
            while True:
                try:
                    queue.put_nowait(None)
                    break
                except asyncio.QueueFull:
                    queue.get_nowait()  # make room for the close marker
