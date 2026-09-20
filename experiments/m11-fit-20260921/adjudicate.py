"""Conservative, auditable second pass. Raw model assessments stay immutable.
No fitted values are read here. This review is not an independent human gold standard.
"""
from pathlib import Path
import json,copy,hashlib,re
from audit import match
ROOT=Path(__file__).resolve().parent
changes=[]
(ROOT/'reviewed').mkdir(exist_ok=True)
manual={
 ('case-beae4991','M4'):(3,3,'仅链接另一个安装指南不等于已取得配套依据；现有记录不足以明确CANN与TorchNPU组合，不能按跨已取得页面已选定给4。'),
 ('case-beae4991','M6'):(1,3,'关键aclnn签名存在未消除的版本差异，不能认为全部关键主张已获支持；保留是否真正冲突的区间。'),
 ('case-35ce563d','M3'):(3,3,'PyTorch集成是原题核心要求，官方适配正文未取得，不应按仅缺分支给4分。'),
 ('case-35ce563d','M6'):(3,3,'对PyTorch适配的独立核验未完成，不能满足全部关键说法获支持的4分条件。'),
 ('case-36dc2acc','M6'):(3,3,'原评价写明仅大多关键说法获支持，尚不满足全部获可追溯依据支持的4分条件。'),
 ('case-1e0fab07','M3'):(3,3,'原题核心要求包括固件/驱动配套；评价原文承认未取得该表及查版本命令，不能按仅缺分支细节给4分。'),
 ('case-1e0fab07','M4'):(3,3,'M4=4要求跨已取得页面可确定选择；固件/驱动对应页面未取得，仍有未消除的选择，只满足3。'),
 ('case-1e0fab07','M6'):(1,3,'模型同时报告关键矛盾与3—4区间，不能给确定3。保留矛盾是否属于同一版本范围的不确定性，不把未解决问题认作已可信。'),
 ('case-36dc2acc','M3'):(3,3,'原题包含部署完整流程，原评价承认环境设置和部署/核验在取得的官方正文中缺失；属于主流程缺口，非分支细节。'),
}
outcome_manual={
 ('case-beae4991','M4'):(3,3,'仅链接另一个安装指南不等于已取得配套依据；现有记录不足以明确CANN与TorchNPU组合，不能按跨已取得页面已选定给4。'),
 ('case-beae4991','M6'):(1,3,'关键aclnn签名存在未消除的版本差异，不能认为全部关键主张已获支持；保留是否真正冲突的区间。'),
 ('case-35ce563d','M3'):(3,3,'PyTorch集成是原题核心要求，官方适配正文未取得，不应按仅缺分支给4分。'),
 ('case-35ce563d','M6'):(3,3,'对PyTorch适配的独立核验未完成，不能满足全部关键说法获支持的4分条件。'),
 ('case-36dc2acc','M6'):(3,3,'原评价写明仅大多关键说法获支持，尚不满足全部获可追溯依据支持的4分条件。'),
 ('case-11c5dcc4',4):('absent','最终答案仅列setup.py文件名及python3 setup.py build bdist_wheel，未给该构建配置内容；自定义算子与框架轮子构建链不能仅据命令视为完整。','python3 setup.py build bdist_wheel'),
 ('case-11c5dcc4',5):('absent','最终答案未给框架wheel安装命令/实际张量调用用例；列出包装函数与测试文件名不能代替完整安装调用。','python test/test_add_custom.py'),
 ('case-11c5dcc4',6):('absent','列出test_add_custom.py文件名但未提供其内容，caller下载命令还含...占位；不能认定已有具体可核验的正确性测试。','curl -fLO .../example/quick_start/msopgen/caller/'),
}
for file in sorted((ROOT/'assessments').glob('*.json')):
 d=json.loads(file.read_text());p=json.loads((ROOT/'packets'/f"{d['case']}.json").read_text());obs={x['id']:x['response'] for x in p['observations']};kind='outcome' if file.stem.endswith('outcome') else 'predictors'
 def note(item,before,after,reason):changes.append({'case':d['case'],'kind':kind,'item':item,'before':before,'after':after,'reason':reason})
 if kind=='outcome':
  for x in d['requirements']:
   key=(d['case'],x['id'])
   if key in outcome_manual:
    status,reason,quote=outcome_manual[key];note(x['id'],x['status'],status,reason);x.update(status=status,reason=reason,answer_quote=quote,verification='code_inspection',evidence_id=None,evidence_quote='');continue
   if x['status']!='supported':continue
   aq=match(x.get('answer_quote',''),p['answer']);eq=match(x.get('evidence_quote',''),obs.get(x.get('evidence_id'),''))
   if aq in (None,'needs_review') or (x.get('verification')=='source' and eq in (None,'needs_review')):
    note(x['id'],'supported','unverified','原文引文无法通过规范化/省略片段匹配，尚未完成逐条人工裁定；保留未知，不判错误。');x['status']='unverified'
 else:
  ms={x['id']:x for x in d['metrics']}
  for m in d['metrics']:
   if m.get('lower') is not None and m.get('upper') is not None and m['lower']!=m['upper'] and m.get('score') is not None:
    note(m['id'],m['score'],[m['lower'],m['upper']],'自报分数与区间冲突，保留区间');m['score']=None;m['status']='bounded'
  m=ms['M2'];docs=d.get('m2_documents',m.get('m2_documents',[]));d['m2_documents']=docs
  if docs:
   for doc in docs:
    body=obs.get(doc.get('evidence_id'),'')
    if re.search(r'(?i)full extraction|api documentation extract|here is .*extract|## Summary|根据文章内容，我为你提取',body):
     note('M2 document '+doc['url'],[doc.get('lower'),doc.get('upper')],3,'返回明确标注为摘要/摘录表示，按既定M2形态规则为3，不因内容较长升为完整正文。');doc['lower']=doc['upper']=3
    if len(body)<350 and all(w in body for w in ['获取效率','正确性','完整性','易理解']):
     note('M2 document '+doc['url'],[doc.get('lower'),doc.get('upper')],2,'返回页面框架/反馈标签但无正文，按既定M2框架档记2；不推断SPA原因。');doc['lower']=doc['upper']=2
    if doc.get('upper')==5 and doc.get('lower')==5:
     note('M2 document '+doc['url'],5,[4,5],'没有独立同版全文参照或预定完整章节边界核对记录；自称正文结构完整不能证明无缺失。');doc['lower']=4
   if all(isinstance(z.get('lower'),(int,float)) and isinstance(z.get('upper'),(int,float)) for z in docs):
    lo=sum(z['lower'] for z in docs)/len(docs);hi=sum(z['upper'] for z in docs)/len(docs);m.update(score=lo if lo==hi else None,lower=lo,upper=hi,status='scored' if lo==hi else 'bounded')
  else:
   note('M2',m.get('score'),[1,5],'未提供逐文档清单，任务级值未充分可追溯。');m.update(score=None,lower=1,upper=5,status='bounded')
  if '<prior_answer>' not in p['prior_answer']:
   note('M7',ms['M7'].get('score'),[1,5],'未有结构化完整检索前回答，不能把自评信心当知识正确性。');ms['M7'].update(score=None,lower=1,upper=5,status='bounded')
  if d['case'] in ['case-482bf22d','case-c9741626','case-11c5dcc4','case-ca1435c0','case-6f3a052d','case-021f0823']:
   m=ms['M6'];note('M6',m.get('score'),[2,3],'统一处理已发现的第三方摘要或镜像：不是完全没有材料；但未完成关键说法的全面核验，只能保留2—3区间，不因是否抓取正文而对同类记录分别记N/A或确定3。');m.update(score=None,lower=2,upper=3,status='bounded')
  for key,(lo,hi,reason) in manual.items():
   if key[0]!=d['case']:continue
   m=ms[key[1]];note(key[1],m.get('score'),[lo,hi],reason);m.update(score=lo if lo==hi else None,lower=lo,upper=hi,status='scored' if lo==hi else 'bounded',reason=reason)
 d['_review']={'method':'Conservative quote validation, rubric consistency and limited explicit root content review; reviewer is not blinded; interim fitting diagnostics existed, changes follow explicit rubric and citation checks rather than a coefficient target','source_assessment_sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
 (ROOT/'reviewed'/file.name).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
(ROOT/'adjudication-log.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n')
print('Adjudications',len(changes))
