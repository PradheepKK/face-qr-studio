# In-memory job store. Photos + result disk-la save aagaadhu.
# 10 min-ku mela old jobs auto-delete aagum.

import dataclasses
import threading
import time
import uuid
from dataclasses import dataclass, field

JOB_TTL_SECONDS = 600
MAX_JOBS = 20


class TooManyJobsError(Exception):
    """Server romba busy-a irukku."""


@dataclass
class Job:
    id: str
    state: str = "queued"  # queued / running / done / error
    progress: int = 0
    message: str = "Queue-la irukku..."
    attempt: int = 0
    total_attempts: int = 0
    error: str | None = None
    error_status: int | None = None
    meta: dict | None = None
    png: bytes | None = None
    updated: float = field(default_factory=time.time)


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def _purge(self) -> None:
        # lock already irukkanum
        now = time.time()
        old = [jid for jid, j in self._jobs.items() if now - j.updated > JOB_TTL_SECONDS]
        for jid in old:
            del self._jobs[jid]

    def create(self) -> str:
        with self._lock:
            self._purge()
            if len(self._jobs) >= MAX_JOBS:
                raise TooManyJobsError()
            job_id = uuid.uuid4().hex
            self._jobs[job_id] = Job(id=job_id)
            return job_id

    def update(self, job_id: str, **fields) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return False
            for k, v in fields.items():
                setattr(job, k, v)
            job.updated = time.time()
            return True

    def snapshot(self, job_id: str) -> Job | None:
        """Job-oda copy (PNG illaama). Status paarkka."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            return dataclasses.replace(job, png=None)

    def pop_result(self, job_id: str) -> bytes | None:
        """PNG-a eduthutu job-a delete pannum (oru thadavai mattum edukkalam)."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None or job.state != "done" or job.png is None:
                return None
            del self._jobs[job_id]
            return job.png


store = JobStore()