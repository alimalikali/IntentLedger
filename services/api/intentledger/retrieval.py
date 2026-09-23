from __future__ import annotations
from collections import defaultdict
def lexical(query,docs,k=10):
    terms=set(query.lower().split()); return sorted(docs,key=lambda d:(-len(terms & set(d["text"].lower().split())),d["id"]))[:k]
def latest_eligible(query,docs,k=10): return sorted(docs,key=lambda d:(d.get("available_at") or ""),reverse=True)[:k]
def rrf(rankings,k=60):
    scores=defaultdict(float); docs={}
    for ranking in rankings:
        for rank,d in enumerate(ranking,1): scores[d["id"]]+=1/(k+rank); docs[d["id"]]=d
    return [docs[i] for i in sorted(scores,key=lambda x:(-scores[x],x))]
def eligible(docs,cutoff,strict=True): return [d for d in docs if not strict or (d.get("available_at") and d["available_at"]<=cutoff)]
def temporal_evidence_aware(query,docs,cutoff,k=10):
    corpus=eligible(docs,cutoff); first=lexical(query,corpus,k); related={x for d in first for x in d.get("relations",[])}; expanded=first+[d for d in corpus if d["id"] in related and d not in first]; return expanded[:k]
