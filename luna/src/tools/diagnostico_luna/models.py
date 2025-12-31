from dataclasses import dataclass


@dataclass
class TestResult:
    module: str
    status: str
    duration: float
    details: str = ""
    error: str | None = None
