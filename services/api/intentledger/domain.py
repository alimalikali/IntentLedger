from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from fnmatch import fnmatch
from hashlib import sha256
import json

class Applicability(StrEnum):
    SUPPORTED="supported"; CONFLICTED="conflicted"; INSUFFICIENT="insufficient_evidence"; NOT_APPLICABLE="not_applicable"
class Execution(StrEnum):
    PASS="pass"; FAIL="fail"; UNSUPPORTED="unsupported"; ERROR="error"
@dataclass(frozen=True)
class Decision:
    id: str; status: str; anchor: str|None; scope: tuple[str,...]; exceptions: tuple[str,...]=()
@dataclass(frozen=True)
class Relation:
    source: str; target: str; kind: str; scope: tuple[str,...]; confirmed: bool=True

def path_in_scope(path: str, scope: tuple[str,...], exceptions: tuple[str,...]=()) -> bool:
    return any(fnmatch(path,p) for p in scope) and not any(fnmatch(path,p) for p in exceptions)

def evidence_eligible(availability: datetime|None, cutoff: datetime, mode="strict_replay") -> bool:
    return availability is not None and availability <= cutoff if mode == "strict_replay" else True

def validate_relation_graph(relations: list[Relation]) -> None:
    graph: dict[str,list[str]]={}
    for r in relations:
        if r.kind == "supersedes" and r.confirmed: graph.setdefault(r.source,[]).append(r.target)
    def visit(n, active, done):
        if n in active: raise ValueError("supersession cycle")
        if n in done: return
        active.add(n)
        for child in graph.get(n,[]): visit(child,active,done)
        active.remove(n); done.add(n)
    done=set()
    for n in graph: visit(n,set(),done)

def applicable(decisions: list[Decision], relations: list[Relation], path: str, is_ancestor) -> tuple[Applicability,list[str]]:
    accepted=[d for d in decisions if d.status=="accepted" and d.anchor and is_ancestor(d.anchor) and path_in_scope(path,d.scope,d.exceptions)]
    if any(d.anchor is None for d in decisions if d.status=="accepted" and path_in_scope(path,d.scope,d.exceptions)):
        return Applicability.INSUFFICIENT, []
    suppressed=set()
    contradictions=set()
    by_id={d.id:d for d in accepted}
    for r in relations:
        if not r.confirmed or not path_in_scope(path,r.scope): continue
        if r.source in by_id and r.target in by_id:
            if r.kind=="supersedes": suppressed.add(r.target)
            if r.kind=="contradicts": contradictions.update((r.source,r.target))
    active=[d.id for d in accepted if d.id not in suppressed]
    if contradictions.intersection(active): return Applicability.CONFLICTED,active
    return (Applicability.SUPPORTED if active else Applicability.NOT_APPLICABLE),active

def rule_hash(parameters: dict) -> str:
    return sha256(json.dumps(parameters,sort_keys=True,separators=(",",":")).encode()).hexdigest()
