# Job API response formats.

from pydantic import BaseModel


class JobCreated(BaseModel):
    job_id: str


class JobCheck(BaseModel):
    decoder: str  # zxing / opencv
    variant: str  # 100% / 75% / 50% / jpeg
    ok: bool
    required: bool


class JobAttempt(BaseModel):
    n: int
    v: int  # QR version
    c: float  # center dot size
    ok: bool
    p: int | None = None
    t: int | None = None
    err: str | None = None


class JobResultMeta(BaseModel):
    verified: bool
    summary: str
    message: str
    checks: list[JobCheck]
    attempts: list[JobAttempt]
    final_attempt: int
    qr_version: int
    mask: int
    ec_level: str
    center_frac: float
    segmentation: str
    resolution: int


class JobStatus(BaseModel):
    job_id: str
    state: str
    progress: int
    message: str
    attempt: int
    total_attempts: int
    error: str | None
    error_status: int | None
    result: JobResultMeta | None