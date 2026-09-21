"""Continuous composite with explicit unavailable-channel and interval semantics."""
import json,sys,math

def calculate(metrics, channel_states=None):
    states=channel_states or {}; missing=[]; decisions=[]
    def value(k, neutral_na=False):
        m=metrics.get(k,{})
        if neutral_na and m.get('status')=='not_applicable':
            decisions.append({'metric':k,'handling':'neutral adjustment; not a grade 5 observation'})
            return (1.,1.)
        if m.get('status')=='scored' and m.get('score') is not None: lo=hi=m['score']
        elif m.get('status')=='bounded' and m.get('lower') is not None and m.get('upper') is not None:lo,hi=m['lower'],m['upper']
        else:
            missing.append({'metric':k,'status':m.get('status','not_assessed'),'reason':m.get('reason','分项尚无可用评分或区间')});return None
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in [lo,hi]) or not 1<=lo<=hi<=5:raise ValueError(k+': invalid grade interval')
        return lo/5,hi/5
    def channel(name,keys):
        state=states.get(name,{})
        if state.get('status')=='confirmed_unavailable':
            if not state.get('evidence') or not state.get('reason'):raise ValueError(name+': unavailable channel requires audited evidence and reason')
            decisions.append({'channel':name,'handling':'zero contribution','reason':state['reason'],'evidence':state['evidence']})
            return (0.,0.)
        parts=[value(k) for k in keys]
        if any(x is None for x in parts):return None
        return math.prod(x[0] for x in parts),math.prod(x[1] for x in parts)
    o=channel('official',['M1','M2','M3']);s=channel('third_party',['M5','M6']);p=channel('prior',['M7'])
    v=value('M4',True);c=value('M8')
    if missing:return {'scale':'0–100','status':'incomplete_inputs','score':None,'missing_inputs':missing,'decisions':decisions}
    def total(i):return 100*(1-(1-o[i])*(1-s[i])*(1-p[i]))*(.7+.3*v[i])*(.9+.1*c[i])
    lo,hi=total(0),total(1)
    out={'scale':'0–100','status':'calculated' if lo==hi else 'bounded','score':lo if lo==hi else None,'lower':lo,'upper':hi,'decisions':decisions,'interpretation':'composite index, not probability; interval is not a statistical confidence interval'}
    if lo==hi:out['display_score']=round(lo,1)
    else:out['display_interval']=[math.floor(lo*10)/10,math.ceil(hi*10)/10]
    return out
if __name__=='__main__':
    data=json.load(sys.stdin)
    print(json.dumps(calculate(data.get('metrics',data),data.get('channel_states',{})),ensure_ascii=False,indent=2))
