"""Output-contract gate: verify an upstream's output summary before letting a downstream run.

A contract is configured per (downstream job, upstream job) and checked against the
upstream's successful attempt detail (its output summary) from the same orchestration.
Rules:
  - min_rows: summary["artifact_rows"] must be >= min_rows (catches empty successes).
  - required_field: the named field must be present and non-null in the summary.
"""

from __future__ import annotations

from typing import Any


def check_upstream_contracts(
    contracts: list[dict[str, Any]],
    upstream_summaries: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return a list of violations; empty means every contract passed.

    contracts: rows with upstream_name / min_rows / required_field.
    upstream_summaries: upstream job name -> its attempt detail (output summary).
    """
    violations: list[dict[str, Any]] = []
    for c in contracts:
        name = c["upstream_name"]
        summary = upstream_summaries.get(name)
        if summary is None:
            violations.append(
                {
                    "upstream": name,
                    "rule": "upstream_summary",
                    "expected": "success summary in this orchestration",
                    "actual": None,
                    "message": f"上游 {name} 本次编排没有可核验的成功产出摘要",
                }
            )
            continue
        min_rows = c.get("min_rows") or 0
        actual_rows = summary.get("artifact_rows")
        if not isinstance(actual_rows, int) or actual_rows < min_rows:
            violations.append(
                {
                    "upstream": name,
                    "rule": "min_rows",
                    "expected": min_rows,
                    "actual": actual_rows,
                    "message": f"上游 {name} 产出行数 {actual_rows} 低于契约下限 {min_rows}",
                }
            )
        field = (c.get("required_field") or "").strip()
        if field:
            value = summary.get(field)
            if value is None:
                violations.append(
                    {
                        "upstream": name,
                        "rule": "required_field",
                        "expected": field,
                        "actual": None,
                        "message": f"上游 {name} 产出摘要缺少约定字段 {field}",
                    }
                )
    return violations
