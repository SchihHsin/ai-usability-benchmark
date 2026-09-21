import unittest
from review_normalization import completeness
class CompletenessReview(unittest.TestCase):
 def test_only_same_document_boundary_can_establish_truncation(self):
  item={'sources':[{'event_id':'e','text':'body truncated here'}]}
  for evidence,wanted in [([{'event_id':'e','quote':'truncated'}],'incomplete'),([{'event_id':'other','quote':'truncated'}],'unknown'),([],'unknown')]:
   doc={'event_id':'e','representation':'body','completeness':'incomplete','boundary_evidence':evidence};completeness(doc,item);self.assertEqual(doc['completeness'],wanted)
 def test_complete_requires_matching_independent_reference(self):
  for ref,wanted in [({},'unknown'),({'id':'r'},'complete')]:
   doc={'event_id':'e','representation':'body','completeness':'complete','reference':ref}
   completeness(doc,{'sources':[],'completeness_references':{'r':{'event_id':'e','verified_complete':True}}});self.assertEqual(doc['completeness'],wanted)
if __name__=='__main__':unittest.main()
