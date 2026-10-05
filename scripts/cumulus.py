#!/usr/bin/env python3
"""Cumulus v0.2.1 — project-aware memory and capability optimization for coding agents."""
from __future__ import annotations

import argparse, json, os, re, subprocess, sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

VERSION = "0.2.1"
STATE = ".cumulus"
FAILURES = {"task_failed", "test_failure", "build_failure", "tool_failure"}
DEFAULTS = {
    "schema_version": 2,
    "auto_level": 1,
    "thresholds": {"same_domain_failures": 3, "manual_interventions": 2, "user_corrections": 2, "high_severity_failures": 1, "high_effort_tasks": 3},
    "protected_actions": ["credentials", "paid_services", "system_changes", "security_sensitive", "destructive_actions"],
}


def now(): return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def root():
    try:
        p = subprocess.run(["git", "rev-parse", "--show-toplevel"], check=True, capture_output=True, text=True).stdout.strip()
        if p: return Path(p).resolve()
    except Exception: pass
    return Path.cwd().resolve()

def paths(r):
    b = r / STATE
    return {k: b / v for k, v in {
        "base":"", "config":"config.json", "project":"project.json", "capabilities":"capabilities.json",
        "events":"events.jsonl", "patterns":"patterns.json", "improvements":"improvements.jsonl",
        "decisions":"decisions.jsonl", "skills":"skills.lock.json", "active":"active-task.json",
        "memory":"memory/summary.md", "reviews":"reviews", "scout":"scout"
    }.items()}

def rjson(p, default):
    try: return json.loads(p.read_text())
    except Exception: return default

def wjson(p, data): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(data, indent=2, ensure_ascii=False)+"\n")

def rows(p):
    if not p.exists(): return []
    out=[]
    for line in p.read_text(errors="ignore").splitlines():
        try:
            v=json.loads(line)
            if isinstance(v,dict): out.append(v)
        except Exception: pass
    return out

def append(p, rec): p.parent.mkdir(parents=True, exist_ok=True); p.open("a").write(json.dumps(rec, ensure_ascii=False)+"\n")

def ensure(r):
    p=paths(r)
    if not p["config"].exists():
        print("Cumulus is not initialized. Run ./cumulus init", file=sys.stderr); raise SystemExit(2)
    return p

def text(path, limit=120000):
    try: return path.read_text(errors="ignore")[:limit]
    except Exception: return ""

def profile(r):
    dep="\n".join(text(r/x).lower() for x in ["pyproject.toml","requirements.txt","package.json","go.mod","Cargo.toml"] if (r/x).exists())
    langs=[]
    for lang, marks in {"python":["pyproject.toml","requirements.txt"],"javascript/typescript":["package.json"],"go":["go.mod"],"rust":["Cargo.toml"],"java":["pom.xml","build.gradle"]}.items():
        if any((r/x).exists() for x in marks): langs.append(lang)
    frameworks=[]
    for name, needles in {"fastapi":["fastapi"],"django":["django"],"flask":["flask"],"react":["\"react\""],"nextjs":["\"next\""],"vue":["\"vue\""],"nestjs":["@nestjs/"],"langgraph":["langgraph"],"langchain":["langchain"],"remotion":["remotion"]}.items():
        if any(n in dep for n in needles): frameworks.append(name)
    db=[]
    for name, needles in {"postgresql":["postgres","psycopg","asyncpg"],"mysql":["mysql"],"sqlite":["sqlite"],"mongodb":["mongodb","pymongo","mongoose"],"redis":["redis"]}.items():
        if any(n in dep for n in needles): db.append(name)
    testing=[x for x in ["pytest","vitest","jest","playwright","cypress"] if x in dep]
    infra=[]
    if any((r/x).exists() for x in ["Dockerfile","compose.yml","docker-compose.yml"]): infra.append("docker")
    if (r/".github/workflows").exists(): infra.append("github-actions")
    pm=None
    for name, mark in [("uv","uv.lock"),("poetry","poetry.lock"),("pnpm","pnpm-lock.yaml"),("yarn","yarn.lock"),("npm","package-lock.json")]:
        if (r/mark).exists(): pm=name; break
    return {"languages":langs,"frameworks":frameworks,"databases":db,"testing":testing,"infrastructure":infra,"package_manager":pm}

def add_event(p, typ, domain="general", severity="low", task_id=None, message="", metadata=None):
    rec={"time":now(),"type":typ,"domain":domain or "general","severity":severity,"message":message}
    if task_id: rec["task_id"]=task_id
    if metadata: rec["metadata"]=metadata
    append(p["events"], rec)
    return rec

def known_domains(events): return sorted({e.get("domain") for e in events if e.get("domain") and e.get("domain")!="general"})

def update_caps(p):
    ev=rows(p["events"]); stats=defaultdict(lambda:{"successes":0,"failures":0,"manual_interventions":0,"user_corrections":0,"high_effort_tasks":0})
    for e in ev:
        d=e.get("domain","general"); s=stats[d]; t=e.get("type")
        if t=="task_completed": s["successes"]+=1
        if t in FAILURES: s["failures"]+=1
        if t=="manual_intervention": s["manual_interventions"]+=1
        if t=="user_correction": s["user_corrections"]+=1
        if t=="task_completed" and (e.get("metadata") or {}).get("effort")=="high": s["high_effort_tasks"]+=1
    data={"schema_version":2,"updated_at":now(),"domains":{}}
    for d,s in stats.items():
        total=s["successes"]+s["failures"]
        conf="unknown" if total<2 else ("high" if s["failures"]==0 and s["successes"]>=3 else "medium" if s["successes"]>=s["failures"] else "low")
        data["domains"][d]={**s,"confidence":conf}
    wjson(p["capabilities"],data)

def analyze(r, persist=True):
    p=ensure(r); cfg=rjson(p["config"],DEFAULTS); ev=rows(p["events"])
    cut={}
    for e in ev:
        if e.get("type")=="improvement_kept": cut[e.get("domain","general")]=e.get("time","")
    grouped=defaultdict(list)
    for e in ev:
        d=e.get("domain","general")
        if cut.get(d) and e.get("time","")<=cut[d]: continue
        grouped[d].append(e)
    th=cfg.get("thresholds",DEFAULTS["thresholds"]); patterns=[]
    for d, es in grouped.items():
        c=Counter(e.get("type") for e in es)
        failures=sum(c[x] for x in FAILURES); high=sum(1 for e in es if e.get("severity")=="high" and e.get("type") in FAILURES)
        high_eff=sum(1 for e in es if e.get("type")=="task_completed" and (e.get("metadata") or {}).get("effort")=="high")
        reasons=[]
        if failures>=th["same_domain_failures"]: reasons.append(f"{failures} failures")
        if c["manual_intervention"]>=th["manual_interventions"]: reasons.append(f"{c['manual_intervention']} manual interventions")
        if c["user_correction"]>=th["user_corrections"]: reasons.append(f"{c['user_correction']} user corrections")
        if high>=th["high_severity_failures"]: reasons.append(f"{high} high-severity failures")
        if high_eff>=th["high_effort_tasks"]: reasons.append(f"{high_eff} high-effort tasks")
        if reasons: patterns.append({"domain":d,"reasons":reasons,"evidence_count":len(es),"detected_at":now()})
    if persist:
        wjson(p["patterns"],{"updated_at":now(),"patterns":patterns})
        existing=rows(p["improvements"])
        open_domains={x.get("domain") for x in existing if x.get("status") in {"queued","trial"}}
        if cfg.get("auto_level",1)>=1:
            for pat in patterns:
                if pat["domain"] not in open_domains:
                    append(p["improvements"],{"id":f"imp-{len(existing)+1:04d}","created_at":now(),"domain":pat["domain"],"status":"queued","reason":"; ".join(pat["reasons"]),"candidate":None})
                    existing.append({})
    return patterns

def integrate(r, target="AGENTS.md"):
    p=r/target; old=text(p,2_000_000) if p.exists() else ""
    start="<!-- cumulus:start -->"; end="<!-- cumulus:end -->"
    block=f'''{start}\n## Cumulus\n\nThis repository uses `.cumulus/` as project memory and capability evidence.\n\nFor substantial tasks:\n1. Read `.cumulus/project.json` and relevant memory.\n2. Start with `./cumulus task-start --task-id <id> --domain <domain> --goal "<goal>"`.\n3. If a specialized new domain appears, run `./cumulus scout-plan --domain <domain>` before inventing a custom skill.\n4. Finish with `./cumulus task-end ...` and record only meaningful retries, manual intervention, or user corrections.\n5. Respect `.cumulus/config.json` auto level before applying capability changes.\n6. Use `./cumulus review` when the user asks to improve the agent.\n\nKeep bookkeeping lightweight.\n{end}'''
    pat=re.compile(re.escape(start)+r".*?"+re.escape(end),re.S)
    new=pat.sub(block,old) if pat.search(old) else (old.rstrip()+"\n\n"+block+"\n").lstrip()
    p.write_text(new)

def cmd_init(a):
    r=root(); p=paths(r); p["base"].mkdir(parents=True,exist_ok=True)
    cfg=dict(DEFAULTS); cfg["auto_level"]=a.auto_level if a.auto_level is not None else 1; wjson(p["config"],cfg)
    prof=profile(r); goal=a.goal or ""
    project={"schema_version":2,"created_at":now(),"updated_at":now(),"goal":goal,"profile":prof,"known_domains":sorted(set(prof["frameworks"]+prof["databases"]+prof["testing"]+prof["infrastructure"]))}
    wjson(p["project"],project); wjson(p["capabilities"],{"schema_version":2,"updated_at":now(),"domains":{}}); wjson(p["skills"],{"schema_version":1,"skills":[]})
    if not p["events"].exists(): p["events"].touch()
    add_event(p,"project_initialized",message=f"Cumulus {VERSION} initialized")
    if not a.no_integrate: integrate(r,a.integration_target)
    cmd_scout(argparse.Namespace(domain=project["known_domains"] or None, quiet=True))
    print(f"Cumulus {VERSION} initialized in {r}")
    print(f"Auto level: {cfg['auto_level']} | Goal: {goal or '(unspecified)'}")

def cmd_profile(a):
    r=root(); p=ensure(r); pr=rjson(p["project"],{}); pr["profile"]=profile(r); pr["updated_at"]=now(); wjson(p["project"],pr); print(json.dumps(pr["profile"],indent=2))

def cmd_set_auto(a):
    p=ensure(root()); cfg=rjson(p["config"],DEFAULTS); cfg["auto_level"]=a.level; wjson(p["config"],cfg); print(f"Auto level set to {a.level}")

def cmd_log(a):
    p=ensure(root()); meta=json.loads(a.metadata) if a.metadata else None; add_event(p,a.type,a.domain,a.severity,a.task_id,a.message,meta); update_caps(p); analyze(root()); print("Logged.")

def cmd_task_start(a):
    p=ensure(root())
    if p["active"].exists() and not a.force: print("An active task already exists; use --force.",file=sys.stderr); raise SystemExit(2)
    task={"task_id":a.task_id,"domain":a.domain,"goal":a.goal,"started_at":now()}; wjson(p["active"],task); add_event(p,"task_started",a.domain,"low",a.task_id,a.goal)
    pr=rjson(p["project"],{}); ds=set(pr.get("known_domains",[]))
    if a.domain not in ds: ds.add(a.domain); pr["known_domains"]=sorted(ds); pr["updated_at"]=now(); wjson(p["project"],pr); add_event(p,"new_domain",a.domain,"low",a.task_id,"New project domain detected")
    print(f"Started {a.task_id} ({a.domain})")

def cmd_task_end(a):
    p=ensure(root()); active=rjson(p["active"],{})
    tid=a.task_id or active.get("task_id"); domain=a.domain or active.get("domain") or "general"
    if not tid: print("No active task and no --task-id provided",file=sys.stderr); raise SystemExit(2)
    if a.result=="success": add_event(p,"task_completed",domain,"low",tid,a.message or "Task completed",{"effort":a.effort,"retries":a.retries})
    else: add_event(p,"task_failed",domain,a.severity,tid,a.message or "Task failed",{"effort":a.effort,"retries":a.retries})
    for _ in range(max(0,a.retries)): add_event(p,"retry",domain,"low",tid,"Task retry")
    if a.manual: add_event(p,"manual_intervention",domain,"medium",tid,a.manual)
    if a.user_correction: add_event(p,"user_correction",domain,"medium",tid,a.user_correction)
    try: p["active"].unlink()
    except FileNotFoundError: pass
    update_caps(p); pats=analyze(root()); print(f"Finished {tid}; capability-debt patterns: {len(pats)}")

def cmd_analyze(a):
    pats=analyze(root())
    if not pats: print("No capability-debt pattern detected."); return
    for x in pats: print(f"{x['domain']}: " + "; ".join(x["reasons"]))

def cmd_scout(a):
    r=root(); p=ensure(r); pr=rjson(p["project"],{}); domains=a.domain or pr.get("known_domains",[]) or ["general"]
    payload={"created_at":now(),"domains":domains,"instructions":"Search official/vendor skills first, then maintained public registries/repos, then MCP/CLI/tool workflows. Inspect actual instructions, dependencies, freshness, permissions, security, and fit. Classify install/adapt/learn/skip.","queries":[]}
    for d in domains:
        payload["queries"].append({"domain":d,"terms":[d,f"{d} agent skill",f"{d} best practices",f"{d} testing",f"{d} security"]})
    p["scout"].mkdir(parents=True,exist_ok=True); out=p["scout"]/("plan-"+datetime.now().strftime("%Y%m%d-%H%M%S")+".json"); wjson(out,payload)
    if not getattr(a,"quiet",False): print(json.dumps(payload,indent=2)); print(f"Saved: {out}")

def cmd_decide(a):
    p=ensure(root()); append(p["decisions"],{"time":now(),"type":a.type,"domain":a.domain,"decision":a.decision,"reason":a.reason,"scope":a.scope}); print("Decision recorded.")

def cmd_skill_add(a):
    p=ensure(root()); lock=rjson(p["skills"],{"schema_version":1,"skills":[]}); lock["skills"]=[x for x in lock.get("skills",[]) if x.get("name")!=a.name]; lock["skills"].append({"name":a.name,"source":a.source,"version":a.version,"ref":a.ref,"status":a.status,"domains":a.domain or [],"added_at":now()}); wjson(p["skills"],lock); print(f"Locked skill: {a.name}")

def cmd_skill_list(a):
    p=ensure(root()); lock=rjson(p["skills"],{"skills":[]})
    for s in lock.get("skills",[]): print(f"{s.get('name')}  {s.get('status')}  {s.get('source')}  {s.get('ref') or s.get('version') or ''}")

def cmd_improvements(a):
    p=ensure(root()); items=rows(p["improvements"]); shown=[x for x in items if a.all or x.get("status") in {"queued","trial"}]
    for x in shown: print(f"{x.get('id')}: {x.get('domain')} [{x.get('status')}] {x.get('reason','')}")

def rewrite_jsonl(path, items): path.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in items))

def cmd_trial_start(a):
    p=ensure(root()); items=rows(p["improvements"]); found=False
    for x in items:
        if x.get("id")==a.improvement_id: x.update({"status":"trial","candidate":a.candidate,"trial_started_at":now(),"before":json.loads(a.before) if a.before else {}}); found=True
    if not found: print("Improvement not found",file=sys.stderr); raise SystemExit(2)
    rewrite_jsonl(p["improvements"],items); print("Trial started.")

def cmd_trial_finish(a):
    p=ensure(root()); items=rows(p["improvements"]); found=None
    for x in items:
        if x.get("id")==a.improvement_id: x.update({"status":"kept" if a.outcome=="keep" else "rolled_back","trial_finished_at":now(),"after":json.loads(a.after) if a.after else {},"reason_final":a.reason}); found=x
    if not found: print("Improvement not found",file=sys.stderr); raise SystemExit(2)
    rewrite_jsonl(p["improvements"],items); add_event(p,"improvement_kept" if a.outcome=="keep" else "improvement_rolled_back",found.get("domain","general"),"low",message=a.reason,metadata={"candidate":found.get("candidate")}); analyze(root()); print(f"Trial {a.outcome}.")

def cmd_compact(a):
    p=ensure(root()); pr=rjson(p["project"],{}); caps=rjson(p["capabilities"],{}); pats=analyze(root(),persist=False)
    lines=["# Cumulus Project Memory","",f"Updated: {now()}","",f"Goal: {pr.get('goal') or '(unspecified)'}","", "## Known domains", *[f"- {d}" for d in pr.get("known_domains",[])], "", "## Capability debt", *([f"- {x['domain']}: {'; '.join(x['reasons'])}" for x in pats] or ["- none"]), "", "## Capability evidence"]
    for d,v in (caps.get("domains") or {}).items(): lines.append(f"- {d}: confidence={v.get('confidence')} successes={v.get('successes')} failures={v.get('failures')}")
    p["memory"].parent.mkdir(parents=True,exist_ok=True); p["memory"].write_text("\n".join(lines)+"\n"); print(f"Wrote {p['memory']}")

def cmd_status(a):
    p=ensure(root()); pr=rjson(p["project"],{}); cfg=rjson(p["config"],DEFAULTS); pats=analyze(root(),persist=False)
    print(f"Cumulus {VERSION}"); print(f"Goal: {pr.get('goal') or '(unspecified)'}"); print(f"Auto level: {cfg.get('auto_level')}"); print(f"Domains: {', '.join(pr.get('known_domains',[])) or '(none)'}"); print(f"Capability debt: {len(pats)}")

def cmd_review(a):
    r=root(); p=ensure(r); pr=rjson(p["project"],{}); caps=rjson(p["capabilities"],{}); pats=analyze(r,persist=False); items=[x for x in rows(p["improvements"]) if x.get("status") in {"queued","trial"}]
    lines=["# Cumulus Optimization Review","",f"Generated: {now()}","",f"Goal: {pr.get('goal') or '(unspecified)'}","", "## Capability debt"]
    lines += [f"- **{x['domain']}** — {'; '.join(x['reasons'])}" for x in pats] or ["- none detected"]
    lines += ["", "## Open improvements"] + ([f"- {x.get('id')}: {x.get('domain')} [{x.get('status')}]" for x in items] or ["- none"])
    lines += ["", "## Domain confidence"] + ([f"- {d}: {v.get('confidence')}" for d,v in (caps.get("domains") or {}).items()] or ["- no evidence yet"])
    out="\n".join(lines)+"\n"; p["reviews"].mkdir(parents=True,exist_ok=True); f=p["reviews"]/("review-"+datetime.now().strftime("%Y%m%d-%H%M%S")+".md"); f.write_text(out); print(out); print(f"Saved: {f}")

def cmd_integrate(a): integrate(root(),a.target); print(f"Updated {a.target}")

def cmd_doctor(a):
    p=ensure(root()); issues=[]
    if rjson(p["config"],{}).get("schema_version")!=2: issues.append("WARN: config schema mismatch")
    if not p["skills"].exists(): issues.append("WARN: skills.lock.json missing")
    if p["active"].exists(): issues.append("INFO: an active task is still open")
    pats=analyze(root(),persist=False)
    if pats: issues.append(f"INFO: {len(pats)} capability-debt pattern(s) need attention")
    print(f"Doctor: Cumulus {VERSION}"); print("\n".join(issues) if issues else "OK: state looks healthy.")

def parser():
    p=argparse.ArgumentParser(prog="cumulus",description=f"Cumulus {VERSION}"); p.add_argument("--version",action="version",version=VERSION); s=p.add_subparsers(dest="cmd",required=True)
    x=s.add_parser("init"); x.add_argument("--auto-level",type=int,choices=range(4)); x.add_argument("--goal"); x.add_argument("--non-interactive",action="store_true"); x.add_argument("--yes",action="store_true"); x.add_argument("--no-integrate",action="store_true"); x.add_argument("--integration-target",default="AGENTS.md"); x.add_argument("--force",action="store_true"); x.set_defaults(func=cmd_init)
    x=s.add_parser("profile"); x.set_defaults(func=cmd_profile)
    x=s.add_parser("set-auto"); x.add_argument("level",type=int,choices=range(4)); x.set_defaults(func=cmd_set_auto)
    x=s.add_parser("log"); x.add_argument("--type",required=True); x.add_argument("--domain",default="general"); x.add_argument("--severity",choices=["low","medium","high"],default="low"); x.add_argument("--task-id"); x.add_argument("--message",required=True); x.add_argument("--metadata"); x.set_defaults(func=cmd_log)
    x=s.add_parser("task-start"); x.add_argument("--task-id",required=True); x.add_argument("--domain",required=True); x.add_argument("--goal",required=True); x.add_argument("--force",action="store_true"); x.set_defaults(func=cmd_task_start)
    x=s.add_parser("task-end"); x.add_argument("--task-id"); x.add_argument("--domain"); x.add_argument("--result",choices=["success","failed"],required=True); x.add_argument("--severity",choices=["low","medium","high"],default="medium"); x.add_argument("--retries",type=int,default=0); x.add_argument("--effort",choices=["low","medium","high"],default="medium"); x.add_argument("--manual"); x.add_argument("--user-correction"); x.add_argument("--message"); x.set_defaults(func=cmd_task_end)
    x=s.add_parser("analyze"); x.set_defaults(func=cmd_analyze)
    x=s.add_parser("scout-plan"); x.add_argument("--domain",action="append"); x.set_defaults(func=cmd_scout)
    x=s.add_parser("decide"); x.add_argument("--type",choices=["architecture","convention","constraint","other"],required=True); x.add_argument("--domain",required=True); x.add_argument("--decision",required=True); x.add_argument("--reason",required=True); x.add_argument("--scope",choices=["project","domain","global"],default="project"); x.set_defaults(func=cmd_decide)
    x=s.add_parser("skill-add"); x.add_argument("--name",required=True); x.add_argument("--source",required=True); x.add_argument("--version"); x.add_argument("--ref"); x.add_argument("--status",choices=["candidate","trial","active","retired"],default="active"); x.add_argument("--domain",action="append"); x.set_defaults(func=cmd_skill_add)
    x=s.add_parser("skill-list"); x.set_defaults(func=cmd_skill_list)
    x=s.add_parser("improvements"); x.add_argument("--all",action="store_true"); x.set_defaults(func=cmd_improvements)
    x=s.add_parser("trial-start"); x.add_argument("improvement_id"); x.add_argument("--candidate",required=True); x.add_argument("--before"); x.set_defaults(func=cmd_trial_start)
    x=s.add_parser("trial-finish"); x.add_argument("improvement_id"); x.add_argument("--outcome",choices=["keep","rollback"],required=True); x.add_argument("--after"); x.add_argument("--reason",required=True); x.set_defaults(func=cmd_trial_finish)
    x=s.add_parser("compact"); x.add_argument("--archive",action="store_true"); x.set_defaults(func=cmd_compact)
    x=s.add_parser("status"); x.set_defaults(func=cmd_status)
    x=s.add_parser("review"); x.set_defaults(func=cmd_review)
    x=s.add_parser("integrate"); x.add_argument("--target",default="AGENTS.md"); x.set_defaults(func=cmd_integrate)
    x=s.add_parser("doctor"); x.set_defaults(func=cmd_doctor)
    return p

def main():
    a=parser().parse_args(); a.func(a)

if __name__=="__main__": main()
