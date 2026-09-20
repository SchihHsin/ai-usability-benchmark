"""Historical diagnostic replay. Does not update experiment evaluations or Skill."""
import json,re,hashlib
from pathlib import Path
from html import escape as H
from urllib.parse import urlparse
ROOT=Path(__file__).parent
DATA=Path('/Users/hsin/Documents/Coding/opknow/experiments/multimodel/e-validation-body-state-20260914/runs')
def candidate(q,r):
    return 5 if (q,r)==(1,1) else 4 if q==1 else 3 if q==2 else 2
out=[]
for f in sorted(DATA.glob('*/process.jsonl')):
    rows=[json.loads(l) for l in f.read_text().splitlines()]
    results={r['request_id']:r for r in rows if r['type']=='tool_result'}
    searches=[];first=None;bad=False;active=set();overlap=False
    roles={r['id']:r.get('role') for r in rows if r['type']=='tool_request'}
    for e in rows:
        if e['type']=='tool_dispatch' and roles.get(e['request_id'])=='search':
            if active:overlap=True
            active.add(e['request_id'])
        if e['type']=='tool_result':active.discard(e['request_id'])
    requests=[r for r in rows if r['type']=='tool_request' and r.get('role')=='search']
    for q,req in enumerate(requests,1):
        ret=results[req['id']];raw=ret['response']['content'];assert hashlib.sha256(raw.encode()).hexdigest()==ret['response']['sha256']
        text=raw.replace('\\n','\n');hits=[]
        for m in re.finditer(r'## (\d+)\. \[(.*?)\]\((https?://[^\n]+)\)',text):
            host=urlparse(m[3]).hostname or ''
            official=any(host==d or host.endswith('.'+d) for d in ['hiascend.com','nvidia.com','pytorch.org'])
            hits.append(dict(position=int(m[1]),title=m[2],url=m[3],official_domain_candidate=official))
        failed=ret['tool_status']=='error' or text.startswith('Error:')
        if first is None and (failed or not hits):bad=True
        official=next((h for h in hits if h['official_domain_candidate']),None)
        if first is None and official:first=dict(query=q,position=official['position'],url=official['url'],event=ret['id'])
        searches.append(dict(query=q,request=req['arguments'],event=ret['id'],results=hits,failed=failed,response_sha256=ret['response']['sha256']))
    # First hits were inspected in returned titles/snippets: troubleshooting introductions or Compute Sanitizer.
    # Relevance is discovery-level, not proof of detailed answer support or page acquisition.
    score=candidate(first['query'],first['position']) if first and not bad and not overlap else None
    out.append(dict(run=f.parent.name,source_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),first=first,pre_hit_missing=bad,overlapping_searches=overlap,candidate_band=score,searches=searches))
(ROOT/'m1-replay.json').write_text(json.dumps(dict(status='diagnostic_only_not_validated',candidate='first hit q=1/r=1:5; q=1/r>1:4; q=2:3; q>=3:2; completed no-hit:1; missing/parallel:unknown',scope='observed top5 only, cannot validate proposed top10 protocol; official first hits manually checked for task topical relevance',runs=out),ensure_ascii=False,indent=2))
body='<h3>M1旧记录回放：诊断结果</h3><p>仅用于检查候选规则，未改旧评分，未运行模型，未证明效度。以下分数使用刚讨论的轮次优先候选量规，非sDCG复现、非正式结果。首次命中标题/摘要已核对为故障排查入口或Compute Sanitizer，足以判定任务相关来源，不代表正文充分。</p><table><tr><th>旧运行</th><th>首次官方命中（查询/位置）</th><th>候选分</th></tr>'
for x in out:
 f=x['first'];p=f"{f['query']} / {f['position']}" if f else '未观察';score=x['candidate_band']
 body+=f'<tr><td>{H(x["run"])}</td><td>{p}</td><td>{score if score is not None else "待定：前序缺失或并行"}</td></tr>'
body+='</table><p><b>发现：</b>成功列表每次只有5条；首次命中位置均为1，缺少低排名首轮命中样本，不能检验轮次/排名权衡。GLM CANN首轮实际超时，外层状态仍为ok，不能当无结果。此六轮同属E任务，不能当六种任务验证。</p><p><b>参数敏感性（纯数学示例，不是实测）：</b>以等效检查负担E=(q−1)×c+(r−1)演示，c为一次追加查询假定等价的列表位置数。首轮第8位E=7；次轮第1位E=c。c=3或5时次轮更优，c=10时首轮更优。这说明权重会改变排序；此式仅用于展示问题，不作为新评分或文献公式。</p><p><b>结论：</b>当前候选可区分早/晚命中，但现有记录无法验证五档或轮次绝对优先；不能据此冻结正式M1。下一步补齐方法依据及低排名、多轮未命中边界材料，而非为拟合这六轮调整阈值。独立评分者一致性尚未测量。</p><p><b>全文查阅状态：</b>sDCG出版社PDF入口返回落地页，OpenAlex未列开放全文位置；本轮仍未取得完整公式，保留摘要/引言的已读范围，不声称完成全文核验。</p>'
for x in out:
 body+=f'<details><summary>{H(x["run"])}：全部搜索网址</summary>'
 for s in x['searches']:
  body+=f'<p>查询{s["query"]}：{H(str(s["request"]))} · {H(s["event"])}</p><ol>'
  for r in s['results']:body+=f'<li value="{r["position"]}"><a href="{H(r["url"])}">{H(r["title"])}</a><br>{H(r["url"])}</li>'
  body+='</ol>'
  if s['failed']:body+='<p>实际返回错误，非零结果。</p>'
 body+='</details>'
(ROOT/'m1-replay.html').write_text(body)
print([(x['run'],x['first']['query'] if x['first'] else None,x['candidate_band'],x['overlapping_searches']) for x in out])
