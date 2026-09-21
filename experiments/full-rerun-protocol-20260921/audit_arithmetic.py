"""Independent expanded-polynomial arithmetic check, not validity validation."""
import datetime
import json
import math
from pathlib import Path
R=Path(__file__).resolve().parent
checked=0
issues=[]
for row in json.loads((R/'results.json').read_text())['rows']:
    if not row.get('assessed') or row['overall']['status'] not in ('bounded','calculated'):
        continue
    value=json.loads((R/row['evaluation']).read_text())['revisions'][-1]['evaluation']
    metrics={m['id']:m for m in row['metrics']}
    channels=value.get('channel_states',{})
    def x(n,side):
        m=metrics[f'M{n}']
        v=m.get(side)
        if v is None:v=m.get('score')
        return v/5
    expected=[]
    for side in ('lower','upper'):
        off=0 if channels.get('official',{}).get('status')=='confirmed_unavailable' else x(1,side)*x(2,side)*x(3,side)
        sec=0 if channels.get('third_party',{}).get('status')=='confirmed_unavailable' else x(5,side)*x(6,side)
        prior=0 if channels.get('prior',{}).get('status')=='confirmed_unavailable' else x(7,side)
        union=off+sec+prior-off*sec-off*prior-sec*prior+off*sec*prior
        version=1 if metrics['M4'].get('status')=='not_applicable' else .7+.3*x(4,side)
        expected.append(100*union*version*(.9+.1*x(8,side)))
    actual=[row['overall'].get(side,row['overall'].get('score')) for side in ('lower','upper')]
    if any(not math.isclose(a,b,abs_tol=1e-6) for a,b in zip(expected,actual)):
        issues.append({'run_id':row['run_id'],'expected':expected,'actual':actual})
    checked+=1
result={'updated':datetime.datetime.now().isoformat(timespec='seconds'),'checked':checked,'issues':issues,'method':'Independent expanded noise-OR polynomial O+S+P-OS-OP-SP+OSP, both endpoints. Does not establish input validity or probability calibration.'}
(R/'arithmetic-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result))
raise SystemExit(bool(issues))
