#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml


def _discover_root() -> Path:
    explicit = os.environ.get("CURSOR_FRAMEWORK_ROOT")
    if explicit:
        return Path(explicit).resolve()
    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        if (candidate / "VERSION").is_file() and (candidate / ".cursor" / "framework.json").is_file():
            return candidate
    raise RuntimeError("Cannot locate repository root (VERSION + .cursor/framework.json)")

ROOT=_discover_root(); PY=sys.executable; FAIL=[]
def check(c,m):
    if not c: FAIL.append(m)
def run_validator(temp):
    env=os.environ.copy(); env['CURSOR_FRAMEWORK_ROOT']=str(temp); env['PYTHONUTF8']='1'; env['PYTHONIOENCODING']='utf-8'; return subprocess.run([PY,'-B',str(ROOT/'.cursor/skills/learning-check/scripts/validate_cursor_learning.py')],text=True,encoding='utf-8',errors='replace',capture_output=True,env=env,timeout=15)
def build():
    temp=Path(tempfile.mkdtemp(prefix='cursor-learning-eval-')); (temp/'.cursor').mkdir(); shutil.copy2(ROOT/'.cursor/framework.json',temp/'.cursor/framework.json'); shutil.copytree(ROOT/'.cursor/learning',temp/'.cursor/learning'); shutil.copytree(ROOT/'.cursor/skills',temp/'.cursor/skills'); return temp
def proposal(tasks=None):
    tasks=tasks or ['task-a','task-b']; return {'schema_version':1,'id':'LEARN-20990101-001','status':'ACCEPTED','created_at':'2099-01-01','summary':'Prevent a deterministic repeated framework regression','severity':'NORMAL','source_refs':['eval://fixture'],'occurrences':[{'task_ref':x,'evidence_ref':f'eval://{x}'} for x in tasks],'problem':{'observed_behavior':'bad','expected_behavior':'good','reproduction':'python eval.py'},'proposal':{'target_type':'EVAL','target_paths':['.cursor/evals/fixture-target.txt'],'change_summary':'add regression coverage','blast_radius':'framework eval only'},'replay':{'before_cases':['case-a'],'before_result':'fails before','after_cases':['case-a'],'after_result':'passes after'},'validation':{'commands':['python eval.py'],'evidence_refs':['.cursor/evals/validation.txt'],'result':'PASS'},'approvals':[],'promotion':{'authorization_ref':'user://explicit','promoted_at':'2099-01-01T00:00:00Z','promoted_digest':'a'*64,'regression_digest':'b'*64}}
def install(temp,d):
    p=temp/'.cursor/learning/accepted/LEARN-20990101-001.yaml'; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(yaml.safe_dump(d,sort_keys=False),encoding='utf-8'); rp=temp/'.cursor/learning/REGISTRY.yaml'; r=yaml.safe_load(rp.read_text(encoding='utf-8')) or {}; r['entries']=[{'id':d['id'],'status':d['status'],'file':'.cursor/learning/accepted/LEARN-20990101-001.yaml'}]; rp.write_text(yaml.safe_dump(r,sort_keys=False),encoding='utf-8'); (temp/'.cursor/evals').mkdir(parents=True,exist_ok=True); (temp/'.cursor/evals/fixture-target.txt').write_text('target\n',encoding='utf-8'); (temp/'.cursor/evals/validation.txt').write_text('PASS\n',encoding='utf-8')
# valid proposal without mandatory reviewers passes
for mode in ('valid','single','no-validation','cycle'):
    temp=build()
    try:
        d=proposal(tasks=['task-a'] if mode=='single' else None); install(temp,d)
        if mode=='no-validation':
            p=temp/'.cursor/learning/accepted/LEARN-20990101-001.yaml'; x=yaml.safe_load(p.read_text(encoding='utf-8')); x['validation']['result']='FAIL'; p.write_text(yaml.safe_dump(x,sort_keys=False),encoding='utf-8')
        if mode=='cycle':
            rp=temp/'.cursor/learning/SKILL_RELATIONS.yaml'; x=yaml.safe_load(rp.read_text(encoding='utf-8')); x['relations'].extend([{'from':'capture-learning','to':'consolidate-learning','type':'requires'},{'from':'consolidate-learning','to':'capture-learning','type':'requires'}]); rp.write_text(yaml.safe_dump(x,sort_keys=False),encoding='utf-8')
        cp=run_validator(temp)
        if mode=='valid': check(cp.returncode==0,'valid accepted proposal rejected: '+cp.stdout)
        elif mode=='single': check(cp.returncode!=0 and 'requires >=2 independent task occurrences' in cp.stdout,'single occurrence not rejected')
        elif mode=='no-validation': check(cp.returncode!=0 and 'deterministic validation PASS' in cp.stdout,'failed validation not rejected')
        elif mode=='cycle': check(cp.returncode!=0 and 'requires cycle' in cp.stdout,'requires cycle not rejected')
    finally: shutil.rmtree(temp,ignore_errors=True)
if FAIL:
    print('LEARNING GATE EVAL FAILED'); [print('-',x) for x in FAIL]; raise SystemExit(1)
print('LEARNING GATE EVAL PASS')
