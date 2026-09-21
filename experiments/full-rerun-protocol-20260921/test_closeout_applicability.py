import unittest
from review_gate import check
class ApplicabilityAliases(unittest.TestCase):
 def test_applicable_task_rejects_all_na_aliases(self):
  item={'sources':[], 'final':'', 'applicability':{'M9':{'applicable':True,'scope':'version relation'}}}
  for status in ['N/A','not_applicable','NA','not applicable']:
   v={'m9_m10':[{'id':'M9','score':None,'status':status,'evidence':[]}]}
   gate=check(v,item,'outcome')
   self.assertIn('M9: contradicts predefined applicability',str(gate))
 def test_concept_task_stays_na(self):
  item={'sources':[], 'final':'', 'applicability':{'M9':{'applicable':False,'scope':'concept only'}}}
  v={'m9_m10':[{'id':'M9','score':5,'status':'scored'}]}
  check(v,item,'outcome')
  self.assertEqual(v['m9_m10'][0]['status'],'not_applicable')
if __name__=='__main__':unittest.main()
