#!/usr/bin/env python3
"""从新实验 runs 生成隔离的 predictor/outcome 后评输入；不计算分数。"""
from __future__ import annotations
import argparse, base64, hashlib, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def unpack(v):
    if not isinstance(v,dict) or v.get('encoding') not in ('utf-8','base64'):
        return ''
    b=v.get('content','').encode() if v['encoding']=='utf-8' else base64.b64decode(v.get('content',''))
    if v.get('sha256') and hashlib.sha256(b).hexdigest()!=v['sha256']:
        raise ValueError('packed content hash mismatch')
    return b.decode('utf-8','replace')

def visible_text(value):
    out=[]
    if isinstance(value,dict):
        if value.get('type') in ('text','output_text') and isinstance(value.get('text'),str): out.append(value['text'])
        for k,v in value.items():
            if k not in ('thinking','reasoning','reasoning_content','signature','rawContent'): out.extend(visible_text(v))
    elif isinstance(value,list):
        for x in value: out.extend(visible_text(x))
    return out

def parse_run(p, tasks, protocol):
    rows=[json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
    start=rows[0]; meta=start.get('metadata',{}); task=str(meta.get('task_id')); eco=str(meta.get('ecosystem','')).lower()
    if task not in tasks: raise ValueError(f'{p}: unknown task {task}')
    q=unpack(start.get('question',{}))
    req=tasks[task].get('criteria',{}).get(eco,[])
    split='development' if task in protocol.get('development',[]) else 'heldout' if task in protocol.get('heldout',[]) else 'unknown'
    requests={r['id']:r for r in rows if r.get('type')=='tool_request'}
    sources=[]; prior=[]; errors=[]
    first_tool=min((r.get('seq',10**9) for r in rows if r.get('type')=='tool_request'),default=10**9)
    for r in rows:
        if r.get('type')=='client_note' and r.get('seq',0)<first_tool:
            txt=unpack(r.get('content',{}));
            try: obj=json.loads(txt); pieces=visible_text(obj)
            except Exception: pieces=[txt]
            joined='\n'.join(pieces)
            # 只保存执行模型明确闭合的 prior_answer，且不能把 assistant 后续答案混入。
            m=re.search(r'<prior_answer>\s*(.*?)\s*</prior_answer>',joined,re.S)
            if m: prior.append({'event_id':r['id'],'text':m.group(1).strip()})
        if r.get('type')=='tool_result':
            txt=unpack(r.get('response',{})); reqrow=requests.get(r.get('request_id'),{})
            sources.append({'event_id':r['id'],'request_id':r.get('request_id'),'role':reqrow.get('role'),'tool':reqrow.get('tool'),'url':(reqrow.get('arguments') or {}).get('url'),'arguments':reqrow.get('arguments',{}),'query':(reqrow.get('arguments') or {}).get('query'),'text':txt,'status':r.get('status',r.get('tool_status'))})
    end=next((r for r in rows if r.get('type')=='run_end'),None)
    if end is None:
        raise ValueError('incomplete run: missing run_end')
    final=unpack(end.get('answer',{}))
    # 计数只基于实际 dispatch，拒绝请求不计入；保留失败来源片段供 M6 审核。
    dispatched={r.get('request_id') for r in rows if r.get('type')=='tool_dispatch'}
    counts={'search':sum(1 for r in requests.values() if r.get('role')=='search' and r.get('id') in dispatched),'fetch':sum(1 for r in requests.values() if r.get('role')=='fetch' and r.get('id') in dispatched)}
    case='case-'+hashlib.sha256(str(meta.get('run_id',p.parent.name)).encode()).hexdigest()[:12]
    return {'case':case,'budget':meta.get('protocol',{}).get('budget_arm'),'run_name':p.parent.name,'run_dir':str(p.parent),'task_id':task,'ecosystem':eco,'split':split,'question':q,'criteria':req,'prior':prior,'sources':sources,'final':final,'counts':counts,'metadata':{'run_id':meta.get('run_id'),'model_id':meta.get('model_id'),'protocol_version':meta.get('protocol_version'),'rubric_version':meta.get('rubric_version'),'question_sha256':meta.get('question_sha256'),'process_sha256':hashlib.sha256(p.read_bytes()).hexdigest()},'errors':errors}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--runs',type=Path,default=ROOT/'runs'); ap.add_argument('--out',type=Path,default=ROOT/'assessment-input'); ap.add_argument('--split',choices=['development','heldout','all'],default='all'); args=ap.parse_args()
    protocol=json.loads((ROOT/'protocol.json').read_text()); raw=json.loads((ROOT/'tasks.json').read_text()); tasks=raw.get('tasks',raw)
    runs=sorted(args.runs.glob('*/process.jsonl')) if args.runs.exists() else []
    rows=[]
    for p in runs:
        try:
            z=parse_run(p,tasks,protocol)
            if args.split=='all' or z['split']==args.split: rows.append(z)
        except Exception as e: print(f'SKIP {p}: {e}')
    args.out.mkdir(parents=True,exist_ok=True)
    for split in ('development','heldout'):
        selected=[r for r in rows if r['split']==split]
        (args.out/f'{split}.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2)+'\n')
    manifest={'protocol_sha256':hashlib.sha256((ROOT/'protocol.json').read_bytes()).hexdigest(),'tasks_sha256':hashlib.sha256((ROOT/'tasks.json').read_bytes()).hexdigest(),'runs':len(rows),'by_split':{s:sum(r['split']==s for r in rows) for s in ('development','heldout')},'cases':[r['case'] for r in rows]}
    (args.out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
