"""Coverage-based M2; preserves document aggregation and historical versions."""
try:
    from . import document_metrics as previous
except ImportError:
    import document_metrics as previous
VERSION = 'v2-coverage-2026-09-15'
aggregate = previous.aggregate

def template(rows):
    value = previous.template(rows)
    value['rubric_version'] = VERSION
    return value

def coverage_score(d, protocol):
    level = d.get('acquisition_level')
    if level not in {'page_not_obtained','frame_only','partial_body','complete_body','unknown'}:
        raise ValueError('须单独记录正文取得程度')
    if not d.get('return_kind'): raise ValueError('须独立记录返回形式')
    if d.get('score') is None: return None
    if level == 'page_not_obtained': return 1
    if level == 'frame_only': return 2
    if level == 'complete_body':
        if not d.get('completeness_basis'): raise ValueError('完整取得须有完整性核对依据')
        return 5
    if level != 'partial_body': raise ValueError('未知正文状态不能评分')
    c = d.get('coverage') or {}
    if c.get('unit_type') not in {'paragraph','section','page'} or c.get('unit_type') != protocol.get('m2_coverage_unit') or not protocol.get('m2_unit_rule'):
        raise ValueError('覆盖单元须在执行协议中固定')
    ref = c.get('reference') or {}
    if any(not ref.get(k) for k in ('url','version_scope','captured_at','tool','content','unit_spans')):
        raise ValueError('须保存参照正文及来源、范围和单元位置')
    units=c.get('reference_units');got=c.get('returned_units')
    if not isinstance(units,list) or not isinstance(got,list) or not units or not got:
        raise ValueError('部分正文须有非空参照及取得单元清单')
    if len(set(units))!=len(units) or len(set(got))!=len(got) or not set(got)<=set(units):
        raise ValueError('正文单元重复或超出参照')
    spans=ref['unit_spans']
    for uid in units:
        span=spans.get(uid)
        if not isinstance(span,list) or len(span)!=2 or any(type(x)!=int for x in span) or not 0<=span[0]<span[1]<=len(ref['content']):
            raise ValueError('参照单元须能定位到保存的原文')
    if type(c.get('within_unit_truncation')) is not bool: raise ValueError('须说明单元内是否截断')
    if len(got)==len(units) and not c['within_unit_truncation']:
        raise ValueError('全部完整取得应检查5分，不能标部分正文')
    for uid in got:
        refs=(c.get('unit_evidence') or {}).get(uid,[])
        if not refs or not set(refs)<=set(d.get('evidence_refs',[])):
            raise ValueError('取得单元须引用本篇文档实际返回证据')
    return 3 if 2*len(got)<len(units) else 4

def validate(rows,value):
    protocol=rows[0]['metadata'].get('protocol',{})
    for d in value['metrics'][1]['observation']['targets']:
        if coverage_score(d,protocol)!=d.get('score'): raise ValueError('M2分值与覆盖依据不一致')
    previous.validate(rows,value,coverage=True)
