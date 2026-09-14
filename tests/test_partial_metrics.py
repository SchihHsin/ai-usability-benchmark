import copy
import unittest
from scripts import partial_metrics as p


class ConfirmedMetricsTests(unittest.TestCase):
    def setUp(self):
        self.rows=[dict(type='run_start', metadata=dict(rubric_version=p.VERSION, protocol=dict(requirements=[dict(id='R1',importance='core',description='操作')]))),
                   dict(type='tool_request',id='s1',role='search'),dict(type='tool_dispatch',request_id='s1'),
                   dict(type='tool_request',id='f1',role='fetch'),dict(type='tool_dispatch',request_id='f1'),
                   dict(type='tool_request',id='f2',role='fetch')]
        self.v=p.template(self.rows)

    def scored(self, metric, score):
        v=copy.deepcopy(self.v)
        v['requirements'][0].update(status='reviewed',reason='依据原文',evidence_refs=['e1'])
        m=v['metrics'][metric-1]
        m.update(score=score,status='scored',reason='按完整方案检查',requirement_refs=['R1'],evidence_refs=['e1'])
        if metric==3:m['official_body_observed']=True
        if metric==10:m['applicable_conditions']='题目声明的环境'
        return v

    def test_template_preserves_unknown_costs(self):
        p.validate(self.rows,self.v)
        self.assertEqual(self.v['metrics'][7]['observation']['C'],dict(S=1,F=1,R=None,U=None))

    def test_only_confirmed_metrics_can_have_scores(self):
        for i in [1,2,4,5,6,7,8,9,11]:
            with self.subTest(i=i),self.assertRaises(ValueError):p.validate(self.rows,self.scored(i,3))
        p.validate(self.rows,self.scored(3,3))
        p.validate(self.rows,self.scored(10,4))
        for score in [True,3.0,0,6]:
            with self.assertRaises(ValueError):p.validate(self.rows,self.scored(10,score))

    def test_m3_requires_body_and_frozen_importance(self):
        v=self.scored(3,1);v['metrics'][2]['official_body_observed']=False
        with self.assertRaises(ValueError):p.validate(self.rows,v)
        rows=copy.deepcopy(self.rows);del rows[0]['metadata']['protocol']['requirements'][0]['importance']
        with self.assertRaises(ValueError):p.validate(rows,self.scored(3,3))
        with self.assertRaises(ValueError):p.validate(self.rows,self.scored(3,4))

    def test_m10_requires_completed_review_and_scope(self):
        v=self.scored(10,5);v['requirements'][0]['status']='pending'
        with self.assertRaises(ValueError):p.validate(self.rows,v)
        v=self.scored(10,5);v['metrics'][9]['scope']='extra_solution'
        with self.assertRaises(ValueError):p.validate(self.rows,v)

    def test_costs_count_dispatched_ids_not_model_numbers(self):
        obs=self.v['metrics'][7]['observation'];obs.update(retry_request_ids=['f1'],no_body_fetch_request_ids=['f1'],C=dict(S=1,F=1,R=1,U=1))
        self.v['metrics'][7].update(reason='同目标重试且没有目标正文',evidence_refs=['e1'])
        p.validate(self.rows,self.v)
        obs['C']['F']=6
        with self.assertRaises(ValueError):p.validate(self.rows,self.v)
        for ids in [['f2'],['s1'],['f1','f1']]:
            with self.assertRaises(ValueError):p.cost_vector(self.rows,no_body=ids)

    def test_m2_states_and_no_overall(self):
        obs=self.v['metrics'][1]['observation'];obs['targets']=[dict(target_id='t1',initial_state='not_obtained',final_official_state='obtained',evidence_refs=['e1'])]
        p.validate(self.rows,self.v)
        obs['targets'][0]['final_official_state']='third_party_obtained'
        with self.assertRaises(ValueError):p.validate(self.rows,self.v)
        self.v=p.template(self.rows);self.v['overall']=.8
        with self.assertRaises(ValueError):p.validate(self.rows,self.v)

if __name__=='__main__':unittest.main()
