import copy
import json
from pathlib import Path
import tempfile
import unittest
from scripts import run_log as log


class TwoFileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.run = self.root / 'run'
        self.body = self.root / 'input'
        self.body.write_bytes(b'question\r\n')
        self.metadata = dict(run_id='r1', task_id='D', ecosystem='test', model_id='test',
                             repetition=1, protocol_version='test', rubric_version='v2-draft')
        log.init_run(self.run, self.metadata, self.body)

    def complete(self):
        log.begin(self.run, 's1', 'search', 'synthetic', {'query': 'q'})
        log.dispatch(self.run, 's1')
        self.body.write_bytes('正文\r\n'.encode())
        log.finish(self.run, 's1', self.body, 'ok', {})
        log.end_run(self.run, self.body, 'task_complete')
        payload = log.events(self.run)[3]['response']
        return dict(rubric_version='v2-draft', assessor={'id':'test'}, limitations=[],
            evidence=[dict(id='e1', event_id='s1.result', field='response', sha256=payload['sha256'], start=0, end=2, quote='正文')],
            requirements=[dict(id='R1', evidence_refs=['e1'])], issues=[],
            metrics=[dict(id='M2', score=None, event_refs=['s1'])], overall=None)

    def test_two_files_exact_bytes_and_revisions(self):
        value = self.complete()
        log.save_evaluation(self.run, value)
        log.save_evaluation(self.run, value)
        self.assertEqual(sorted(p.name for p in self.run.iterdir()), ['evaluation.json','process.jsonl'])
        self.assertEqual(log.unpack(log.events(self.run)[3]['response']), '正文\r\n'.encode())
        self.assertEqual(len(log.read_json(self.run/'evaluation.json')['revisions']), 2)
        self.assertEqual(log.check(self.run)['issues'], [])
        with self.assertRaises(ValueError):
            log.begin(self.run, 'late', 'fetch', 'test', {})

    def test_pending_and_blocked_not_counted_as_dispatched(self):
        log.begin(self.run, 's1', 'search', 'test', {})
        log.begin(self.run, 'f1', 'fetch', 'test', {}, parent='s1')
        self.body.write_bytes(b'blocked')
        log.finish(self.run, 'f1', self.body, 'not_dispatched', {})
        result = log.check(self.run)
        self.assertEqual(result['counts']['requested'], dict(search=1,fetch=1,other=0))
        self.assertEqual(result['counts']['dispatched'], dict(search=0,fetch=0,other=0))
        self.assertEqual(result['counts']['not_dispatched']['fetch'],1)
        self.assertTrue(any('未保存返回' in s for s in result['issues']))

    def test_duplicate_and_dispatch_validation(self):
        log.begin(self.run, 's1', 'search', 'test', {})
        with self.assertRaises(ValueError): log.begin(self.run, 's1', 'search', 'test', {})
        with self.assertRaises(ValueError): log.finish(self.run, 's1', self.body, 'ok', {})
        log.dispatch(self.run, 's1')
        with self.assertRaises(ValueError): log.dispatch(self.run, 's1')
        with self.assertRaises(ValueError): log.finish(self.run, 's1', self.body, 'not_dispatched', {})
        log.finish(self.run, 's1', self.body, 'error', {})
        with self.assertRaises(ValueError): log.finish(self.run, 's1', self.body, 'ok', {})
        with self.assertRaises(ValueError): log.begin(self.run, 'f1', 'fetch', 'test', {}, parent='missing')
        with self.assertRaises(FileExistsError): log.init_run(self.run, self.metadata, self.body)

    def test_evidence_draft_and_version_rejected(self):
        value = self.complete()
        for mutation in ('quote','event','span','hash','ref','version','score','overall'):
            v = copy.deepcopy(value)
            if mutation=='quote': v['evidence'][0]['quote']='假'
            if mutation=='event': v['evidence'][0]['event_id']='missing'
            if mutation=='span': v['evidence'][0]['end']=100
            if mutation=='hash': v['evidence'][0]['sha256']='bad'
            if mutation=='ref': v['requirements'][0]['evidence_refs']=['missing']
            if mutation=='version': v['rubric_version']='2026-09-14'
            if mutation=='score': v['metrics'][0]['score']=5
            if mutation=='overall': v['overall']=.9
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): log.save_evaluation(self.run,v)
        self.assertEqual(log.read_json(self.run/'evaluation.json')['revisions'], [])

    def test_corruption_and_process_binding(self):
        log.save_evaluation(self.run,self.complete())
        rows=log.events(self.run)
        rows[3]['response']['content']='changed'
        (self.run/'process.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
        issues=log.check(self.run)['issues']
        self.assertTrue(any('哈希' in s for s in issues))
        self.assertIn('评价与过程哈希不符',issues)

    def test_self_report_remains_in_process(self):
        self.body.write_text('自评及简短依据', encoding='utf-8')
        log.report(self.run, 'm7', self.body, 'self_report')
        row=log.events(self.run)[-1]
        self.assertEqual(row['type'], 'self_report')
        self.assertEqual(log.unpack(row['content']).decode(), '自评及简短依据')
        self.assertEqual(len(list(self.run.iterdir())), 2)

    def test_legacy_scorer_rejects_draft_version(self):
        import score_template
        record={**self.metadata, 'raw':{}, 'evidence_refs':{}}
        with self.assertRaises(ValueError):
            score_template.score_records([record], (2026,9))

    def test_binary_roundtrip_and_credentials(self):
        body=b'\xff\x00\r\n'
        self.assertEqual(log.unpack(log.pack(body)),body)
        with self.assertRaises(ValueError): log.begin(self.run,'../outside','fetch','test',{})
        with self.assertRaises(ValueError): log.begin(self.run,'s1','search','test',{'cookie':'secret'})
        self.assertEqual(len(log.events(self.run)),1)

if __name__=='__main__': unittest.main()
