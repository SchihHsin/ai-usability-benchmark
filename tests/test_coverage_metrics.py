import copy
import unittest
from scripts import coverage_metrics as c,run_log
from tests.test_document_metrics import DocumentTests

class CoverageTests(unittest.TestCase):
    def fixture(self):
        r,v=DocumentTests().fixture()
        r[0]['metadata']['rubric_version']=c.VERSION;v['rubric_version']=c.VERSION
        r[0]['metadata']['protocol'].update(m2_coverage_unit='section',m2_unit_rule='官方同版正文一级章节；标题不算正文')
        a,b=v['metrics'][1]['observation']['targets']
        a.update(acquisition_level='partial_body',score=3,final_official_state='partial',return_kind='excerpt',coverage=dict(unit_type='section',reference_units=['a','b','c'],returned_units=['a'],within_unit_truncation=False,reference=dict(url='https://example.com/A',version_scope='v1 full',captured_at='2026-09-15',tool='browser',content='abcdef',unit_spans={'a':[0,2],'b':[2,4],'c':[4,6]}),unit_evidence={'a':['e0'],'b':['e1']}))
        b['acquisition_level']='frame_only'
        self.refresh(v)
        return r,v
    def refresh(self,v):
        m=v['metrics'][1];m['observation']['aggregate']=c.aggregate(m['observation']['targets']);m['score']=m['observation']['aggregate']['band']
    def test_fraction_boundaries_and_format_independence(self):
        r,v=self.fixture();c.validate(r,v)
        a=v['metrics'][1]['observation']['targets'][0]
        a['coverage']['reference_units']=['a','b'];a['score']=4;self.refresh(v);c.validate(r,v)
        a['return_kind']='summary_or_preview';c.validate(r,v)
    def test_unknown_not_dropped(self):
        r,v=self.fixture();a=v['metrics'][1]['observation']['targets'][0];a['score']=None;a.pop('coverage');self.refresh(v);v['metrics'][1]['status']='pending';c.validate(r,v)
        self.assertIsNone(v['metrics'][1]['observation']['aggregate']['mean'])
    def test_missing_reference_and_false_complete_rejected(self):
        r,v=self.fixture();a=v['metrics'][1]['observation']['targets'][0]
        a['coverage']['reference']['content']=''
        with self.assertRaises(ValueError):c.validate(r,v)
        a.update(score=5,acquisition_level='complete_body',final_official_state='obtained');self.refresh(v)
        with self.assertRaises(ValueError):c.validate(r,v)
    def test_new_template_dispatch(self):
        r,_=self.fixture();v=run_log.metric_template(r);self.assertEqual(v['rubric_version'],c.VERSION);c.validate(r,v)
