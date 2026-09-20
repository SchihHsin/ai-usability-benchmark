"""Continuous 0–100 index. Pure arithmetic, not evidence validation."""
import json,sys,math

def calculate(metrics):
    missing=[];values={}
    for i in range(1,9):
        k=f'M{i}';m=metrics.get(k,{})
        if m.get('status')!='scored' or m.get('score') is None:
            missing.append({'metric':k,'status':m.get('status','not_assessed'),'reason':m.get('reason','未完成对应分项评价')});continue
        v=m['score']
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 1<=v<=5:raise ValueError(k+'分值须在1—5内')
        values[i]=v/5
    if missing:return {'scale':'0–100','score':None,'status':'incomplete_inputs','missing_inputs':missing}
    x=values;o=x[1]*x[2]*x[3];t=x[5]*x[6];p=x[7]
    k=1-(1-o)*(1-t)*(1-p)
    vf=.7+.3*x[4];cf=.9+.1*x[8];score=100*k*vf*cf
    return {'scale':'0–100','score':score,'display_score':round(score,1),'status':'calculated','components':{'official':o,'third_party':t,'prior':p,'knowledge_availability':k,'version_factor':vf,'cost_factor':cf},'interpretation':'composite index, not probability'}
if __name__=='__main__':print(json.dumps(calculate(json.load(sys.stdin)),ensure_ascii=False,indent=2))
