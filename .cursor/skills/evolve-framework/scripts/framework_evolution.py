#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path


def _discover_root() -> Path:
    explicit = os.environ.get("CURSOR_FRAMEWORK_ROOT")
    if explicit:
        return Path(explicit).resolve()
    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        if (candidate / "VERSION").is_file() and (candidate / ".cursor" / "framework.json").is_file():
            return candidate
    raise RuntimeError("Cannot locate repository root (VERSION + .cursor/framework.json)")

ROOT=_discover_root()
STATE=ROOT/'.cursor/runtime/evolution_state.json'; FRAMEWORK=ROOT/'.cursor/framework.json'
STAGES=['ORIENT','REFRESH_KB','SELECT_PROPOSALS','IMPLEMENT_CANDIDATE','REPLAY','VALIDATE','PROMOTE','RELEASE']

def load_state():
    try:
        v=json.loads(STATE.read_text(encoding='utf-8')); return v if isinstance(v,dict) else {}
    except Exception: return {}
def save(v):
    STATE.parent.mkdir(parents=True,exist_ok=True); t=STATE.with_suffix('.tmp'); t.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); t.replace(STATE)
def semver(v):
    m=re.fullmatch(r'(\d+)\.(\d+)\.(\d+)',v)
    if not m: raise ValueError(v)
    return tuple(int(x) for x in m.groups())
def release_gate(state):
    if state.get('stage')!='RELEASE': return False,'stage must be RELEASE'
    validations=list(state.get('validations') or [])
    if not validations: return False,'deterministic validation evidence missing'
    latest=validations[-1]
    if latest.get('status')!='PASS' or not str(latest.get('evidence_ref') or '').strip(): return False,'latest deterministic validation must PASS with evidence_ref'
    if state.get('recovery_required'): return False,'recovery_required must be cleared explicitly'
    return True,'deterministic release gate passed'

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
    s=sub.add_parser('start'); s.add_argument('--target',required=True); s.add_argument('--goal',required=True)
    s=sub.add_parser('stage'); s.add_argument('stage',choices=STAGES); s.add_argument('--next-action',required=True)
    s=sub.add_parser('validate'); s.add_argument('--status',choices=['PASS','FAIL'],required=True); s.add_argument('--evidence-ref',required=True)
    sub.add_parser('status'); sub.add_parser('finish'); args=ap.parse_args()
    if args.cmd=='start':
        if load_state().get('active'): print('ERROR: an evolution release is already active'); return 4
        current=str(json.loads(FRAMEWORK.read_text(encoding='utf-8')).get('framework_version','0.0.0'))
        try:
            if semver(args.target)<=semver(current): print(f'ERROR: target {args.target} must be newer than current {current}'); return 4
        except ValueError: print('ERROR: versions must be simple semver'); return 4
        save({'active':True,'target_version':args.target,'goal':args.goal,'stage':'ORIENT','next_action':'读取框架/知识库并冻结本次目标。','validations':[],'release_gate':'PENDING','max_followups':5,'recovery_required':False,'started_at':datetime.now(timezone.utc).isoformat()}); return 0
    state=load_state()
    if not state: print('ERROR: no active evolution state'); return 2
    if args.cmd=='stage': state['stage']=args.stage; state['next_action']=args.next_action; state['updated_at']=datetime.now(timezone.utc).isoformat(); save(state); return 0
    if args.cmd=='validate':
        state.setdefault('validations',[]).append({'status':args.status,'evidence_ref':args.evidence_ref,'at':datetime.now(timezone.utc).isoformat()}); state['updated_at']=datetime.now(timezone.utc).isoformat(); save(state); return 0
    if args.cmd=='finish':
        ok,reason=release_gate(state)
        if not ok: state['release_gate']='FAIL'; state['next_action']=f'发布门禁未通过：{reason}；回到 VALIDATE/REWORK。'; state['stage']='VALIDATE'; state['updated_at']=datetime.now(timezone.utc).isoformat(); save(state); print('REJECTED:',reason); return 3
        state['active']=False; state['release_gate']='PASS'; state['finished_at']=datetime.now(timezone.utc).isoformat(); save(state); print('PASS: deterministic release gate satisfied'); return 0
    print(json.dumps(state,ensure_ascii=False,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
