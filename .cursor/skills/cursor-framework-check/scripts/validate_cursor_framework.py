#!/usr/bin/env python3
from __future__ import annotations

import ast
import datetime as dt
import json
import os
import re
from pathlib import Path
from typing import Any

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

ROOT = _discover_root()
CURSOR = ROOT / '.cursor'
errors: list[str] = []
warnings: list[str] = []
FM = re.compile(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)', re.S)

def err(msg:str): errors.append(msg)
def warn(msg:str): warnings.append(msg)
def parse_date(value: Any, label: str) -> dt.date | None:
    try:
        return dt.date.fromisoformat(str(value))
    except ValueError:
        err(f'invalid date: {label}: {value!r}')
        return None

def validation_date() -> dt.date:
    injected = os.environ.get('CURSOR_VALIDATION_DATE')
    if injected:
        parsed = parse_date(injected, 'CURSOR_VALIDATION_DATE')
        return parsed or dt.datetime.now(dt.timezone.utc).date()
    return dt.datetime.now(dt.timezone.utc).date()

VALIDATION_DATE = validation_date()

def parse_fm(path:Path)->dict[str,Any]:
    text=path.read_text(encoding='utf-8'); m=FM.match(text)
    if not m: err(f'missing frontmatter: {path.relative_to(ROOT)}'); return {}
    try:
        data=yaml.safe_load(m.group(1)) or {}
        if not isinstance(data,dict): raise TypeError('not mapping')
        return data
    except Exception as exc:
        err(f'bad frontmatter: {path.relative_to(ROOT)}: {exc}'); return {}

try: fw=json.loads((CURSOR/'framework.json').read_text(encoding='utf-8'))
except Exception as exc: err(f'framework.json invalid: {exc}'); fw={}
if fw.get('schema_version') != 2: err('framework schema_version must be 2')
version=str(fw.get('framework_version') or '')
if not re.fullmatch(r'\d+\.\d+\.\d+',version): err('framework_version must be semver')
root_version=(ROOT/'VERSION').read_text(encoding='utf-8').strip() if (ROOT/'VERSION').exists() else ''
if root_version != version: err(f'VERSION/framework mismatch: {root_version!r} != {version!r}')
expected=os.environ.get('CURSOR_EXPECTED_FRAMEWORK_VERSION')
if expected and version != expected: err(f'expected framework version {expected}')
if 'research_os_baseline' in fw: err('research_os_baseline must not exist under unified version policy')
profiles=fw.get('cursor_runtime_profiles') or {}
if (profiles.get('ide_local') or {}).get('status') != 'supported': err('ide_local Cursor runtime profile must be supported')
cloud=profiles.get('cloud_agent') or {}
if cloud.get('status') != 'conditional': err('cloud_agent profile must be conditional')
cloud_missing=set(cloud.get('unsupported_project_hook_dependencies') or [])
for event in ('sessionStart','sessionEnd','beforeMCPExecution','afterMCPExecution'):
    if event not in cloud_missing: err(f'cloud_agent compatibility profile missing unsupported/deferred hook: {event}')
cloud_knowledge=CURSOR/'knowledge/CLOUD_AGENT_COMPATIBILITY.md'
if not cloud_knowledge.is_file(): err('missing Cloud Agent compatibility knowledge')
else:
    cloud_text=cloud_knowledge.read_text(encoding='utf-8')
    for phrase in ('早期只读','项目 Hook 完全不运行','不得依赖项目 Hook','beforeMCPExecution'):
        if phrase not in cloud_text: err(f'Cloud compatibility knowledge missing early-readonly caveat: {phrase}')

compatibility_path=CURSOR/'compatibility/CURSOR_COMPATIBILITY.yaml'
try: compatibility=yaml.safe_load(compatibility_path.read_text(encoding='utf-8')) or {}
except Exception as exc: err(f'Cursor compatibility matrix invalid: {exc}'); compatibility={}
if compatibility.get('schema_version') != 1: err('Cursor compatibility schema_version must be 1')
compat_verified=parse_date(compatibility.get('knowledge_verified_at'), 'compatibility.knowledge_verified_at')
if compat_verified is not None and compat_verified > VALIDATION_DATE:
    err('Cursor compatibility knowledge_verified_at must not be in the future')
runtime_entries=compatibility.get('runtime_tested_versions') or []
if not isinstance(runtime_entries,list) or not runtime_entries:
    err('Cursor compatibility must contain runtime-tested versions')
    runtime_entries=[]
seen_runtime=set()
for entry in runtime_entries:
    if not isinstance(entry,dict): err('Cursor runtime compatibility entry must be a mapping'); continue
    key=(entry.get('cursor_version'),entry.get('platform'))
    if key in seen_runtime: err(f'duplicate Cursor runtime compatibility entry: {key}')
    seen_runtime.add(key)
    if not re.fullmatch(r'\d+\.\d+\.\d+',str(entry.get('cursor_version') or '')):
        err(f'invalid Cursor runtime version: {entry.get("cursor_version")!r}')
    tested_at=parse_date(entry.get('tested_at'), f'Cursor runtime {key}.tested_at')
    if tested_at is not None and tested_at > VALIDATION_DATE: err(f'Cursor runtime test is in the future: {key}')
    status=entry.get('status')
    if status not in {'PASS','PASS_WITH_MITIGATION'}: err(f'invalid Cursor runtime status: {key}: {status!r}')
    for group,required_probes in {
        'live_probes': {'normal_read_allowed','pretool_secret_read_denied','powershell_root_delete_denied'},
        'subprocess_probes': {'utf8_bom_input','utf8_json_output','malformed_json_fail_closed','invalid_utf8_fail_closed','security_behavior_matrix'},
    }.items():
        probes=entry.get(group) or {}
        if not isinstance(probes,dict): err(f'Cursor runtime {key} {group} must be a mapping'); continue
        missing_probes=required_probes-set(probes)
        if missing_probes: err(f'Cursor runtime {key} missing {group}: {sorted(missing_probes)}')
        failed={name for name,value in probes.items() if value != 'PASS'}
        if failed: err(f'Cursor runtime {key} has non-PASS {group}: {sorted(failed)}')
    caveats=entry.get('caveats') or []
    if status=='PASS_WITH_MITIGATION' and not any(
        isinstance(item,dict) and item.get('id') and item.get('mitigation') for item in caveats
    ):
        err(f'Cursor runtime {key} PASS_WITH_MITIGATION requires a documented mitigation')
if ('3.14.7','windows') not in seen_runtime:
    err('Cursor compatibility missing live-tested 3.14.7/windows entry')
required_probe_ids={'hook_json_utf8_bom','malformed_input_fail_closed','pretool_secret_read_denied','dangerous_shell_denied'}
declared_probe_ids=set(compatibility.get('probes') or [])
if not required_probe_ids <= declared_probe_ids:
    err(f'Cursor compatibility missing required probe declarations: {sorted(required_probe_ids-declared_probe_ids)}')

hook_eval_path=CURSOR/'skills/cursor-framework-check/scripts/run_cursor_hook_evals.py'
security_cases_path=CURSOR/'evals/cases/security.yaml'
for required_path in (hook_eval_path,security_cases_path):
    if not required_path.is_file(): err(f'missing Hook negative-test asset: {required_path.relative_to(ROOT)}')
if hook_eval_path.is_file():
    hook_eval_text=hook_eval_path.read_text(encoding='utf-8')
    for token in ('with_bom=True','"malformed"','"non-object"','"invalid-utf8"','raw_stdout.decode("utf-8")'):
        if token not in hook_eval_text: err(f'Hook eval missing transport negative case: {token}')
quality=fw.get('quality_policy') or {}
allowed_quality={'deterministic_release_gate','scoped_review','reviewer_selection'}
if set(quality)-allowed_quality: err(f'unsupported quality_policy keys: {sorted(set(quality)-allowed_quality)}')
if quality.get('deterministic_release_gate') is not True: err('deterministic release gate required')
if quality.get('scoped_review') is not True: err('scoped review policy required')
sub=fw.get('subagent_policy') or {}
if sub.get('delegation_is_optional') is not True: err('subagent delegation must be optional')
if sub.get('max_parallel_per_wave') != 3: err('subagent max_parallel_per_wave must be 3 (<4)')
if sub.get('cumulative_task_limit') is not None: err('subagent cumulative task limit must be unset')
if sub.get('nested_delegation') is not False: err('nested subagent delegation must be disabled')
# Cursor supports limited nesting; no-nesting here must stay documented as an intentionally stricter project policy.
delegation_rule=(CURSOR/'rules'/'10-agent-delegation.mdc')
if delegation_rule.exists():
    delegation_text=delegation_rule.read_text(encoding='utf-8')
    if '更严格项目策略' not in delegation_text or 'Cursor 当前官方能力本身支持有限一层 nested subagent' not in delegation_text:
        err('delegation rule must distinguish stricter project no-nesting policy from Cursor platform capability')
if sub.get('custom_reviewers_background') is not False: err('custom reviewers must be foreground for current hook compatibility')

for rel in (
 '.cursor/learning/README.md','.cursor/learning/REGISTRY.yaml','.cursor/learning/SKILL_RELATIONS.yaml',
 '.cursor/skills/capture-learning/SKILL.md','.cursor/skills/consolidate-learning/SKILL.md',
 '.cursor/skills/promote-learning/SKILL.md','.cursor/skills/evolve-framework/SKILL.md',
 '.cursor/skills/learning-check/scripts/validate_cursor_learning.py','.cursor/skills/learning-check/scripts/run_cursor_learning_evals.py','.cursor/skills/cursor-framework-check/scripts/run_cursor_framework_evals.py',
 '.cursor/skills/framework-release/scripts/release_cursor_framework.py','.cursor/skills/framework-release/scripts/verify_cursor_framework_release.py'):
    if not (ROOT/rel).exists(): err(f'missing evolution asset: {rel}')
if not (fw.get('self_evolution') or {}).get('require_explicit_user_intent'): err('self evolution must require explicit user intent')
se=fw.get('self_evolution') or {}
if se.get('learning_lifecycle') != ['OBSERVE','PROPOSE','CONSOLIDATE','REPLAY','VALIDATE','PROMOTE']: err('learning_lifecycle mismatch')
if se.get('framework_evolution_lifecycle') != ['ORIENT','REFRESH_KB','SELECT_PROPOSALS','IMPLEMENT_CANDIDATE','REPLAY','VALIDATE','PROMOTE','RELEASE']: err('framework_evolution_lifecycle mismatch')
if 'lifecycle' in se: err('ambiguous self_evolution.lifecycle is forbidden; use explicit lifecycle fields')

try: kb=yaml.safe_load((CURSOR/'knowledge/SOURCES.yaml').read_text(encoding='utf-8')) or {}
except Exception as exc: err(f'knowledge sources invalid: {exc}'); kb={}
kb_verified=parse_date(kb.get('verified_at'), 'SOURCES.yaml.verified_at')
fw_verified=parse_date((fw.get('cursor_knowledge') or {}).get('verified_at'), 'framework.cursor_knowledge.verified_at')
if kb_verified is not None and kb_verified > VALIDATION_DATE: err('SOURCES.yaml verified_at must not be in the future')
if fw_verified is not None and fw_verified > VALIDATION_DATE: err('framework cursor_knowledge verified_at must not be in the future')
if kb_verified is not None and fw_verified is not None and kb_verified != fw_verified:
    err('framework cursor_knowledge verified_at must match SOURCES.yaml')
required={'cursor-rules','cursor-skills','cursor-subagents','cursor-hooks','cursor-mcp','cursor-ignore','cursor-plugins','cursor-plan-mode'}
source_ids=set()
refresh_after_days=(kb.get('policy') or {}).get('refresh_after_days')
if not isinstance(refresh_after_days,int) or isinstance(refresh_after_days,bool) or refresh_after_days <= 0:
    err('knowledge refresh_after_days must be a positive integer')
    refresh_after_days=30
for source in kb.get('sources') or []:
    if not isinstance(source,dict): err('knowledge source must be mapping'); continue
    sid=source.get('id'); source_ids.add(sid)
    if not source.get('url') or not source.get('tier'): err(f'incomplete knowledge source: {sid}')
    if source.get('tier')=='T1_OFFICIAL' and not str(source.get('url')).startswith(('https://cursor.com/','https://docs.cursor.com/')):
        err(f'T1_OFFICIAL must be Cursor-owned: {sid}')
    verified=parse_date(source.get('verified_at'), f'knowledge source {sid}.verified_at')
    if verified is not None:
        age=(VALIDATION_DATE-verified).days
        if age < 0: err(f'knowledge source verified_at is in the future: {sid}: {verified}')
        elif age > refresh_after_days: warn(f'stale knowledge source: {sid}')
if not required <= source_ids: err(f'missing official sources: {sorted(required-source_ids)}')

rule_dir=CURSOR/'rules'
if list(rule_dir.rglob('*.md')): err('plain .md in .cursor/rules is not accepted; use .mdc')
allowed_rule_fields={'description','globs','alwaysApply'}
for path in rule_dir.rglob('*.mdc'):
    fm=parse_fm(path)
    unknown=set(fm)-allowed_rule_fields
    if unknown: err(f'unsupported/new Rule frontmatter fields require knowledge refresh: {path.relative_to(ROOT)}: {sorted(unknown)}')
    if not isinstance(fm.get('alwaysApply'),bool): err(f'alwaysApply must be bool: {path.relative_to(ROOT)}')
    description=fm.get('description')
    if description is not None and not isinstance(description,str): err(f'Rule description must be string or empty: {path.relative_to(ROOT)}')
    globs=fm.get('globs')
    # Cursor's current Rule docs expose globs as a single frontmatter value; keep
    # repository Rules on the comma-separated string form rather than relying on
    # parser-specific YAML-list behavior observed in community reports.
    if globs is not None and not isinstance(globs,str): err(f'Rule globs must use a comma-separated string: {path.relative_to(ROOT)}')

skill_name_re=re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
for path in CURSOR.rglob('SKILL.md'):
    if '/skills/' not in path.as_posix(): continue
    fm=parse_fm(path)
    name=fm.get('name')
    if name != path.parent.name: err(f'skill name/folder mismatch: {path.relative_to(ROOT)}')
    if not isinstance(name,str) or not skill_name_re.fullmatch(name): err(f'skill name must use lowercase letters/numbers/hyphens: {path.relative_to(ROOT)}')
    if not str(fm.get('description') or '').strip(): err(f'skill description missing: {path.relative_to(ROOT)}')
    allowed_skill_fields={'name','description','paths','disable-model-invocation','metadata'}
    unknown=set(fm)-allowed_skill_fields
    if unknown: err(f'unsupported/new Skill frontmatter fields require knowledge refresh: {path.relative_to(ROOT)}: {sorted(unknown)}')
    if 'globs' in fm: err(f'new Skills must use paths, not legacy globs: {path.relative_to(ROOT)}')
    if 'paths' in fm:
        paths=fm.get('paths')
        if isinstance(paths,str):
            if not paths.strip(): err(f'Skill paths string must be non-empty: {path.relative_to(ROOT)}')
        elif isinstance(paths,list):
            if not paths or not all(isinstance(x,str) and x.strip() for x in paths): err(f'Skill paths list must contain non-empty strings: {path.relative_to(ROOT)}')
        else:
            err(f'Skill paths must be a comma-separated string or list: {path.relative_to(ROOT)}')
    if 'disable-model-invocation' in fm and not isinstance(fm.get('disable-model-invocation'),bool): err(f'disable-model-invocation must be bool: {path.relative_to(ROOT)}')
    if 'metadata' in fm and not isinstance(fm.get('metadata'),dict): err(f'Skill metadata must be a mapping: {path.relative_to(ROOT)}')

for skill_name in ('framework-release','cursor-framework-check','semantic-commit','promote-learning','evolve-framework','engineering-memory','capture-learning','refresh-cursor-kb'):
    fm=parse_fm(CURSOR/'skills'/skill_name/'SKILL.md')
    if fm.get('disable-model-invocation') is not True: err(f'high-risk skill must require explicit invocation: {skill_name}')

expected_agents={'architecture-reviewer','verification-reviewer','security-governance-reviewer'}
allowed_agent_fields={'name','description','model','readonly','is_background'}
agent_name_re=re.compile(r'^[a-z]+(?:-[a-z]+)*$')
seen=set()
for path in (CURSOR/'agents').glob('*.md'):
    fm=parse_fm(path); name=fm.get('name'); seen.add(name)
    unknown=set(fm)-allowed_agent_fields
    if unknown: err(f'unsupported/new Subagent frontmatter fields require knowledge refresh: {path.name}: {sorted(unknown)}')
    if not isinstance(name,str) or not agent_name_re.fullmatch(name): err(f'subagent name must use lowercase letters and hyphens: {path.name}')
    if name != path.stem: err(f'subagent name/file mismatch: {path.name}')
    if not str(fm.get('description') or '').strip(): err(f'agent description missing: {path.name}')
    if not isinstance(fm.get('model'),str): err(f'subagent model must be string: {path.name}')
    if fm.get('readonly') is not True: err(f'reviewer must be readonly: {path.name}')
    if fm.get('model') != 'inherit': err(f'reviewer model must inherit: {path.name}')
    if fm.get('is_background') is not False: err(f'reviewer must be foreground under current subagentStop caveat: {path.name}')
    if '禁止启动或委派任何子代理' not in path.read_text(encoding='utf-8'): err(f'reviewer missing no-delegation instruction: {path.name}')
    reviewer_text=path.read_text(encoding='utf-8')
    if 'readonly: true` 只代表 Cursor 对文件编辑/状态变更 Shell 的限制' not in reviewer_text or '未经用户显式批准不得调用 MCP' not in reviewer_text:
        err(f'reviewer must not overclaim readonly/MCP isolation: {path.name}')
if seen != expected_agents: err(f'reviewer agent set mismatch: {seen ^ expected_agents}')

try: hooks=json.loads((CURSOR/'hooks.json').read_text(encoding='utf-8'))
except Exception as exc: err(f'hooks.json invalid: {exc}'); hooks={}
if set(hooks)-{'version','hooks'}: err(f'unsupported hooks.json top-level keys: {sorted(set(hooks)-{"version","hooks"})}')
if hooks.get('version') != 1: err('hooks version must be 1')
required_events={'sessionStart','beforeShellExecution','beforeMCPExecution','preToolUse','subagentStart','subagentStop','stop'}
official_events={
    'sessionStart','sessionEnd','preToolUse','postToolUse','postToolUseFailure','subagentStart','subagentStop',
    'beforeShellExecution','afterShellExecution','beforeMCPExecution','afterMCPExecution','beforeReadFile','afterFileEdit',
    'beforeSubmitPrompt','preCompact','stop','afterAgentResponse','afterAgentThought','beforeTabFileRead','afterTabFileEdit','workspaceOpen'
}
hook_map=hooks.get('hooks') or {}
if not isinstance(hook_map,dict): err('hooks must be an object'); hook_map={}
unknown_events=set(hook_map)-official_events
if unknown_events: err(f'unsupported/new Hook events require knowledge refresh: {sorted(unknown_events)}')
missing=required_events-set(hook_map.keys())
if missing: err(f'missing hook events: {sorted(missing)}')
guard_events={'beforeReadFile','beforeShellExecution','beforeMCPExecution','preToolUse','subagentStart'}
allowed_hook_entry_fields={'command','type','timeout','loop_limit','failClosed','matcher','prompt','model'}
for event,entries in hook_map.items():
    if not isinstance(entries,list): err(f'hook event not list: {event}'); continue
    for entry in entries:
        if not isinstance(entry,dict): err(f'hook entry must be object: {event}'); continue
        unknown=set(entry)-allowed_hook_entry_fields
        if unknown: err(f'unsupported/new Hook entry fields require knowledge refresh: {event}: {sorted(unknown)}')
        hook_type=entry.get('type','command')
        if hook_type not in {'command','prompt'}: err(f'hook type must be command or prompt: {event}')
        if hook_type=='command':
            cmd=entry.get('command','')
            if not isinstance(cmd,str) or not cmd.strip(): err(f'command hook missing command: {event}'); cmd=''
            parts=cmd.split(); script=next((x for x in reversed(parts) if x.endswith(('.py','.sh','.ts','.js'))),'')
            if not script or not (ROOT/script).exists(): err(f'hook script missing: {event}: {script or cmd}')
            if 'prompt' in entry or 'model' in entry: err(f'command hook must not declare prompt/model: {event}')
        else:
            if not str(entry.get('prompt') or '').strip(): err(f'prompt hook missing prompt: {event}')
            if 'command' in entry: err(f'prompt hook must not declare command: {event}')
        timeout=entry.get('timeout')
        if not isinstance(timeout,(int,float)) or timeout <= 0 or timeout > 30: err(f'hook timeout must be explicit and <=30s: {event}')
        if 'loop_limit' in entry and event not in {'stop','subagentStop'}: err(f'loop_limit only valid for stop/subagentStop: {event}')
        if event in guard_events and entry.get('failClosed') is not True: err(f'guard hook must failClosed: {event}')
        if event=='preToolUse' and entry.get('command','').endswith('subagent_pretool_guard.py') and entry.get('matcher')!='Task': err('subagent preToolUse guard must use matcher=Task')
        if event=='preToolUse' and entry.get('command','').endswith('secret_guard.py') and entry.get('matcher')!='Read': err('secret preToolUse guard must use matcher=Read')
read_guards=[entry for entry in (hook_map.get('preToolUse') or []) if isinstance(entry,dict) and entry.get('command','').endswith('secret_guard.py')]
if len(read_guards) != 1 or read_guards[0].get('matcher') != 'Read' or read_guards[0].get('failClosed') is not True:
    err('Read secret guard must be bound exactly once as fail-closed preToolUse matcher=Read')
for entry in hook_map.get('beforeReadFile') or []:
    if isinstance(entry,dict) and entry.get('command','').endswith('secret_guard.py'):
        err('secret guard must not bind beforeReadFile; Cursor 3.14.7 Windows may serialize file content as invalid JSON')
# Cursor-native context protection layer must exist for real secrets.
cursorignore = ROOT/'.cursorignore'
if not cursorignore.exists(): err('.cursorignore is required')
else:
    ci = cursorignore.read_text(encoding='utf-8')
    for pat in ('.env', '*.pem', '*.key'):
        if pat not in ci: err(f'.cursorignore missing sensitive pattern: {pat}')


# Unified version semantics must also hold in active Rule/Hook/Agent assets.
for rel in ('.cursor/rules/21-cursor-framework-governance.mdc','.cursor/hooks/session_context.py'):
    txt=(ROOT/rel).read_text(encoding='utf-8')
    if 'research_os_baseline' in txt or '产品架构基线' in txt or '版本与 Research OS 产品架构版本分离' in txt:
        err(f'unified version policy residue: {rel}')
for agent in (CURSOR/'agents').glob('*.md'):
    txt=agent.read_text(encoding='utf-8')
    if re.search(r'`?score:\s*0(?:\.0)?-10(?:\.0)?`?',txt): err(f'numeric reviewer self-score is forbidden: {agent.relative_to(ROOT)}')


# Internal autonomy/architecture conflict checks.
git_rule=(CURSOR/'rules/43-git-commit-policy.mdc').read_text(encoding='utf-8')
if '每个任务默认一个本地语义提交' in git_rule: err('Git policy must not auto-commit every task')
if '最新 recheck' in git_rule and '如果任务流程要求' not in git_rule: err('Git policy must not unconditionally require recheck')
arch_rule=(CURSOR/'rules/44-code-architecture.mdc')
arch_fm=parse_fm(arch_rule); arch_text=arch_rule.read_text(encoding='utf-8')
if arch_fm.get('alwaysApply') is not False or not arch_fm.get('globs'): err('code architecture Rule must be scoped, not Always')
if 'domain → application → adapter/infra' in arch_text: err('architecture Rule contains invalid domain-to-application runtime flow')
for phrase in ('entry adapter → application use case → domain','application → inward-owned Port → adapter / infrastructure'):
    if phrase not in arch_text: err(f'architecture Rule missing runtime flow: {phrase}')

# Ordinary CI must be frozen, cross-platform and read-only with respect to release evidence.
ci_path = ROOT / ".github/workflows/m0-quality.yml"
if not ci_path.is_file():
    err("missing Windows/Linux M0 CI workflow")
else:
    ci_text = ci_path.read_text(encoding="utf-8")
    try:
        ci_document = yaml.safe_load(ci_text)
        if not isinstance(ci_document, dict):
            err("M0 CI workflow must be a YAML mapping")
    except Exception as exc:
        err(f"M0 CI workflow invalid: {exc}")
    for token in (
        "ubuntu-latest",
        "windows-latest",
        "uv lock --check",
        "uv sync --frozen --dev",
        "pnpm install --frozen-lockfile",
        "run_all_checks.py",
        "--profile m0",
        "--keep-going",
        "contents: read",
    ):
        if token not in ci_text:
            err(f"M0 CI workflow missing deterministic gate: {token}")
    for uses in re.findall(r"(?m)^\s*uses:\s*([^\s#]+)", ci_text):
        if re.fullmatch(r"[^@\s]+@[0-9a-f]{40}", uses) is None:
            err(f"M0 CI action must use an immutable commit SHA: {uses}")
    for forbidden_command in (
        "release_cursor_framework.py",
        "verify_cursor_framework_release.py",
        "package_cursor_framework.py",
        "framework-release",
        "framework-package",
        "FRAMEWORK_MANIFEST.json",
        "RELEASE_EVIDENCE.json",
    ):
        if forbidden_command in ci_text:
            err(f"ordinary M0 CI must not generate or verify release evidence: {forbidden_command}")

for required_tooling_asset in (
    ".node-version",
    ".importlinter",
    "package.json",
    "pnpm-lock.yaml",
    "pnpm-workspace.yaml",
    "tsconfig.base.json",
    "tsconfig.json",
    "eslint.config.mjs",
    "dependency-cruiser.config.mjs",
    "tests/architecture/python/test_dependency_boundaries.py",
    "tests/architecture/typescript/dependency-boundaries.test.mjs",
):
    if not (ROOT / required_tooling_asset).is_file():
        err(f"missing M0 tooling asset: {required_tooling_asset}")

# Cursor engineering automation is Skill-owned; do not reintroduce a generic root scripts/.
if (ROOT/'scripts').exists(): err('root scripts/ is forbidden; move Cursor engineering automation into the owning .cursor/skills/<skill>/scripts/')

# Every Python automation under .cursor/skills must belong to a Skill. Public entrypoints
# are referenced from the owning SKILL.md with a path relative to the Skill root.
for script in (CURSOR/'skills').rglob('scripts/*.py'):
    skill_root=script.parent.parent
    skill_md=skill_root/'SKILL.md'
    if not skill_md.is_file():
        err(f'orphan skill script without SKILL.md: {script.relative_to(ROOT)}')
        continue
    if not script.name.startswith('_'):
        rel_from_skill=script.relative_to(skill_root).as_posix()
        if rel_from_skill not in skill_md.read_text(encoding='utf-8'):
            err(f'skill entrypoint is not referenced with a Skill-relative path: {script.relative_to(ROOT)}')

# Parse Python automation sources without generating bytecode and enforce explicit UTF-8 text boundaries.
for script in [*(CURSOR/'hooks').glob('*.py'), *((CURSOR/'skills').rglob('scripts/*.py'))]:
    try:
        tree=ast.parse(script.read_text(encoding='utf-8'), filename=str(script))
    except SyntaxError as exc:
        err(f'python syntax error: {script.relative_to(ROOT)}:{exc.lineno}: {exc.msg}')
        continue
    for node in ast.walk(tree):
        if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Attribute):
            continue
        keyword_names={keyword.arg for keyword in node.keywords if keyword.arg is not None}
        if node.func.attr in {'read_text','write_text'}:
            positional_encoding=(node.func.attr=='read_text' and len(node.args)>=1) or (node.func.attr=='write_text' and len(node.args)>=2)
            if 'encoding' not in keyword_names and not positional_encoding:
                err(f'Python text I/O must declare encoding: {script.relative_to(ROOT)}:{node.lineno}')
        if node.func.attr=='run' and any(
            keyword.arg in {'text','universal_newlines'} and isinstance(keyword.value,ast.Constant) and keyword.value.value is True
            for keyword in node.keywords
        ) and 'encoding' not in keyword_names:
            err(f'text subprocess must declare encoding: {script.relative_to(ROOT)}:{node.lineno}')

# Keep Always Rules concise and non-duplicative with AGENTS.md.
repo_rule=(CURSOR/'rules/00-repository-contract.mdc').read_text(encoding='utf-8')
if '开始工作前先读根目录 `AGENTS.md`' in repo_rule:
    err('repository Rule must not force re-reading AGENTS.md when Cursor already applies it')
if '复杂任务还必须关联项目计划、复检和工程记忆' in repo_rule:
    err('repository Rule must not force Plan/Recheck/Memory for every complex task')
encoding_rule=(CURSOR/'rules/42-command-encoding.mdc').read_text(encoding='utf-8')
if '默认在 Windows PowerShell' in encoding_rule:
    err('command encoding Rule must not assume a single operating system/shell')

# Session-start context must not re-introduce instructions that the Always Rules intentionally scoped away.
session_context=(CURSOR/'hooks'/'session_context.py').read_text(encoding='utf-8')
if '复杂或高影响任务开始前读取 AGENTS.md' in session_context:
    err('sessionStart must not force redundant full AGENTS.md reload')

# Current official subagentStop payload does not expose subagent_id/parent_conversation_id as hook-specific fields.
subagent_stop=(CURSOR/'hooks'/'subagent_stop.py').read_text(encoding='utf-8')
if "event.get('subagent_id')" in subagent_stop or 'event.get("subagent_id")' in subagent_stop:
    err('subagentStop cleanup must not depend on undocumented subagent_id')
if "event.get('parent_conversation_id')" in subagent_stop or 'event.get("parent_conversation_id")' in subagent_stop:
    err('subagentStop cleanup must not depend on undocumented parent_conversation_id')
if 'allow()' in subagent_stop or 'import RUNTIME, allow' in subagent_stop:
    err('subagentStop must not emit permission fields; current schema only supports optional followup_message')

# External MCP calls are explicit-approval by project policy; hard secret material stays denied.
mcp_guard=(CURSOR/'hooks'/'mcp_guard.py').read_text(encoding='utf-8')
if 'from common import ask' not in mcp_guard or 'ask(' not in mcp_guard:
    err('beforeMCPExecution guard must require explicit approval for non-secret MCP calls')

# stop audit hook must speak Cursor JSON on stdout, never ad-hoc text.
snapshot=(CURSOR/'hooks'/'snapshot_commit.py').read_text(encoding='utf-8')
if 'emit({})' not in snapshot or 'print(' in snapshot:
    err('stop snapshot hook must emit valid JSON only and avoid ad-hoc stdout')


# Release/package/verifier share one source-file selector, and evidence content is validated
# rather than trusted only by digest.
release_helper=(CURSOR/'skills/framework-release/scripts/_release_files.py').read_text(encoding='utf-8')
for phrase in ('NON_RELEASE_DIRS', '".venv"', '"node_modules"', 'def source_files'):
    if phrase not in release_helper:
        err(f'release file selector missing hygiene invariant: {phrase}')
release_verify=(CURSOR/'skills/framework-release/scripts/verify_cursor_framework_release.py').read_text(encoding='utf-8')
for phrase in ('iter_releasable_files(ROOT)','release evidence contains non-zero command','release evidence command set/order mismatch'):
    if phrase not in release_verify:
        err(f'release verifier missing hardening invariant: {phrase}')
release_script=(CURSOR/'skills/framework-release/scripts/release_cursor_framework.py').read_text(encoding='utf-8')
if 'releasable_files(ROOT)' not in release_script:
    err('release generator must use the shared source-file selector')
package_script=(CURSOR/'skills/framework-release/scripts/package_cursor_framework.py').read_text(encoding='utf-8')
if 'archive_files(ROOT, output)' not in package_script:
    err('release packager must use the shared source-file selector')

runtime_ignore=CURSOR/'runtime/.gitignore'
if not runtime_ignore.exists() or '*' not in runtime_ignore.read_text(encoding='utf-8'): err('.cursor/runtime must contain local .gitignore')

# Windows CI checkouts default to core.autocrlf=true; without a pinned eol the formatter gate and
# release digests diverge per platform.
attributes=ROOT/'.gitattributes'
if not attributes.exists():
    err('repository must pin line endings via .gitattributes')
elif 'eol=lf' not in attributes.read_text(encoding='utf-8'):
    err('.gitattributes must pin eol=lf for deterministic cross-platform checkouts')

for w in warnings: print('WARNING:',w)
if errors:
    for e in errors: print('ERROR:',e)
    print(f'FAILED: {len(errors)} error(s), {len(warnings)} warning(s)'); raise SystemExit(1)
print(f'PASS: Cursor framework {version} validated; {len(warnings)} warning(s)')
