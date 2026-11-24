# Data Quality Remediation Runbook

## Incident Response

1. Identify the failing table, check, and violation count.
2. Stop downstream publication for ERROR-level failures.
3. Investigate the affected source batch.
4. Correct or quarantine invalid records.
5. Reprocess the affected batch.
6. Rerun the quality checks.
7. Resume downstream execution after successful validation.

## Duplicate Primary Keys

Severity: ERROR

Investigate repeated composite keys using GROUP BY
and HAVING count() > 1.

Review ingestion retries, source duplication, and
idempotency logic.

Deduplicate using an approved business rule.

## Missing Required Fields

Severity: ERROR

Identify records containing NULL or empty required fields.

Review source mappings and transformation logic.

Correct the source data or quarantine affected records.
Do not invent missing identifiers.

## Cross-Tenant Integrity Violations

Severity: ERROR

Investigate records without a corresponding reference
within the same organisation and processing date.

Verify authoritative tenant ownership and join conditions.

Quarantine affected records and investigate possible
unauthorized data exposure.

Do not reassign ownership without verification.

## Numeric Range Violations

Severity: Configurable

Review units, currency conversions, transformation logic,
and configured business thresholds.

Correct invalid values at the source where possible.

## Row Count Discrepancies

Severity: Configurable

Compare expected and observed record counts.

Investigate incomplete ingestion, duplicate processing,
unexpected source growth, and filtering logic.

Update expected counts only when supported by verified
source or business requirements.

## Recovery Criteria

- All ERROR-level violations resolved.
- Remaining warnings reviewed and documented.
- Quality gate returns exit code 0.
- Downstream processing can safely resume.

Never perform destructive remediation against production
tables without appropriate review and authorization.
