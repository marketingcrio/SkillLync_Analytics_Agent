"""Smoke test for report_funnel.

Run: python tests/test_funnel.py [--month M --year Y]

Validates that the funnel report runs against the live warehouse and the
result passes basic sanity checks. Default period is the current month.

Exit code 0 = pass, 1 = fail.
"""

import argparse
import os
import sys
from datetime import datetime

# Allow running from repo root or from tests/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))

from query_warehouse import (  # noqa: E402
    report_funnel,
    report_funnel_by_source,
    report_funnel_by_segment,
    check_data_freshness,
)


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--month', type=int, default=datetime.now().month)
    parser.add_argument('--year', type=int, default=datetime.now().year)
    args = parser.parse_args()

    print(f"Running smoke test for {args.year}-{args.month:02d}")

    # 1. Freshness check (should not raise)
    print("→ check_data_freshness()")
    warning = check_data_freshness()
    if warning:
        print(f"  WARNING: {warning}")

    # 2. Overall funnel
    print("→ report_funnel()")
    rows = report_funnel(args.month, args.year)
    if not rows or len(rows) != 1:
        fail(f"report_funnel returned {len(rows) if rows else 0} rows, expected 1")

    r = rows[0]
    print(f"  {r}")

    leads = r.get('Leads') or 0
    demos_se = r.get('Demos_SE') or 0
    enrolls = r.get('Enrolls') or 0
    same_month = r.get('Same_Month_Enrolls') or 0
    revenue = r.get('Total_Sale_Value') or 0

    if leads == 0:
        print("  WARN: Leads = 0 — month may have no data yet")
    if enrolls > leads and leads > 0:
        fail(f"Enrolls ({enrolls}) > Leads ({leads}) — definitionally impossible")
    if same_month > enrolls:
        fail(f"Same_Month_Enrolls ({same_month}) > Enrolls ({enrolls}) — should be a subset")
    if enrolls > 0 and revenue == 0:
        print("  WARN: Enrolls > 0 but Total_Sale_Value = 0 — sale_value join may be incomplete")

    # 3. Source breakdown
    print("→ report_funnel_by_source()")
    src_rows = report_funnel_by_source(args.month, args.year)
    print(f"  {len(src_rows)} source rows")

    src_lead_total = sum((r.get('Leads') or 0) for r in src_rows)
    if leads > 0 and src_lead_total != leads:
        fail(f"Source breakdown Leads total ({src_lead_total}) != overall Leads ({leads})")

    # 4. Segment breakdown
    print("→ report_funnel_by_segment()")
    seg_rows = report_funnel_by_segment(args.month, args.year)
    print(f"  {len(seg_rows)} segment rows")

    seg_lead_total = sum((r.get('Leads') or 0) for r in seg_rows)
    # Segment is partitioned: every lead falls in exactly one segment, so totals should match
    if leads > 0 and seg_lead_total != leads:
        fail(f"Segment breakdown Leads total ({seg_lead_total}) != overall Leads ({leads})")

    print("\nPASS")


if __name__ == '__main__':
    main()
