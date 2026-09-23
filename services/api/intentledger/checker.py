"""Repository-script-free TypeScript dependency checker.

It reads immutable Git objects only. It never checks out a revision, installs dependencies,
or evaluates repository configuration.
"""
from __future__ import annotations
import fnmatch, hashlib, json, posixpath, re, subprocess
from dataclasses import asdict, dataclass

@dataclass(frozen=True)
class Edge:
    source:str; specifier:str; target:str|None; line:int; kind:str; type_only:bool; status:str
@dataclass(frozen=True)
class Finding:
    revision:str; file:str; line:int; target:str; fingerprint:str; path:tuple[str,...]=(); disposition:str="present"
IMPORT=re.compile(r"(?P<type>import\s+type\s+)?(?:import[^'\"\n]*?from\s*|export[^'\"\n]*?from\s*|require\s*\(|import\s*\()\s*['\"](?P<target>[^'\"]+)['\"]")
NON_LITERAL=re.compile(r"(?:require|import)\s*\(\s*(?!['\"])")

def git(repo,*args):
    return subprocess.run(["git","-c","core.hooksPath=/dev/null","-C",repo,*args],check=True,text=True,capture_output=True,timeout=30).stdout.strip()
def resolve(repo,rev):
    sha=git(repo,"rev-parse","--verify",f"{rev}^{{commit}}")
    if not re.fullmatch(r"[0-9a-f]{40}",sha): raise ValueError("revision did not resolve to an immutable commit")
    return sha
def read(repo,sha,path):
    result=subprocess.run(["git","-c","core.hooksPath=/dev/null","-C",repo,"show",f"{sha}:{path}"],text=True,capture_output=True,timeout=15)
    return result.stdout if result.returncode==0 else None
def config(repo,sha):
    raw=read(repo,sha,"tsconfig.json")
    if not raw:return ".",{}
    try:
        clean=re.sub(r"/\*.*?\*/|//[^\n]*","",raw,flags=re.S); clean=re.sub(r",\s*([}\]])",r"\1",clean)
        options=json.loads(clean).get("compilerOptions",{}); return options.get("baseUrl","."),options.get("paths",{})
    except (TypeError,json.JSONDecodeError): return ".",{}
def candidates(spec,source,base,aliases):
    roots=[posixpath.normpath(posixpath.join(posixpath.dirname(source),spec))] if spec.startswith(".") else []
    if not roots:
        for pattern,replacements in aliases.items():
            match=re.match("^"+re.escape(pattern).replace(r"\*","(.+)")+"$",spec)
            if match:
                value=match.group(1) if match.groups() else ""; roots += [posixpath.join(base,x.replace("*",value)) for x in replacements]
    return [item for root in roots for item in (root.removeprefix("./"),root.removeprefix("./")+".ts",root.removeprefix("./")+".tsx",posixpath.join(root.removeprefix("./"),"index.ts"),posixpath.join(root.removeprefix("./"),"index.tsx"))]
def analyze(repo,revision):
    sha=resolve(repo,revision); files={x for x in git(repo,"ls-tree","-r","--name-only",sha).splitlines() if x.endswith((".ts",".tsx"))}; base,aliases=config(repo,sha); edges=[]; limits=[]
    for file in sorted(files):
        text=read(repo,sha,file)
        if text is None: limits.append(f"{file}: unavailable Git object"); continue
        for number,line in enumerate(text.splitlines(),1):
            if NON_LITERAL.search(line): limits.append(f"{file}:{number}: non-literal dynamic loading")
            for match in IMPORT.finditer(line):
                spec=match.group("target"); possible=candidates(spec,file,base,aliases); target=next((x for x in possible if x in files),None); external=not spec.startswith(".") and not possible; status="external" if external else "resolved" if target else "unresolved"
                if status=="unresolved":limits.append(f"{file}:{number}: unresolved import {spec}")
                token=match.group(0).lstrip(); kind="dynamic_import" if token.startswith("import(") else "require" if "require" in token else "export" if token.startswith("export") else "import"
                edges.append(Edge(file,spec,target,number,kind,bool(match.group("type")),status))
    return sha,edges,sorted(set(limits))
def matches(value,patterns):return any(value==x or fnmatch.fnmatch(value,x) for x in patterns)
def scan(repo,revision,rule):
    sha,edges,limits=analyze(repo,revision); include=rule.get("include_type_only",False); graph={}
    for edge in edges:
        if include or not edge.type_only:graph.setdefault(edge.source,[]).append(edge)
    forbidden=rule.get("forbidden_targets",[]) if rule["kind"]=="forbidden_import" else rule.get("protected_packages",[]); allowed=set(rule.get("allowed_adapter_paths",[])); transitive=rule.get("mode","direct")=="transitive"; findings=[]
    scoped=lambda p:matches(p,rule["scope"]) and not matches(p,rule.get("exceptions",[]))
    for source in sorted(x for x in graph if scoped(x)):
        queue=[(source,(source,))]; visited=set()
        while queue:
            current,path=queue.pop(0)
            if current in visited:continue
            visited.add(current)
            for edge in graph.get(current,[]):
                if (matches(edge.specifier,forbidden) or bool(edge.target and matches(edge.target,forbidden))) and not (rule["kind"]=="adapter_boundary" and current in allowed):
                    fingerprint=hashlib.sha256(f"{source}\0{edge.specifier}".encode()).hexdigest(); findings.append(Finding(sha,source,edge.line,edge.specifier,fingerprint,path+(edge.specifier,)))
                if transitive and edge.target and edge.target not in allowed:queue.append((edge.target,path+(edge.target,)))
    return sha,list({x.fingerprint:x for x in findings}.values()),limits
def renames(repo,base,head):
    certain={}; uncertain=[]
    for row in git(repo,"diff","--name-status","--find-renames=60%",base,head).splitlines():
        parts=row.split("\t")
        if parts and parts[0].startswith("R") and len(parts)==3:
            score=int(parts[0][1:] or 0)
            if score>=80:certain[parts[1]]=parts[2]
            else:uncertain.append(f"ambiguous rename {parts[1]} -> {parts[2]} ({score}%)")
    return certain,uncertain
def compare(repo,base,head,rule):
    b,bf,bl=scan(repo,base,rule); h,hf,hl=scan(repo,head,rule); rename,rl=renames(repo,b,h)
    key=lambda x,path:hashlib.sha256(f"{rename.get(x.file,x.file) if path else x.file}\0{x.target}".encode()).hexdigest(); bm={key(x,True):x for x in bf}; hm={key(x,False):x for x in hf}
    out=[{**asdict(v),"disposition":"existing" if k in bm else "introduced"} for k,v in hm.items()]+[{**asdict(v),"revision":h,"file":rename.get(v.file,v.file),"disposition":"resolved"} for k,v in bm.items() if k not in hm]; limitations=sorted(set(bl+hl+rl)); active=[x for x in out if x["disposition"] in ("introduced","existing")]
    return {"checker_version":"1.1.0","base_sha":b,"head_sha":h,"rule_hash":hashlib.sha256(json.dumps(rule,sort_keys=True,separators=(",",":")).encode()).hexdigest(),"execution":"unsupported" if limitations else "fail" if active else "pass","findings":out,"coverage":{"limitations":limitations,"type_only_included":bool(rule.get("include_type_only",False)),"mode":rule.get("mode","direct")}}
