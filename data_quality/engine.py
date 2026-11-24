from dataclasses import dataclass
from typing import Protocol

from data_quality.schema import QualityCheck


class CountAdapter(Protocol):
    def count_violations(self, check: QualityCheck) -> int:
        """Return only the number of violating records or groups."""
        ...


@dataclass(frozen=True)
class CheckResult:
    table: str
    name: str
    check_type: str
    severity: str
    violation_count: int
    status: str


class QualityEngine:
    def __init__(self, adapter: CountAdapter):
        self.adapter = adapter

    def execute(self, checks: list[QualityCheck]) -> list[CheckResult]:
        results = []

        for check in checks:
            count = self.adapter.count_violations(check)

            if type(count) is not int or count < 0:
                raise ValueError(
                    f"{check.name}: adapter must return a nonnegative integer"
                )

            status = "PASS" if count == 0 else check.severity

            results.append(
                CheckResult(
                    table=check.table,
                    name=check.name,
                    check_type=check.check_type,
                    severity=check.severity,
                    violation_count=count,
                    status=status,
                )
            )

        return results

    @staticmethod
    def should_fail_pipeline(results: list[CheckResult]) -> bool:
        return any(result.status == "ERROR" for result in results)
