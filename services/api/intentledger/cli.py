import argparse,json,os,subprocess,sys
from pathlib import Path
from .checker import compare,resolve

def allowed(path):
    p=Path(path).resolve(); roots=[Path(x).resolve() for x in os.getenv("ALLOWED_REPOSITORY_ROOTS",str(Path.cwd())).split(os.pathsep)]
    if not any(p==r or r in p.parents for r in roots): raise SystemExit("repository is outside ALLOWED_REPOSITORY_ROOTS")
    return p
def main():
    p=argparse.ArgumentParser(prog="intentledger"); sub=p.add_subparsers(dest="cmd",required=True)
    for name in ("register","ingest","analyze","check","export","evaluate"):
        x=sub.add_parser(name); x.add_argument("--repo",default="."); x.add_argument("--json",action="store_true"); x.add_argument("--base",default="HEAD~1"); x.add_argument("--head",default="HEAD"); x.add_argument("--rule",default="fixtures/demo/rule.json")
    demo=sub.add_parser("demo"); demo.add_argument("action",choices=["seed"]); demo.add_argument("--path",default=".intentledger/demo")
    a=p.parse_args()
    if a.cmd=="demo": subprocess.run([sys.executable,"fixtures/demo/generate.py",a.path],check=True); return
    repo=allowed(a.repo)
    if a.cmd=="register": result={"path":str(repo),"default_branch":subprocess.run(["git","-C",repo,"branch","--show-current"],text=True,capture_output=True,check=True).stdout.strip(),"status":"registered"}
    elif a.cmd=="ingest": result={"repository":str(repo),"head":resolve(repo,a.head),"status":"ingested","idempotent":True}
    elif a.cmd in ("analyze","check"):
        rule=json.loads(Path(a.rule).read_text()); result=compare(repo,a.base,a.head,rule)
    elif a.cmd=="evaluate": subprocess.run([sys.executable,"evals/run.py","--output","evals/reports"],check=True); return
    else: result={"status":"export requires API analysis id"}
    print(json.dumps(result,indent=2,default=str) if a.json else "\n".join(f"{k}: {v}" for k,v in result.items()))
    if a.cmd=="check": raise SystemExit(2 if result["execution"] in ("unsupported","error") else 1 if result["execution"]=="fail" else 0)
if __name__=="__main__":main()
