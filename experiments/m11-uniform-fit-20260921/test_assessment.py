"""Evidence failures must not silently become supported scores."""
import copy
import assess

def run():
    item={'sources':[{'event_id':'s1','text':'real source quote'}],'prior':[], 'final':'real final code','counts':{'search':3,'fetch':6}}
    v={'metrics':[{'id':'M2','score':5,'lower':5,'upper':5,'status':'scored','evidence':[{'event_id':'s1','quote':'invented quote'}]},{'id':'M8','score':3,'status':'scored','evidence':[]}]}
    z=assess.audit(copy.deepcopy(v),item,'predictors')
    assert z['metrics'][0]['score'] is None and z['metrics'][0]['lower']==1
    assert z['metrics'][1]['score']==1
    assert v['metrics'][0]['score']==5
    req={'requirements':[{'id':1,'status':'supported','answer_quote':'real final code','evidence_id':'s1','evidence_quote':'','reason':'x'}]}
    assert assess.audit(req,item,'outcome')['requirements'][0]['status']=='unverified'
    bad={'requirements':[{'id':1,'status':'supported','answer_quote':'made up','evidence_id':'s1','evidence_quote':'real source quote'}]}
    assert assess.audit(bad,item,'outcome')['requirements'][0]['status']=='unverified'
    assert assess.clean_json([{'type':'reasoning','text':'private'},{'type':'output_text','text':'visible'}])==[{'type':'output_text','text':'visible'}]
    item['prior']=[{'event_id':'prior1','text':'only prior text'}]
    prior_ref={'requirements':[{'id':1,'status':'supported','answer_quote':'real final code','evidence_id':'prior1','evidence_quote':'only prior text','verification':'source'}]}
    assert assess.audit(prior_ref,item,'outcome')['requirements'][0]['status']=='unverified'
    print('evidence rejection, controller M8, immutable raw values, and reasoning filtering PASS')
if __name__=='__main__':run()
