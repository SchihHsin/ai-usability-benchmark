import unittest,copy,json,importlib.util
from pathlib import Path
from assessment_gate import check
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('overall',ROOT/'frozen-skill/scripts/overall_score.py'); overall=importlib.util.module_from_spec(spec);spec.loader.exec_module(overall)
class Checks(unittest.TestCase):
 def fixture(self):
  item={'sources':[{'event_id':'a','url':'https://example.org/a','role':'fetch','text':'导航'},{'event_id':'b','url':'https://example.org/a#x','role':'fetch','text':'正文，v2适用x'},{'event_id':'c','url':'https://example.org/c','role':'fetch','text':'导航'}],'final':'安装命令','applicability':{k:{'applicable':True,'scope':'工具版本'} for k in ['M4','M9','M10']}}
  docs=[{'event_id':eid,'ownership':'official','representation':state,'completeness':'unknown','evidence':[{'event_id':eid,'quote':quote}]} for eid,state,quote in [('a','frame','导航'),('b','body','正文'),('c','frame','导航')]]
  value={'metrics':[{'id':f'M{i}','score':5,'status':'scored'} for i in range(1,9)],'m2_documents':docs,'m4_check':{'required_relations':['工具与设备'],'missing_relations':[],'unresolved_conflicts':[],'determination':'direct','evidence':[{'event_id':'b','quote':'v2适用x'}]}}
  return item,value
 def test_retry_unknown_average(self):
  i,v=self.fixture();r=check(v,i,'predictors');m=r['metrics'][1];self.assertEqual((m['lower'],m['upper']),(3,3.5));self.assertIsNone(m['score']);self.assertTrue(r['execution_gate']['passed'])
 def test_missing_doc_rejected(self):
  i,v=self.fixture();v['m2_documents'].pop();r=check(v,i,'predictors');self.assertIsNone(r['metrics'][1]['score']);self.assertFalse(r['execution_gate']['passed'])
 def test_false_complete_rejected(self):
  i,v=self.fixture();v['m2_documents'][1]['completeness']='complete';r=check(v,i,'predictors');self.assertIsNone(r['metrics'][1]['score'])
 def test_verified_reference(self):
  i,v=self.fixture();d=v['m2_documents'][1];d.update(completeness='complete',reference={'id':'r'});i['completeness_references']={'r':{'verified_complete':True,'event_id':'b'}};r=check(v,i,'predictors');self.assertEqual(r['metrics'][1]['score'],3.5)
 def test_m4_missing_relation(self):
  i,v=self.fixture();v['m4_check']['missing_relations']=['芯片'];r=check(v,i,'predictors');self.assertIsNone(r['metrics'][3]['score'])
 def test_m4_conflict(self):
  i,v=self.fixture();v['metrics'][3]['score']=3;v['m4_check']['unresolved_conflicts']=['冲突'];self.assertIsNone(check(v,i,'predictors')['metrics'][3]['score'])
 def test_combination_requires_explanation(self):
  i,v=self.fixture();v['metrics'][3]['score']=4;v['m4_check']['determination']='combined';self.assertIsNone(check(v,i,'predictors')['metrics'][3]['score'])
 def test_na_and_empty_final_citation(self):
  i,v=self.fixture();v={'m9_m10':[{'id':'M9','score':5,'status':'scored','evidence':[]},{'id':'M10','score':5,'status':'scored','evidence':[]}]};i['applicability']['M9']['applicable']=False;r=check(v,i,'outcome');self.assertEqual(r['m9_m10'][0]['status'],'not_applicable');self.assertIsNone(r['m9_m10'][1]['score'])
 def test_m11_no_imputation(self):
  m={f'M{i}':{'score':5,'status':'scored'} for i in range(1,9)};self.assertEqual(overall.calculate(m)['score'],100);m['M4'].update(score=None,status='not_applicable');self.assertIsNone(overall.calculate(m)['score']);self.assertEqual(overall.calculate(m)['missing_inputs'][0]['metric'],'M4')
 def test_all_tasks_scoped_and_original_questions(self):
  t=json.loads((ROOT/'tasks.json').read_text())['tasks'];self.assertEqual(len(t),26)
  for key,v in t.items():
   for e in ['cann','cuda']:
    self.assertNotIn('展开 ·',v[e]);self.assertNotIn('\\_',v[e]);self.assertEqual(v['applicability'][e]['M4']['applicable'],key!='Z')
if __name__=='__main__':unittest.main()
