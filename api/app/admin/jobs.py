"""In-memory job tracker for long-running admin operations.

Lives in the same process as FastAPI (we have only one api container with
N workers; jobs created in worker A are visible to other workers via the
filesystem we'd need — but for the MVP we accept that the same worker
that started the job must serve the polling). This is fine because uvicorn's
default worker stickiness routes a single client to the same worker for
keep-alive connections, and our polling is short-lived.
"""
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Job:
    id: str
    kind: str  # "url" | "upload" | "reingest"
    status: str = "running"  # running | done | error
    stage: str = "starting"
    progress: int = 0  # 0-100
    message: str = ""
    source_id: str | None = None
    chunk_count: int | None = None
    error: str | None = None
    started_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class JobsManager:
    """Thread-safe job registry. Auto-prunes jobs older than 1 hour."""

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create(self, kind: str) -> Job:
        job_id = uuid.uuid4().hex[:12]
        job = Job(id=job_id, kind=kind)
        with self._lock:
            self._jobs[job_id] = job
            self._prune_locked()
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, **fields: Any) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            for k, v in fields.items():
                setattr(job, k, v)
            job.updated_at = time.time()

    def list_recent(self, limit: int = 20) -> list[Job]:
        with self._lock:
            return sorted(self._jobs.values(), key=lambda j: j.started_at, reverse=True)[:limit]

    def _prune_locked(self) -> None:
        cutoff = time.time() - 3600
        for jid in [jid for jid, j in self._jobs.items() if j.updated_at < cutoff]:
            del self._jobs[jid]
