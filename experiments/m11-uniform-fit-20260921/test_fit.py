import json,sys
import tempfile
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).parent)); import fit

def row(case,group,a,b, y=None, split="development"):
    x=[[3,3]]*8
    x[3]=[a,a]; x[7]=[b,b]
    return {"case":case,"group":group,"split":split,"input_intervals":x,"outcome_interval":[y,y] if y is not None else [0,1]}

def test_synthetic_recovery():
    # Constant K=0.784, factors identify a=.30,b=.10 through varied M4/M8.
    true=(.30,.10); rows=[]
    for g in "ABCD":
        for i,(m4,m8) in enumerate([(1,1),(2,4),(4,2),(5,5)]):
            x=[[3,3]]*8; x[3]=[m4,m4]; x[7]=[m8,m8]; k=1-(1-.6**3)*(1-.6**2)*(1-.6); y=k*(1-true[0]*(1-m4/5))*(1-true[1]*(1-m8/5)); rows.append({"case":f"{g}{i}","group":g,"input_intervals":x,"outcome_interval":[y,y]})
    fam,chosen,_=fit.select_family(rows); assert chosen["a"]==true[0] and chosen["b"]==true[1]

def test_group_isolation():
    rows=[row("a","A",1,1,.2),row("b","B",1,1,.8)]
    assert fit.group_mean(rows,np.array([1.,3.]))==2.

def test_interval_monotone_boundaries():
    r={"case":"x","group":"A","input_intervals":[[1,5]]*8,"outcome_interval":[0,1]}
    p=fit.predict([r],.3,.1)[0]; assert 0<=p[0]<=p[1]<=1

def test_input_integrity_and_split_isolation():
    with tempfile.NamedTemporaryFile(mode='w+',suffix='.json') as f:
        f.write(json.dumps([row('x','A',1,1,.2),row('x','B',1,1,.3)])); f.flush()
        try: fit.read_rows(f.name); assert False
        except ValueError as e: assert 'duplicate case' in str(e)
    with tempfile.NamedTemporaryFile(mode='w+',suffix='.json') as f:
        z=row('nan','A',1,1,.2); z['input_intervals'][0]=[float('nan'),1]; f.write(json.dumps([z,],allow_nan=True)); f.flush()
        try: fit.read_rows(f.name); assert False
        except ValueError as e: assert 'non-finite' in str(e)
