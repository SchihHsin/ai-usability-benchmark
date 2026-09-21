import unittest
from score_review import preserve_bounds
class ScoreReview(unittest.TestCase):
 def test_candidate_not_certain(self):
  m={'score':4,'lower':3,'upper':4,'status':'scored'};preserve_bounds(m);self.assertIsNone(m['score']);self.assertEqual(m['status'],'bounded');self.assertEqual(m['candidate_score'],4)
 def test_unverified_not_promoted(self):
  m={'score':None,'lower':1,'upper':5,'status':'insufficient_evidence'};preserve_bounds(m);self.assertEqual(m['status'],'insufficient_evidence')
 def test_equal_bound_stays_point(self):
  m={'score':4,'lower':4,'upper':4,'status':'scored'};preserve_bounds(m);self.assertEqual(m['score'],4)
if __name__=='__main__':unittest.main()
