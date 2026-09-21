"""Reject malformed tool-call text mistakenly returned as a completed answer."""
from pathlib import Path
import sys,re,json
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'frozen-skill'))
from scripts import run_log

def errors(run):
 events=run_log.events(Path(run));end=events[-1]
 if end.get('type')!='run_end':return ['no_run_end']
 answer=run_log.unpack(end['answer']).decode('utf-8');out=[]
 if not any(e['type']=='tool_dispatch' for e in events):
  if re.search(r'<(?:WebSearch|WebFetch|invoke|tool_call)\b',answer,re.I):out.append('tool_call_serialized_as_text_without_dispatch')
  if '<prior_answer>' in answer and not re.sub(r'<prior_answer>[\s\S]*?</prior_answer>','',answer).strip():out.append('prior_only_no_final_answer')
 return out

def invalid_ids():
 p=R/'run-invalidations.json'
 return set(json.loads(p.read_text())) if p.exists() else set()
