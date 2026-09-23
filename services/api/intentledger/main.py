from __future__ import annotations
import os
from pathlib import Path
from fastapi import FastAPI,HTTPException,Query,Response
from fastapi.middleware.cors import CORSMiddleware
from .schemas import AnalysisRequest,IngestionRequest,RepositoryCreate,ReviewRequest
from .store import store
app=FastAPI(title="IntentLedger",version="1.1.0")
app.add_middleware(CORSMiddleware,allow_origins=[os.getenv("WEB_ORIGIN","http://127.0.0.1:3000")],allow_methods=["GET","POST"],allow_headers=["authorization","content-type"])
@app.middleware("http")
async def local_auth(request,call_next):
 token=os.getenv("LOCAL_API_TOKEN","")
 if token and request.url.path!="/api/v1/health" and request.headers.get("authorization")!=f"Bearer {token}":return Response(status_code=401,content='{"detail":"local access token required"}',media_type="application/json")
 return await call_next(request)
def allowed(raw):
 path=Path(raw).resolve(strict=True);roots=[Path(x).resolve() for x in os.getenv("ALLOWED_REPOSITORY_ROOTS",str(Path.cwd())).split(os.pathsep)]
 if not any(path==root or root in path.parents for root in roots):raise HTTPException(422,"repository outside allowed roots")
 return path
@app.get("/api/v1/health")
def health():return {"status":"ok","readiness":{"database":"ready","database_engine":os.getenv("INTENTLEDGER_STORAGE","sqlite")+"-offline","provider":os.getenv("PROVIDER","fixture"),"embeddings":"lexical-only" if not os.getenv("EMBEDDING_MODEL") else "configured"}}
@app.post("/api/v1/repositories",status_code=201)
def register(payload:RepositoryCreate):
 try:return store.register(allowed(payload.path),payload.display_name)
 except Exception as exc:raise HTTPException(422,str(exc)) from exc
@app.get("/api/v1/repositories")
def repositories(limit:int=Query(50,le=100),offset:int=Query(0,ge=0)):
 items=store.repositories();return {"items":items[offset:offset+limit],"total":len(items)}
@app.post("/api/v1/repositories/{repo_id}/ingestions")
def ingest(repo_id:str,payload:IngestionRequest):
 try:return store.ingest(repo_id,payload.revision,payload.rule)
 except KeyError as exc:raise HTTPException(404,str(exc)) from exc
@app.post("/api/v1/analyses",status_code=201)
def analyze(payload:AnalysisRequest):
 try:return store.create_analysis(payload.repository_id,payload.base,payload.head,payload.evidence_cutoff.isoformat(),payload.mode,payload.idempotency_key)
 except KeyError as exc:raise HTTPException(409,str(exc)) from exc
@app.get("/api/v1/analyses/{analysis_id}")
def analysis(analysis_id:str):
 value=store.analysis(analysis_id)
 if not value:raise HTTPException(404,"analysis not found")
 return value
@app.get("/api/v1/repositories/{repo_id}/analyses")
def analyses(repo_id:str):return {"items":store.analyses(repo_id)}
@app.get("/api/v1/repositories/{repo_id}/evidence")
def repository_evidence(repo_id:str):return {"items":store.evidence_for_repository(repo_id)}
@app.get("/api/v1/evidence/{evidence_id}")
def evidence(evidence_id:str):
 value=store.evidence(evidence_id)
 if not value:raise HTTPException(404,"evidence not found")
 return value
@app.post("/api/v1/reviews")
def review(payload:ReviewRequest):
 try:return store.review(payload.target_id,payload.version,payload.content_hash,payload.action,payload.reviewer,payload.rationale,payload.idempotency_key)
 except ValueError as exc:raise HTTPException(409,str(exc)) from exc
@app.post("/api/v1/analyses/{analysis_id}/resume")
def resume(analysis_id:str):
 try:return store.execute(analysis_id)
 except KeyError as exc:raise HTTPException(404,str(exc)) from exc
 except PermissionError as exc:raise HTTPException(409,str(exc)) from exc
@app.get("/api/v1/analyses/{analysis_id}/export")
def export(analysis_id:str,format:str="json"):
 value=analysis(analysis_id)
 if format=="json":return value
 if format=="markdown":return Response(f"# IntentLedger analysis\n\n- Base: `{value['base_sha']}`\n- Head: `{value['head_sha']}`\n- Status: **{value['status']}**\n- Findings: {len(value['findings'])}\n",media_type="text/markdown")
 raise HTTPException(422,"format must be json or markdown")
