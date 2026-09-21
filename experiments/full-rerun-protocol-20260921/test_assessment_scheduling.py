import fcntl
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import assess_remaining_parallel as schedule

class SchedulingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        (self.root/'assessments/development').mkdir(parents=True)
        (self.root/'.assessment-locks').mkdir()
        self.rootpatch=patch.object(schedule,'R',self.root);self.rootpatch.start()
        self.item={'case':'case-test'}
    def tearDown(self):
        self.rootpatch.stop();self.tmp.cleanup()
    def write(self,name,value):
        (self.root/'assessments/development'/name).write_text(json.dumps(value))
    def test_busy_case_is_not_called(self):
        with (self.root/'.assessment-locks/case-test-predictors').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            with patch.object(schedule.assess,'run_one') as call:
                schedule.work((self.item,'predictors'));call.assert_not_called()
    def test_success_and_two_failures_are_not_called(self):
        self.write('case-test-predictors.json',{'error':'timeout'})
        self.write('case-test-predictors-attempt-1.json',{'error':'malformed'})
        self.assertEqual(schedule.remaining(self.item,'predictors'),(False,True))
        self.write('case-test-outcome.json',{'raw_assessment':{}})
        self.assertEqual(schedule.remaining(self.item,'outcome'),(False,False))
    def test_one_failure_allows_exactly_remaining_attempt(self):
        self.write('case-test-predictors.json',{'error':'timeout'})
        with patch.object(schedule.assess,'run_one',return_value={'status':'done'}) as call:
            schedule.work((self.item,'predictors'))
            call.assert_called_once()
            self.assertTrue(call.call_args.args[2].overwrite)
            self.assertEqual(call.call_args.args[2].timeout,900)

if __name__=='__main__':unittest.main()
