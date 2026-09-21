import unittest
from quote_alignment import align
class QuoteAlignment(unittest.TestCase):
 def test_link_and_code(self):
  src='Before: consult [the complete documentation](https://example.org) for `configuration` details.'
  q='consult the complete documentation for configuration details.'
  got=align(q,src);self.assertIn(got,src);self.assertIn('https://example.org',got)
 def test_word_change_rejected(self):
  self.assertIsNone(align('The official version is compatible with all GPUs.','The official version is compatible with some GPUs.'))
 def test_ambiguous_rejected(self):
  q='This sufficiently long sentence occurs twice.';self.assertIsNone(align(q,q+' '+q))
 def test_empty_heading_anchor(self):
  src='# [](https://example.org/guide#heading)Complete installation documentation heading'
  q='# Complete installation documentation heading'
  got=align(q,src);self.assertIn(got,src);self.assertIn('https://example.org/guide#heading',got)
 def test_empty_anchor_does_not_allow_word_change(self):
  src='# [](https://example.org/guide#heading)Complete installation documentation heading'
  self.assertIsNone(align('# Incomplete installation documentation heading',src))
if __name__=='__main__':unittest.main()
