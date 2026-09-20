import copy
import unittest
from scripts import document_metrics as d,run_log

class DocumentTests(unittest.TestCase):
    def fixture(self):
        rows=[dict(type='run_start',id='start',metadata=dict(rubric_version=d.VERSION,protocol=dict(requirements=[dict(id='R',description='诊断',importance='core')])))]
        for i in range(4):
            rows += [dict(type='tool_request',id=f'f{i}',role='fetch'),dict(type='tool_dispatch',id=f'd{i}',request_id=f'f{i}'),dict(type='tool_result',id=f'r{i}',request_id=f'f{i}',tool_status='ok')]
        rows.append(dict(type='run_end',id='end',stop_reason='complete'))
        v=run_log.metric_template(rows)
        v['evidence']=[dict(id=f'e{i}',event_id=f'r{i}',field='response') for i in range(4)]
        docs=[]
        for name,indices,score,kind in [('A',[0,1,2],5,'complete_body'),('B',[3],2,'frame_only')]:
            docs.append(dict(target_id=name,description='独立文档'+name,requirement_refs=['R'],identity_basis='相同官方正文的重试',urls=['https://example.com/'+name],score=score,return_kind=kind,state_basis='返回原文证据',initial_state='not_obtained',final_official_state='obtained' if score==5 else 'not_obtained',reason='文档最终取得状态',event_refs=[f'r{i}' for i in indices],evidence_refs=[f'e{i}' for i in indices]))
        m=v['metrics'][1];m['observation']=dict(targets=docs,aggregate=d.aggregate(docs),fetch_inventory=[dict(request_id=f'f{i}',source_class='official',document_id='A' if i<3 else 'B',reason='官方文档URL',event_refs=[f'r{i}']) for i in range(4)])
        m.update(score=4,status='scored',reason='两篇文档等权')
        return rows,v
    def test_document_mean_not_attempt_mean(self):
        r,v=self.fixture();d.validate(r,v)
        self.assertEqual(v['metrics'][1]['observation']['aggregate']['mean'],3.5)
        self.assertEqual(v['metrics'][7]['observation']['total_calls'],4)
    def test_duplicate_document_or_omitted_failure_rejected(self):
        r,v=self.fixture();obs=v['metrics'][1]['observation']
        with self.assertRaises(ValueError):d.aggregate(obs['targets']+[obs['targets'][0]])
        obs['fetch_inventory'].pop()
        with self.assertRaises(ValueError):d.validate(r,v)
    def test_mirror_cannot_count_as_official_recovery(self):
        r,v=self.fixture();obs=v['metrics'][1]['observation'];obs['fetch_inventory'][2]['source_class']='third_party'
        with self.assertRaises(ValueError):d.validate(r,v)
    def test_empty_template_pending_is_valid(self):
        r,_=self.fixture();d.validate(r,run_log.metric_template(r))
