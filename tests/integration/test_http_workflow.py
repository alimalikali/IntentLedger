import os,subprocess
from pathlib import Path
import pytest
pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
import intentledger.main as main
from intentledger.store import DatabaseStore

def commit(repo,message,stamp):
 env={**os.environ,"GIT_AUTHOR_NAME":"fixture","GIT_AUTHOR_EMAIL":"fixture@example.invalid","GIT_COMMITTER_NAME":"fixture","GIT_COMMITTER_EMAIL":"fixture@example.invalid","GIT_AUTHOR_DATE":stamp,"GIT_COMMITTER_DATE":stamp};subprocess.run(["git","-C",repo,"add","."],check=True,env=env);subprocess.run(["git","-C",repo,"commit","-m",message],check=True,env=env,capture_output=True);return subprocess.check_output(["git","-C",repo,"rev-parse","HEAD"],text=True).strip()
def test_complete_http_workflow_and_api_restart(tmp_path,monkeypatch):
 repo=tmp_path/"repo";repo.mkdir();subprocess.run(["git","-C",repo,"init","-b","main"],check=True,capture_output=True);(repo/"docs").mkdir();(repo/"src/services").mkdir(parents=True);(repo/"docs/adr.md").write_text("# Adapter boundary\nStatus: Accepted\nUse the payment adapter.\n");(repo/"src/services/pay.ts").write_text("export const pay=1\n");base=commit(repo,"base","2024-01-01T00:00:00Z");(repo/"src/services/pay.ts").write_text("import sdk from 'payment-sdk';\nexport const pay=sdk.pay;\n");head=commit(repo,"head","2024-02-01T00:00:00Z")
 database=tmp_path/"http.db";main.store=DatabaseStore(database);monkeypatch.setenv("ALLOWED_REPOSITORY_ROOTS",str(tmp_path));client=TestClient(main.app)
 registered=client.post("/api/v1/repositories",json={"path":str(repo),"display_name":"HTTP fixture"});assert registered.status_code==201;repository=registered.json()
 rule={"schema_version":1,"decision_version_id":"fixture","kind":"adapter_boundary","scope":["src/services/**"],"protected_packages":["payment-sdk"],"allowed_adapter_paths":["src/adapters/payment.ts"],"exceptions":[],"mode":"direct","include_type_only":False}
 ingested=client.post(f"/api/v1/repositories/{repository['id']}/ingestions",json={"revision":head,"rule":rule});assert ingested.status_code==200 and ingested.json()["snapshots_added"]==1
 created=client.post("/api/v1/analyses",json={"repository_id":repository["id"],"base":base,"head":head,"evidence_cutoff":"2024-03-01T00:00:00Z","mode":"strict_replay","idempotency_key":"http-analysis"});assert created.status_code==201;analysis=created.json()
 assert client.post(f"/api/v1/analyses/{analysis['id']}/resume").status_code==409
 stale=client.post("/api/v1/reviews",json={"target_id":analysis["rule_id"],"version":analysis["rule_version"],"content_hash":"0"*64,"action":"approve","reviewer":"http-test","rationale":"stale","idempotency_key":"stale"});assert stale.status_code==409
 approved=client.post("/api/v1/reviews",json={"target_id":analysis["rule_id"],"version":analysis["rule_version"],"content_hash":analysis["rule_hash"],"action":"approve","reviewer":"http-test","rationale":"exact ADR rule","idempotency_key":"exact"});assert approved.status_code==200
 executed=client.post(f"/api/v1/analyses/{analysis['id']}/resume");assert executed.status_code==200;assert executed.json()["findings"][0]["disposition"]=="introduced"
 evidence=client.get(f"/api/v1/repositories/{repository['id']}/evidence");assert evidence.status_code==200;assert "Use the payment adapter" in evidence.json()["items"][0]["text"]
 main.store=DatabaseStore(database);restarted=TestClient(main.app);persisted=restarted.get(f"/api/v1/analyses/{analysis['id']}");assert persisted.status_code==200 and persisted.json()["findings"]==executed.json()["findings"]
 exported=restarted.get(f"/api/v1/analyses/{analysis['id']}/export?format=markdown");assert exported.status_code==200;assert "Findings: 1" in exported.text
