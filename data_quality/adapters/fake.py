from data_quality.schema import QualityCheck


class FakeCountAdapter:
    def __init__(self, counts=None):
        self.counts = counts or {}

    def count_violations(self, check: QualityCheck) -> int:
        return self.counts.get(check.name, 0)
