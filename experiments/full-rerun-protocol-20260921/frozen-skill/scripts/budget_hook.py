#!/usr/bin/env python3
"""WorkBuddy PreToolUse budget gate. Temporary ledger is NOT a dispatch log."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import sys
import shlex

ROLES = {'WebSearch': 'search', 'WebFetch': 'fetch', 'web_search': 'search', 'web_fetch': 'fetch'}

def decide(path, event, limits):
    if any(type(limits.get(k)) is not int or limits[k] < 0 for k in ('search', 'fetch')):
        raise ValueError('须配置非负整数预算')
    if event.get('hook_event_name') != 'PreToolUse':
        raise ValueError('仅支持PreToolUse')
    session = event.get('session_id')
    role = ROLES.get(event.get('tool_name'))
    if not session or role is None:
        raise ValueError('缺少会话或未知工具，停止派发')
    # Separate sessions share no budget. Lock check+reservation against concurrent hooks.
    with path.open('a+', encoding='utf-8') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0)
        rows = [json.loads(x) for x in f if x.strip()]
        if rows and (rows[0]['session_id'] != session or rows[0]['limits'] != limits):
            raise ValueError('预算账本不能跨会话复用或中途更改上限')
        used = sum(x['allowed'] and x['role'] == role for x in rows)
        allowed = used < limits[role]
        row = dict(seq=len(rows)+1, session_id=session, limits=limits, role=role,
                   tool_name=event['tool_name'], tool_input=event.get('tool_input', {}),
                   allowed=allowed, reserved_count=used+int(allowed))
        # WorkBuddy may omit tool_use_id; never merge identical retry arguments.
        if event.get('tool_use_id'): row['tool_use_id'] = event['tool_use_id']
        f.seek(0, 2)
        f.write(json.dumps(row, ensure_ascii=False)+'\n'); f.flush(); os.fsync(f.fileno())
    message = (f'BENCHMARK_BUDGET_RESERVED {role} {used+1}/{limits[role]}' if allowed else
               f'BENCHMARK_BUDGET_DENIED {role}: 上限{limits[role]}次，本请求未派发。请使用已有材料完成回答，不再重试此类工具。')
    # Allow path leaves existing tool permissions intact; it is not an authorization grant.
    output = {'hookEventName': 'PreToolUse', 'additionalContext': message}
    if not allowed: output.update(permissionDecision='deny', permissionDecisionReason=message)
    return {'hookSpecificOutput': output}

def rejection_for(state, tool_use_id):
    """Use hook evidence, not a denial-looking string in an untrusted webpage."""
    if not tool_use_id or not state.exists(): return None
    with state.open(encoding='utf-8') as f:
        fcntl.flock(f, fcntl.LOCK_SH)
        rows=[json.loads(x) for x in f if x.strip()]
    return next((r for r in reversed(rows) if r.get('tool_use_id')==tool_use_id and not r['allowed']),None)


def workbuddy_settings(state, search, fetch):
    """Merge this hooks object into a run's explicit settings; no global mutation."""
    command=shlex.join([sys.executable,str(Path(__file__).resolve()),'--state',str(Path(state).resolve()),
                        '--search',str(search),'--fetch',str(fetch)])
    return {'hooks':{'PreToolUse':[{'matcher':'WebSearch|WebFetch|web_search|web_fetch',
                                  'hooks':[{'type':'command','command':command}]}]}}


def main():
    p=argparse.ArgumentParser();p.add_argument('--state',type=Path,required=True)
    p.add_argument('--search',type=int,required=True);p.add_argument('--fetch',type=int,required=True)
    args=p.parse_args()
    try: output=decide(args.state,json.load(sys.stdin),dict(search=args.search,fetch=args.fetch))
    except Exception as e:
        # Non-zero exit can be treated as non-blocking by clients: return an explicit deny.
        output={'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'deny',
            'permissionDecisionReason':'BENCHMARK_BUDGET_ERROR: '+str(e)}}
    print(json.dumps(output,ensure_ascii=False))

if __name__=='__main__': main()
