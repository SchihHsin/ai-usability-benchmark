"""Retain assessor's explicitly bounded uncertainty rather than a candidate point."""
def preserve_bounds(metric):
    lo,hi=metric.get('lower'),metric.get('upper')
    if metric.get('status') not in ('scored','supported','bounded'):return
    if all(isinstance(x,(int,float)) and not isinstance(x,bool) for x in (lo,hi)) and 1<=lo<hi<=5:
        metric['candidate_score']=metric.get('score')
        metric['score']=None
        metric['status']='bounded'
        metric['normalization_basis']='Explicit non-degenerate grade range retained; candidate point is not treated as certain.'
