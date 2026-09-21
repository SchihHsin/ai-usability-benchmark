import unittest
from unittest.mock import patch
import completion_guard as guard
class CompletionGuard(unittest.TestCase):
 def outcome(self,answer,dispatch=False):
  events=([{'type':'tool_dispatch'}] if dispatch else [])+[{'type':'run_end','answer':{}}]
  with patch.object(guard.run_log,'events',return_value=events),patch.object(guard.run_log,'unpack',return_value=answer.encode()):return guard.errors('.')
 def test_unexecuted_intent_not_completion(self):
  self.assertIn('prior_followed_only_by_unexecuted_search_intent',self.outcome('<prior_answer>已有知识</prior_answer>\n我先检索官方配套关系文档。'))
 def test_final_answer_is_not_rejected_for_no_tools_alone(self):
  self.assertEqual([],self.outcome('<prior_answer>已有知识</prior_answer>\n最终回答：此任务无法在当前条件下核验。'))
 def test_actual_dispatch_retained(self):
  self.assertEqual([],self.outcome('我先检索官方配套关系文档。',True))
if __name__=='__main__':unittest.main()
