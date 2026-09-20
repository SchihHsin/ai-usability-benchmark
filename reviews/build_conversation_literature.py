from pathlib import Path
import json,html
ROOT=Path(__file__).resolve().parent
refs=json.loads((ROOT/'scoring-proposal-2026-09-15.json').read_text())['references']
rows=[]
for key,v in refs.items():
 rows.append({'id':key,'reference':v[0],'url':v[1],'use_and_reading_scope':v[2],'limits':v[3],'status':'此前记录，未声称本轮重读'})
extra=[
 ('BATES','Bates (1989). The Design of Browsing and Berrypicking Techniques for the Online Search Interface.','https://pages.gseis.ucla.edu/faculty/bates/berrypicking.html','此前已读公开版模型论述与结论，支持多阶段查询演进。','不提供Agent查询五档或次数阈值。'),
 ('SDCG','Järvelin, Price, Delcambre & Nielsen (2008). Discounted Cumulated Gain Based Evaluation of Multiple-Query IR Sessions. ECIR, 4–15.','https://doi.org/10.1007/978-3-540-78646-7_4','此前核对题录及公开预览第4—5页；支持列表位置与查询序列共同评价。','未读完整公式，不声称已复现sDCG。'),
 ('ESRI','Esri. Data classification methods: Equal interval.','https://pro.arcgis.com/en/pro-app/latest/help/mapping/layer-properties/data-classification-methods.htm','此前用于解释等距分档的官方文档；M11已取消五档，该用途已撤回。','制图分档不验证置信度阈值，更不验证M11权重。'),
 ('PEARL','Pearl (1988). Probabilistic Reasoning in Intelligent Systems: Networks of Plausible Inference.','https://www.sciencedirect.com/book/9780080514895/probabilistic-reasoning-in-intelligent-systems','对话中作为noisy-OR结构的理论出处引用；未在本轮核对全文。','不支持把有序分数直接当概率，不验证本公式或系数；无未经核验的页码及原文摘录。'),
 ('ESL','Hastie, Tibshirani & Friedman (2009). The Elements of Statistical Learning, 2nd ed., Chapter 7: Model Assessment and Selection.','https://hastie.su.domains/ElemStatLearn/','本轮取得作者公开PDF，核对第7章纸面页219、222—223、241、243、245—247、249：平方误差、模型选择与评价的区别、交叉验证泄漏及bootstrap。未声称阅读全文。','不规定本研究损失函数、任务分组、样本量、网格步长或权重值。')]
for k,t,u,s,l in extra:rows.append({'id':k,'reference':t,'url':u,'use_and_reading_scope':s,'limits':l,'status':'对话补录'})
(ROOT/'conversation-literature.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
h=html.escape
fragment='<section id="conversation-literature"><h2>本对话文献总账</h2><p>包含已采用、仅作背景和已撤回用途的引用。查阅范围沿用可追溯记录；未读全文不冒称读过。实验网页是技术证据，另存于运行记录，不混作文献依据。</p><table><tr><th>文献/著作</th><th>用途及实际查阅范围</th><th>不能支持的结论</th></tr>'
for r in rows:fragment+=f'<tr><td><a href="{h(r["url"])}">{h(r["reference"])}</a></td><td>{h(r["use_and_reading_scope"])}</td><td>{h(r["limits"])}</td></tr>'
fragment+='</table></section>'
(ROOT/'conversation-literature-fragment.html').write_text(fragment)
print('Recorded',len(rows),'references')
