#!/usr/bin/env python3
"""Audit the exported frozen matrix without rewriting data or protocol results.

This checks the generated data.json projection, not original provider receipts.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import stat

ARMS = ('a0','a1m','a2','a3','a0','a3','a1m','a2','a0','a2','a3','a1m','a0','a0')
EXPECTED = {f'R{i:02d}': arm for i, arm in enumerate(ARMS, 1)}
PHASES = ('plan','review-plan','implement','review-code','validate','approve','writeback','commit')


def nonnegative_int(value):
    return type(value) is int and value >= 0


def audit_matrix(data):
    if not isinstance(data, dict) or not isinstance(data.get('runs'), list):
        raise ValueError('expected generated data.json with runs array')
    if any(not isinstance(row, dict) for row in data['runs']):
        raise ValueError('invalid run entry')
    matrix = [row for row in data['runs'] if row.get('cls') == 'matrix']
    ids = [row.get('run') for row in matrix]
    if any(not isinstance(key, str) for key in ids):
        raise ValueError('invalid matrix run identity')
    counts = Counter(ids)
    rows = []
    for row in matrix:
        key = row['run']
        problems = []
        if key not in EXPECTED or row.get('arm') != EXPECTED.get(key):
            problems.append('unexpected_run_or_arm')
        if counts[key] != 1:
            problems.append('duplicate_run')
        phases = row.get('phases')
        if not isinstance(phases, list) or any(not isinstance(p, dict) for p in phases):
            phases = []
            problems.append('invalid_phases')
        names = [p.get('phase') for p in phases]
        if any(not isinstance(name, str) for name in names) or Counter(names) != Counter(PHASES):
            problems.append('missing_duplicate_or_unexpected_phase')
        if row.get('n_phases') != len(phases) or type(row.get('n_phases')) is not int:
            problems.append('phase_count_mismatch')
        if not phases or not all(p.get('stopReason') == 'stop' for p in phases) or row.get('all_stop') is not True:
            problems.append('phase_stop_unconfirmed')
        gates = row.get('gates')
        if not isinstance(gates, dict) or not all(type(gates.get(g)) is int and gates[g] == 0 for g in ('build','test','lint')) or row.get('gates_green') is not True:
            problems.append('gates_unconfirmed')
        for field in ('input','output'):
            values = [p.get(field) for p in phases]
            total = row.get('total_' + field)
            if not values or not all(nonnegative_int(v) for v in values) or not nonnegative_int(total):
                problems.append(field + '_usage_unknown')
            elif sum(values) != total:
                problems.append(field + '_total_mismatch')
        engage = row.get('engage_check')
        if not isinstance(engage, str) or not re.fullmatch(r'pass(?: \([^\r\n]+\))?', engage):
            problems.append('engagement_unconfirmed')
        rows.append({'run':key, 'status':'projection_consistent' if not problems else 'review_required', 'problems':problems})
    missing = sorted(set(EXPECTED) - set(ids))
    complete = len(matrix) == len(EXPECTED) and not missing and all(not row['problems'] for row in rows)
    return {'scope':'generated projection only', 'independently_verified':False,
            'expected_runs':len(EXPECTED), 'observed_runs':len(matrix), 'missing_runs':missing,
            'projection_consistent':complete, 'rows':rows,
            'limitation':'An unconfirmed projection is not evidence of product failure. Reconcile with original engagement logs and provider receipts; do not silently change the frozen matrix.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('data', type=Path)
    args = parser.parse_args()
    try:
        st = args.data.stat()
        if not stat.S_ISREG(st.st_mode) or st.st_size > 64*1024*1024:
            raise ValueError('expected bounded regular JSON file')
        result = audit_matrix(json.loads(args.data.read_text(encoding='utf-8')))
    except (OSError, ValueError, RecursionError):
        print('invalid or unreadable matrix projection')
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result['projection_consistent'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
