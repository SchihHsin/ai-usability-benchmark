"""Freeze a small M4 rubric comparison before any model scoring."""
from pathlib import Path
import json,hashlib,random,datetime
R=Path(__file__).resolve().parent
ROOT=R.parents[1]
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=(ROOT/'experiments/m11-uniform-fit-20260921/frozen-skill/references/rules.md').read_text().split('## M4 版本清晰度\n',1)[1].split('\n## M5',1)[0]
new='''# M4 版本清晰度：本轮试验版
评价官方资料是否能明确选择适用版本。不评价答案是否正确、正文取得程度或检索成本。
1分：无版本信息。
2分：有版本信息，但无明确选择依据。
3分：部分选择条件明确，仍有关键条件缺失。
4分：需自行合并官方约束，才能确定适用版本。
5分：官方已明确说明条件与适用版本的对应关系。
4分的合并必须有官方依据，不得补入材料未说明的假设；可确定的结果允许是版本范围。
不按页面数量或版本数量扣分。资料未取得记blocked；任务无需版本判断记not_applicable；证据不足或分档无法区分可给区间及uncertain，不强行猜分。
'''
common='''仅评价给定阅读包的M4，不评价整个网站，不检索，不读取旧评分、最终任务答案或其他评价者结果。合成材料仅为规则测试，不能当真实官网事实。真实材料为保留出处的读取片段，包外可能存在资料，不得据此断言整个生态没有信息。
每例返回 case_id、score（1—5整数或null）、status（scored/uncertain/blocked/not_applicable）、lower/upper、reason（简短）、evidence（source_id和逐字quote数组）、ambiguity。不得要求单一版本或具体补丁号，除非任务要求。发现规则无法判定时如实给uncertain。不给隐藏思维链。
'''
for name,rule in [('old',old),('new',new)]:
 p=R/('skill-'+name);p.mkdir(exist_ok=True);(p/'SKILL.md').write_text('# M4 bounded scoring experiment\n\n'+common+'\n'+rule)
cases=[];expected={};relations=[]
def add(cid,docs,expected_score,question=None,status='scored',synthetic=True,**kw):
 question=question or '设备H1、运行时R8，按官方材料选择可用的Alpha SDK版本或范围。'
 cases.append(dict(case_id=cid,kind='synthetic' if synthetic else 'real_official_material',question=question,sources=[dict(source_id=f'{cid}-s{i+1}',page_id=page,text=txt) for i,(page,txt) in enumerate(docs)],**kw))
 expected[cid]={'score':expected_score,'status':status,'basis':'predeclared investigator expectation for diagnostic cases, not independent gold label' if synthetic else 'no expected score for real documents'}
add('u17',[('p1','Alpha SDK提供开发工具和示例。本文没有发布号、版本范围或兼容关系说明。')],1)
add('u42',[('p1','Alpha SDK可下载2.0、2.1、2.2。本文没有说明这些版本各自适用的设备或运行时。')],2)
add('u08',[('p1','设备H1支持Alpha SDK 2.0至2.4。Alpha SDK还需要与运行时版本匹配，但本文未说明运行时R8对应哪些SDK版本。')],3)
constraints=['设备H1允许使用Alpha SDK 2.0至2.4（含端点）。','运行时R8允许使用Alpha SDK 2.2至2.6（含端点）。','同一安装同时满足设备和运行时约束即可使用，无其他版本限制。']
add('u63',[('p1','\n'.join(constraints))],4)
add('u29',[('p'+str(i+1),t) for i,t in enumerate(constraints)],4)
direct='兼容表：设备H1 + 运行时R8 → Alpha SDK 2.2至2.4（含端点），范围内各版本均支持。按该对应关系选择即可，无其他版本限制。'
add('u51',[('p1',direct)],5)
add('u04',[('p1','设备H1的运行时R8兼容关系，请参阅明确关联的官方页面p2。'),('p2',direct)],5)
add('u76',[('p1',direct.replace('Alpha','Beta'))],5,question='设备H1、运行时R8，按官方材料选择可用的Beta SDK版本或范围。')
add('u33',[('p1','兼容表：设备H1 + 运行时R8 → Alpha SDK 2.3。该条件下只支持2.3。')],5)
add('u90',[('p1','当前有效兼容说明：设备H1、运行时R8只支持Alpha SDK 2.3。'),('p2','当前有效兼容说明：设备H1、运行时R8不支持Alpha SDK 2.3，只支持2.4。两页没有标注替代、优先级或适用范围差异。')],2)
add('u12',[('p1','HTTP 403 Forbidden；目标正文没有取得。')],None,status='blocked')
add('u85',[('p1','版本号是软件发布的标识。')],None,question='解释“版本号”这个通用概念；无需选择、比较或锁定任何软件版本。',status='not_applicable')
relations=[{'cases':['u63','u29'],'type':'same_constraints_different_page_partition','expected_new_equal':True},{'cases':['u51','u04'],'type':'explicit_relation_with_or_without_linked_page','expected_new_equal':True},{'cases':['u51','u76'],'type':'brand_swap_only','expected_new_equal':True},{'cases':['u51','u33'],'type':'clear_multiple_vs_clear_single_valid_versions','expected_new_equal':True}]
# Same preselected historical task on both ecosystems; first two official fetches by recorded order.
archive=ROOT/'experiments/m11-uniform-fit-20260921/assessment-input/heldout.json'
packet=json.loads(archive.read_text());selection=[]
for eco,cid in [('cann','r26'),('cuda','r58')]:
 item=next(x for x in packet if x['task_id']=='Q' and x['ecosystem']==eco and x['budget']=='standard')
 sources=[x for x in item['sources'] if x['role']=='fetch' and (x.get('url','').startswith(('https://www.hiascend.com/document/','https://github.com/Ascend/','https://docs.pytorch.org/')))][:2]
 assert len(sources)==2
 cases.append({'case_id':cid,'kind':'real_official_material','question':item['question']+' 本次仅评价所附官方资料对相关功能/参数的版本适用条件是否清楚，不要求实际解决OOM。','sources':[{'source_id':x['event_id'],'page_id':x['url'],'url':x['url'],'text':x['text'],'representation':'original archived WebFetch return, possibly extracted/summary; not raw webpage'} for x in sources]})
 expected[cid]={'score':None,'status':'not_prespecified'}
 selection.append({'case_id':cid,'original_case':item['case'],'original_process_sha256':item['metadata']['process_sha256'],'source_event_ids':[x['event_id'] for x in sources],'selection':'Q standard run; first two official documentation fetches in recorded order; no old scores read'})
# New ecosystems: exact text slices from fresh official HTTP responses, with offsets.
for name,cid,startmark,endmark,question in [
 ('django','r71','What Python version can I use with Django?','What Python version should I use with Django?','Django 5.2分支支持哪些Python次版本？Python 3.14从哪个Django补丁版本开始支持？仅判断官方版本支持关系，不选择生产环境最新补丁。'),
 ('kubernetes','r39','Supported versions\n','kube-proxy\n','HA集群的kube-apiserver为1.36和1.35，哪些kubelet次版本满足官方版本偏差约束？仅评价版本偏差关系，不评价维护期限或额外部署工具约束。')]:
 s=(R/(name+'.txt')).read_text();start=s.rindex(startmark) if name=='kubernetes' else s.index(startmark);end=s.index(endmark,start);excerpt=s[start:end];assert len(excerpt)>500
 ev=next(json.loads(l) for l in (R/'source-acquisition.jsonl').read_text().splitlines() if json.loads(l)['event_id']=='fetch-'+name)
 cases.append({'case_id':cid,'kind':'real_official_material','question':question,'sources':[{'source_id':'fetch-'+name,'page_id':ev['url'],'url':ev['url'],'text':excerpt,'representation':'exact section excerpt from locally extracted HTML text','text_start':start,'text_end':end,'full_extracted_text_sha256':sha(R/(name+'.txt')),'http_body_sha256':ev['body_sha256']}]})
 expected[cid]={'score':None,'status':'not_prespecified'}
random.Random(20260921).shuffle(cases)
dump(R/'input.json',cases);dump(R/'expectations-not-for-raters.json',{'expected':expected,'invariance_checks':relations});dump(R/'source-selection.json',selection)
protocol={'id':R.name,'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'type':'small rubric boundary and evidence replay study; not end-to-end task rerun','model_requested':'gpt-5.6-luna','runs':[{'id':'old-a','rubric':'old'},{'id':'new-a','rubric':'new'},{'id':'new-b','rubric':'new'}],'cases':len(cases),'synthetic_cases':12,'real_cases':4,'real_ecosystems':['CANN','CUDA/PyTorch','Django','Kubernetes'],'primary_checks':['new-a/new-b agreement and uncertainty','predeclared synthetic invariance','traceable quotes','old/new changed decisions'],'blinding':'fresh subagent context fork_turns=none; only assigned rubric and shared input supplied; expectations and other outputs not supplied; no strict OS-level file isolation claimed','retries':'no score-based retries; preserve failed output; technical-format failures may be repaired only syntactically','scope':'M4 only; no new weights, no other metric changes, formal Skill unchanged','limits':['same-model repeated judgments, not independent expert gold','synthetic expected scores are investigator-designed checks','four real cases do not establish ecosystem generalizability','historical source replay differs from fresh HTTP acquisition','only selected source bundle is evaluated, not whole ecosystem'],'input_sha256':sha(R/'input.json'),'rubric_sha256':{x:sha(R/('skill-'+x)/'SKILL.md') for x in ['old','new']}}
dump(R/'protocol.json',protocol)
print(json.dumps({'cases':len(cases),'input_sha256':protocol['input_sha256'],'rubric_sha256':protocol['rubric_sha256']}))
