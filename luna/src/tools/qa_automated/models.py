from dataclasses import dataclass, field


@dataclass
class TestResult:
    name: str
    passed: bool
    duration: float
    error: str | None = None
    screenshot: str | None = None


@dataclass
class TestReport:
    tests: list[TestResult] = field(default_factory=list)
    started_at: str = ""
    finished_at: str = ""

    def add(self, result: TestResult):
        self.tests.append(result)

    @property
    def passed_count(self) -> int:
        return sum(1 for t in self.tests if t.passed)

    @property
    def failed_count(self) -> int:
        return sum(1 for t in self.tests if not t.passed)

    def to_dict(self) -> dict:
        return {
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "total": len(self.tests),
            "passed": self.passed_count,
            "failed": self.failed_count,
            "tests": [
                {
                    "name": t.name,
                    "passed": t.passed,
                    "duration": round(t.duration, 3),
                    "error": t.error,
                }
                for t in self.tests
            ],
        }
