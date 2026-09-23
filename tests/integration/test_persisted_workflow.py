import json,os,subprocess
from pathlib import Path
from intentledger.store import DatabaseStore

def commit(repo,message,stamp):
 env={**os.environ,"GIT_AUTHOR_NAME":"fixture","GIT_AUTHOR_EMAIL":"fixture@example.invalid","GIT_COMMITTER_NAME":"fixture","GIT_COMMITTER_EMAIL":"fixture@example.invalid","GIT_AUTHOR_DATE":stamp,"GIT_COMMITTER_DATE":stamp};subprocess.run(["git","-C",repo,"add","."],check=True,env=env);subprocess.run(["git","-C",repo,"commit","-m",message],check=True,env=env,capture_output=True);return subprocess.check_output(["git","-C",repo,"rev-parse","HEAD"],text=True).strip()
def test_persisted_ingest_approve_execute_restart(tmp_path):
 repo=tmp_path/"repo";repo.mkdir();subprocess.run(["git","-C",repo,"init","-b","main"],check=True,capture_output=True);(repo/"docs").mkdir();(repo/"src/services").mkdir(parents=True);(repo/"docs/adr.md").write_text("# Adapter\nStatus: Accepted\nServices use adapter.\n");(repo/"src/services/a.ts").write_text("export const ok=1\n");base=commit(repo,"base","2024-01-01T00:00:00Z");(repo/"src/services/a.ts").write_text("import sdk from 'payment-sdk';\nexport const bad=sdk;\n");head=commit(repo,"head","2024-02-01T00:00:00Z")
 database=tmp_path/"ledger.db";store=DatabaseStore(database);registered=store.register(repo);rule={"schema_version":1,"decision_version_id":"fixture","kind":"adapter_boundary","scope":["src/services/**"],"protected_packages":["payment-sdk"],"allowed_adapter_paths":["src/adapters/payment.ts"],"exceptions":[],"mode":"direct","include_type_only":False};first=store.ingest(registered["id"],head,rule);second=store.ingest(registered["id"],head,rule);assert first["snapshots_added"]==1 and second["snapshots_added"]==0
 analysis=store.create_analysis(registered["id"],base,head,"2024-03-01T00:00:00+00:00","strict_replay","analysis-1");assert analysis["status"]=="awaiting_review"
 try:store.execute(analysis["id"]);assert False,"execution without approval"
 except PermissionError:pass
 store.review(analysis["rule_id"],analysis["rule_version"],analysis["rule_hash"],"approve","maintainer","ADR matches rule","review-1");completed=store.execute(analysis["id"]);assert completed["status"]=="completed";assert completed["outputs"]["execution"]=="fail";assert completed["findings"][0]["disposition"]=="introduced"
 restarted=DatabaseStore(database);persisted=restarted.analysis(analysis["id"]);assert persisted["status"]=="completed";assert persisted["findings"]==completed["findings"]
