from pathlib import Path
import sys,json
ROOT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'new-skill'))
from scripts import run_log as log
from compare_rules import audit
for a in audit():
 d=ROOT/'runs'/a['run'];rows=log.events(d)
 saved=json.loads((d/'evaluation.json').read_text())
 if saved['revisions'][-1]['evaluation']['assessor'].get('id')=='ab-evidence-diagnostic':continue
 v=log.metric_template(rows);v['assessor']={'id':'ab-evidence-diagnostic','method':'common-evidence cross-rule diagnostic; not independent full rubric validation'}
 v['limitations']=['单题单模型，每组一次；不能估计模型随机性或因果增益','只对明确获取形态和调用计数做有据判定，其余保持待定','不将模型手写日志、证据编号、完整性声明当客户端事实','未执行硬件代码、未完成独立双人内容评分，M11不补算']
 def evidence(eid):
  r=next(x for x in rows if x['id']==eid);p=r['response'];q=p['content'][:450];ident='diag-'+str(len(v['evidence'])+1)
  v['evidence'].append(dict(id=ident,event_id=eid,field='response',sha256=p['sha256'],start=0,end=len(q),quote=q));return ident
 docs=[]
 for item in a['official_fetch_cross_scoring']:
  ref=evidence(item['event']);docs.append(dict(url=item['url'],new_rule_score=item['new'],old_rule_score=item['old'],basis=item['basis'],evidence_refs=[ref],event_refs=[item['event']]))
 for m in v['metrics']:
  if m['id']=='M2':m.update(status='partial_observations',observation={'fetch_level_cross_rule_comparison':docs,'aggregation':'not_computed; document inventory and completeness not fully adjudicated'},reason='仅明确形态可判，不能删除未知项合成任务分')
  if m['id']=='M8':
   c=sum(a['counts'].values());m.update(score=max(1,5-(c-1)//2),status='observed',observation={'S':a['counts']['search'],'F':a['counts']['fetch'],'C':c},reason='从实际派发事件计数',event_refs=[r['id'] for r in rows if r['type']=='tool_dispatch'])
  if m['id']=='M7':m.update(status='prior_captured' if a['prior_full'] else 'self_report_only',observation={'prior_chars':a['prior_chars'],'complete_prior_tag_present':a['prior_full']},reason='正确性未独立核验，不将自评直接计分')
  if m['id']=='M11':m.update(status='not_calculable',reason='输入分项未完成有据评分；旧版默认亦禁算')
 log.save_evaluation(d,v)
 result=log.check(d);assert not result['issues'],result
print('诊断评价已绑定过程哈希保存；原始记录未改。')
