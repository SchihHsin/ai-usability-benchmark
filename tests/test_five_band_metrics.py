import copy
import unittest
from scripts import five_band_metrics as p


class FiveBandTests(unittest.TestCase):
    def rows(self, n=2):
        return [dict(type='run_start', metadata=dict(rubric_version=p.VERSION, protocol=dict(
            requirements=[dict(id='R', description='操作', importance='core')],
            acquisition_targets=[dict(id=str(i),description='目标'+str(i),requirement_refs=['R']) for i in range(n)]))),
            dict(type='tool_request',id='s',role='search'),dict(type='tool_dispatch',request_id='s')]

    def test_mean_and_gaps(self):
        a=p.aggregate([dict(score=s) for s in [5,5,5,5,1]])
        self.assertEqual((a['mean'],a['band'],a['not_obtained_count']), (4.2,4,1))
        self.assertEqual(p.aggregate([dict(score=4),dict(score=5)])['band'],5)
        self.assertIsNone(p.aggregate([dict(score=5),dict(score=None)])['mean'])
        self.assertIsNone(p.aggregate([])['band'])
        for x in [True,2.5,0,6]:
            with self.assertRaises(ValueError):p.aggregate([dict(score=x)])

    def test_cost_boundaries(self):
        self.assertEqual([p.cost_band(i) for i in range(11)], [None,5,5,4,4,3,3,2,2,1,1])

    def test_template_and_scope(self):
        rows=self.rows();v=p.template(rows);p.validate(rows,v)
        for mutate in ['duplicate','remove','new']:
            bad=copy.deepcopy(v);items=bad['metrics'][1]['observation']['targets']
            if mutate=='duplicate':items.append(copy.deepcopy(items[0]))
            elif mutate=='remove':items.pop()
            else:items[0]['target_id']='new'
            with self.assertRaises(ValueError):p.validate(rows,bad)
        v['metrics'][1].update(score=5,status='scored',reason='未知不能忽略')
        with self.assertRaises(ValueError):p.validate(rows,v)

    def test_scored_targets_and_cost(self):
        rows=self.rows();v=p.template(rows);m=v['metrics'][1]
        for t,s in zip(m['observation']['targets'],[4,5]):
            t.update(score=s,initial_state='partial' if s==4 else 'obtained',final_official_state='obtained',reason='原文支持',evidence_refs=['e'],event_refs=['s'])
            if s==4:t['recovery_event_refs']=['s']
        m['observation']['aggregate']=p.aggregate(m['observation']['targets'])
        m.update(score=5,status='scored',reason='均值4.5')
        v['metrics'][7].update(score=5,status='scored',reason='一次实际调用')
        p.validate(rows,v)
        v['metrics'][7]['score']=4
        with self.assertRaises(ValueError):p.validate(rows,v)
        v['metrics'][7]['score']=5
        m['observation']['targets'][0]['recovery_event_refs']=[]
        with self.assertRaises(ValueError):p.validate(rows,v)

    def test_no_dispatch_has_no_cost_score(self):
        rows=self.rows()[:1];v=p.template(rows)
        v['metrics'][7].update(score=5,status='scored',reason='没有执行')
        with self.assertRaises(ValueError):p.validate(rows,v)

if __name__=='__main__':unittest.main()
