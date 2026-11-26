import unittest
from analysis.matrix_receipt_audit import audit_matrix, EXPECTED, PHASES


def fixture():
    return {'runs': [dict(run=key, arm=arm, cls='matrix', n_phases=8, all_stop=True,
                          gates={'build':0,'test':0,'lint':0}, gates_green=True,
                          engage_check='pass (observed calls)', total_input=80, total_output=16,
                          phases=[dict(phase=p, input=10, output=2, stopReason='stop') for p in PHASES])
                     for key, arm in EXPECTED.items()]}


class MatrixReceiptTests(unittest.TestCase):
    def test_complete_projection_is_not_independent_proof(self):
        report = audit_matrix(fixture())
        self.assertTrue(report['projection_consistent'])
        self.assertFalse(report['independently_verified'])

    def test_missing_matrix_run(self):
        d = fixture(); d['runs'].pop()
        self.assertEqual(audit_matrix(d)['missing_runs'], ['R14'])
        self.assertFalse(audit_matrix(d)['projection_consistent'])

    def test_unknown_engagement_does_not_certify(self):
        d = fixture(); d['runs'][1]['engage_check'] = 'unknown'
        self.assertEqual(audit_matrix(d)['rows'][1]['problems'], ['engagement_unconfirmed'])

    def test_missing_counter_does_not_become_zero(self):
        d = fixture(); d['runs'][0]['phases'][0]['input'] = None
        self.assertIn('input_usage_unknown', audit_matrix(d)['rows'][0]['problems'])

    def test_duplicate_phase_and_empty_phase_list(self):
        d = fixture(); d['runs'][0]['phases'][0]['phase'] = PHASES[1]
        self.assertIn('missing_duplicate_or_unexpected_phase', audit_matrix(d)['rows'][0]['problems'])
        d['runs'][0]['phases'] = []
        self.assertIn('phase_stop_unconfirmed', audit_matrix(d)['rows'][0]['problems'])

    def test_total_mismatch(self):
        d = fixture(); d['runs'][0]['total_input'] += 1
        self.assertIn('input_total_mismatch', audit_matrix(d)['rows'][0]['problems'])

    def test_boolean_is_not_numeric_gate(self):
        d = fixture(); d['runs'][0]['gates']['build'] = False
        self.assertIn('gates_unconfirmed', audit_matrix(d)['rows'][0]['problems'])

    def test_duplicate_run_and_wrong_arm(self):
        d = fixture(); d['runs'][0]['arm'] = 'a2'; d['runs'].append(d['runs'][0])
        self.assertEqual(audit_matrix(d)['rows'][0]['problems'], ['unexpected_run_or_arm','duplicate_run'])

    def test_voids_do_not_change_frozen_matrix(self):
        d = fixture(); d['runs'].append({'cls':'void','run':'R06a'})
        self.assertTrue(audit_matrix(d)['projection_consistent'])
