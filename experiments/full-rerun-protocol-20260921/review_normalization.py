"""Keep observed body acquisition while conservatively auditing completeness claims."""
def completeness(doc,item):
    if doc.get('representation')!='body':return None
    state=doc.get('completeness');eid=doc.get('event_id')
    if state=='complete':
        ref=doc.get('reference');ref=ref if isinstance(ref,dict) else {}
        known=item.get('completeness_references',{}).get(ref.get('id'),{})
        verified=known.get('verified_complete') and known.get('event_id')==eid
    elif state=='incomplete':
        text=next((s['text'] for s in item['sources'] if s['event_id']==eid),'')
        evidence=doc.get('boundary_evidence',[])
        verified=isinstance(evidence,list) and bool(evidence) and all(isinstance(e,dict) and e.get('event_id')==eid and isinstance(e.get('quote'),str) and e['quote'].strip() and e['quote'] in text for e in evidence)
    else:return None
    if verified:return None
    doc['completeness']='unknown'
    return {'event_id':eid,'original_completeness':state,'replacement_completeness':'unknown','basis':'Observed body retained, but claimed completeness boundary is not verified; apply frozen 4–5 uncertainty rule.'}
