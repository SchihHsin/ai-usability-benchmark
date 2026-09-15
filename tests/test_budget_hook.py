import concurrent.futures
import json
from pathlib import Path
import tempfile
import unittest
from scripts.budget_hook import decide, rejection_for

class BudgetTests(unittest.TestCase):
    def test_parallel_limit_and_denial(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'ledger';limits=dict(search=4,fetch=8)
            def attempt(i):return decide(p,dict(hook_event_name='PreToolUse',session_id='one',tool_name='WebFetch',tool_input={'url':str(i)}),limits)
            with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:out=list(pool.map(attempt,range(20)))
            self.assertEqual(sum(x['hookSpecificOutput'].get('permissionDecision')!='deny' for x in out),8)
            self.assertEqual(len(p.read_text().splitlines()),20)
            e=dict(hook_event_name='PreToolUse',session_id='one',tool_name='WebSearch',tool_input={})
            self.assertNotIn('permissionDecision',decide(p,e,limits)['hookSpecificOutput'])
            e['session_id']='other'
            with self.assertRaises(ValueError):decide(p,e,limits)
    def test_zero_restart_and_corrupt_state(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'ledger';e=dict(hook_event_name='PreToolUse',session_id='one',tool_name='WebFetch')
            self.assertEqual(decide(p,e,dict(search=1,fetch=0))['hookSpecificOutput']['permissionDecision'],'deny')
            with self.assertRaises(ValueError):decide(p,e,dict(search=1,fetch=8))
            p.write_text('broken')
            with self.assertRaises(ValueError):decide(p,e,dict(search=1,fetch=0))

    def test_rejection_is_bound_to_tool_call_id(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'ledger'
            decide(p,dict(hook_event_name='PreToolUse',session_id='one',tool_name='WebFetch',tool_use_id='denied'),dict(search=0,fetch=0))
            self.assertIsNotNone(rejection_for(p,'denied'))
            self.assertIsNone(rejection_for(p,'actual-webpage-with-denial-text'))
