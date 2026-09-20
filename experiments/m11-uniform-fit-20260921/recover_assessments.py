#!/usr/bin/env python3
"""恢复开发集结构合法但外层格式不合规的评估响应；不调用模型、不覆盖原文件。"""
from __future__ import annotations
import argparse, copy, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=ROOT); ap.add_argument('--run',action='append'); args=ap.parse_args()
    # 只允许 development；从不扫描 heldout。
    inp=json.loads((args.root/'assessment-input/development.json').read_text(encoding='utf-8'))
    bycase={x['case']:x for x in inp}; adir=args.root/'assessments/development'; failures=[]; recovered=[]
    # 延迟导入，确保使用主 assess.extract/audit 定义，不复制评分逻辑。
    import sys; sys.path.insert(0,str(args.root)); import assess
    files=sorted(adir.glob('*-predictors.json'))+sorted(adir.glob('*-outcome.json'))
    if args.run: files=[p for p in files if p.name in set(args.run)]
    for p in files:
        d=json.loads(p.read_text(encoding='utf-8'))
        if 'error' not in d: continue
        case=d.get('case'); item=bycase.get(case); kind=d.get('kind')
        fail={'file':str(p),'case':case,'kind':kind,'original_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
        try:
            if not item or kind not in ('predictors','outcome'): raise ValueError('missing development input mapping or invalid kind')
            raw=d.get('raw_stdout')
            if not isinstance(raw,(dict,list)): raise ValueError('raw_stdout is not a JSON envelope')
            parsed,provider,result=assess.extract(raw)
            if isinstance(parsed,dict) and isinstance(parsed.get(kind),dict): parsed=parsed[kind]
            if not isinstance(parsed,dict): raise ValueError(f'no dict branch for {kind}')
            parsed=assess.clean_json(parsed)
            if kind=='predictors':
                if isinstance(parsed.get('metrics'),dict): parsed['metrics']=list(parsed['metrics'].values())
                if [m.get('id') for m in parsed.get('metrics',[])] != [f'M{i}' for i in range(1,9)]: raise ValueError('metrics IDs are not exactly M1..M8')
                value=assess.audit(copy.deepcopy(parsed),item,kind)
            else:
                if isinstance(parsed.get('requirements'),dict): parsed['requirements']=list(parsed['requirements'].values())
                if [m.get('id') for m in parsed.get('requirements',[])] != list(range(1,7)): raise ValueError('requirement IDs are not exactly integer 1..6')
                value=assess.audit(copy.deepcopy(parsed),item,kind)
            # 仅恢复结构；不采用错误文件中的评分/原因元数据，审计版直接来自 raw 分支。
            out={**value,'case':case,'task_id':item['task_id'],'ecosystem':item['ecosystem'],'split':'development','budget':item.get('budget'),'model_identity':item.get('metadata',{}).get('model_id'),'kind':kind,'raw_assessment':parsed,'_recovery':{'original_file':p.name,'original_file_sha256':fail['original_sha256'],'method':'extract branch selection + evidence-dict-to-list normalization + assess.audit; no model call','providerData':provider,'result_type':result.get('type') if result else None}}
            dest=p.with_name(p.stem+'-recovered.json')
            if dest.exists(): raise FileExistsError(str(dest))
            dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            recovered.append({'file':str(dest),'case':case,'kind':kind})
        except Exception as e:
            fail['reason']=repr(e); failures.append(fail)
    report={'recovered':recovered,'failures':failures,'development_only':True,'method':'syntax-legal envelope recovery; originals unchanged; no model calls'}
    (args.root/'assessment-recovery-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
