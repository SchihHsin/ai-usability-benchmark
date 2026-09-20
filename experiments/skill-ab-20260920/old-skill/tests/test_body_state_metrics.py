import unittest
from scripts import body_state_metrics as p, five_band_metrics as previous, run_log


class BodyStateTests(unittest.TestCase):
    def fixture(self, n=1):
        rows=[dict(type='run_start',id='start',metadata=dict(rubric_version=p.VERSION,protocol=dict(
            requirements=[dict(id='R',description='操作',importance='core')],
            acquisition_targets=[dict(id=str(i),description='正文'+str(i),requirement_refs=['R']) for i in range(n)]))),
            dict(type='tool_request',id='f',role='fetch'),dict(type='tool_dispatch',id='d',request_id='f'),
            dict(type='tool_result',id='r',request_id='f',tool_status='ok'),dict(type='run_end',id='end',stop_reason='complete')]
        v=run_log.metric_template(rows)
        v['evidence']=[dict(id='e',event_id='r',field='response')]
        return rows,v

    def score(self, v, scores, initial='obtained'):
        m=v['metrics'][1]
        kinds=['page_not_obtained','frame_only','summary_or_preview','incomplete_body','complete_body']
        for t,s in zip(m['observation']['targets'],scores):
            t.update(score=s,return_kind=kinds[s-1],state_basis='实际返回状态证据',initial_state=initial,
                     final_official_state='not_obtained' if s<=2 else 'partial' if s<=4 else 'obtained',
                     reason='按返回状态判定',event_refs=['r'],evidence_refs=['e'])
        m['observation']['aggregate']=p.aggregate(m['observation']['targets'])
        m.update(score=m['observation']['aggregate']['band'],status='scored',reason='目标等权平均')
        return m

    def test_five_observable_states_and_mean(self):
        rows,v=self.fixture(5);m=self.score(v,[2,3,4,5,5]);p.validate(rows,v)
        self.assertEqual(m['score'],4)
        self.assertEqual(m['observation']['aggregate']['mean'],3.8)
        self.assertEqual(m['observation']['aggregate']['partial_count'],2)
        self.assertEqual(m['observation']['aggregate']['not_obtained_count'],1)
        for s in range(1,6):
            rows,v=self.fixture();self.score(v,[s]);p.validate(rows,v)

    def test_recovery_complete_gets_five(self):
        rows,v=self.fixture();self.score(v,[5],initial='not_obtained');p.validate(rows,v)
        with self.assertRaises(ValueError):previous.validate(rows,v)

    def test_truncated_body_gets_four_without_recovery(self):
        rows,v=self.fixture();self.score(v,[4]);p.validate(rows,v)
        with self.assertRaises(ValueError):previous.validate(rows,v)

    def test_state_and_evidence_basis_required(self):
        for key,bad in [('return_kind','complete_body'),('state_basis','')]:
            rows,v=self.fixture();m=self.score(v,[4]);m['observation']['targets'][0][key]=bad
            with self.assertRaises(ValueError):p.validate(rows,v)

    def test_pagination_is_one_target_not_multiple_scores(self):
        rows,v=self.fixture();rows.insert(-1,dict(type='tool_request',id='f2',role='fetch'))
        rows.insert(-1,dict(type='tool_dispatch',id='d2',request_id='f2'))
        rows.insert(-1,dict(type='tool_result',id='r2',request_id='f2',tool_status='ok'))
        v['metrics'][7]['observation']['C']['F']=2
        v['metrics'][7]['observation']['total_calls']=2
        m=self.score(v,[5],initial='partial');m['observation']['targets'][0]['event_refs'].append('r2')
        p.validate(rows,v);self.assertEqual(m['observation']['aggregate']['target_count'],1)
        m['observation']['targets'].append(dict(m['observation']['targets'][0]))
        with self.assertRaises(ValueError):p.validate(rows,v)

    def test_unknown_does_not_disappear(self):
        rows,v=self.fixture(2);self.assertEqual(v['rubric_version'],p.VERSION)
        p.validate(rows,v)
        a=p.aggregate([dict(score=5),dict(score=None)])
        self.assertIsNone(a['mean']);self.assertIsNone(a['band'])
        self.assertEqual(p.aggregate([dict(score=4),dict(score=5)])['band'],5)

if __name__=='__main__':unittest.main()
