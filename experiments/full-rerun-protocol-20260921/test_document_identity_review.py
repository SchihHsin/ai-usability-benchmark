import unittest
from review_gate import check
class DocumentIdentityReview(unittest.TestCase):
 def test_proxy_retry_does_not_add_independent_document(self):
  item={'sources':[{'event_id':'first','role':'fetch','url':'https://example.org/doc/','text':'body one'}, {'event_id':'proxy','role':'fetch','url':'https://proxy/doc/','text':'blocked'}, {'event_id':'last','role':'fetch','url':'https://example.org/doc/index.html','text':'body last'}],'applicability':{},'reviewed_document_groups':dict(first='same',proxy='same',last='same')}
  value={'metrics':[{'id':'M2','score':None}],'m2_documents':[{'event_id':e,'ownership':own,'representation':'body','completeness':'unknown','evidence':[{'event_id':e,'quote':text}]} for e,own,text in [('first','official','body one'),('proxy','unknown','blocked'),('last','official','body last')]]}
  out=check(value,item,'predictors');self.assertEqual(out['execution_gate']['errors'],[]);self.assertEqual((out['metrics'][0]['lower'],out['metrics'][0]['upper']),(4,5));self.assertEqual(len(out['m2_documents']),3)
if __name__=='__main__':unittest.main()
