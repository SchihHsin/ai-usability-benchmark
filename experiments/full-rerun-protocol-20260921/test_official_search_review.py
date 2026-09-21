import copy,unittest
from review_gate import check
class OfficialSearchReview(unittest.TestCase):
 def test_only_exact_reviewed_quote_is_allowed(self):
  item={'sources':[{'event_id':'s','role':'search','text':'Official library 13.4 documentation'}],'applicability':{'M4':{'applicable':True}}}
  value={'metrics':[{'id':'M4','score':5}],'m2_documents':[],'m4_check':{'required_relations':['version'],'determination':'direct','evidence':[{'event_id':'s','quote':'Official library 13.4 documentation'}]}}
  failed=check(copy.deepcopy(value),copy.deepcopy(item),'predictors');self.assertIn('M4: missing official constraint citations',failed['execution_gate']['errors'])
  item['reviewed_official_search_evidence']=[{'event_id':'s','quote':'Official library 13.4 documentation'}]
  passed=check(copy.deepcopy(value),item,'predictors');self.assertEqual(passed['metrics'][0]['score'],5)
  value['m4_check']['evidence'][0]['quote']='library 13.4'
  failed=check(value,item,'predictors');self.assertIsNone(failed['metrics'][0]['score'])
if __name__=='__main__':unittest.main()
