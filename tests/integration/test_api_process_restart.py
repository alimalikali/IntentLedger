import importlib.util,json,os,socket,subprocess,sys,time,urllib.request
from pathlib import Path
import pytest
from intentledger.store import DatabaseStore

pytestmark=pytest.mark.skipif(importlib.util.find_spec("fastapi") is None or importlib.util.find_spec("uvicorn") is None,reason="FastAPI/uvicorn not installed")
def free_port():
 with socket.socket() as value:value.bind(("127.0.0.1",0));return value.getsockname()[1]
def get(url):
 with urllib.request.urlopen(url,timeout=2) as response:return json.loads(response.read())
def start(database,port):
 env={**os.environ,"PYTHONPATH":"services/api","INTENTLEDGER_STORAGE":"sqlite","INTENTLEDGER_DB_PATH":str(database),"LOCAL_API_TOKEN":""};process=subprocess.Popen([sys.executable,"-m","uvicorn","intentledger.main:app","--host","127.0.0.1","--port",str(port)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(50):
  try:get(f"http://127.0.0.1:{port}/api/v1/health");return process
  except Exception:time.sleep(.1)
 process.terminate();raise AssertionError("API did not start")
def test_completed_analysis_survives_real_api_process_restart(tmp_path):
 database=tmp_path/"restart.db";store=DatabaseStore(database);store.db.execute("INSERT INTO repositories VALUES(?,?,?,?,?)",("repo","fixture",str(tmp_path),"main","complete"));store.db.execute("INSERT INTO rule_versions VALUES(?,?,?,?,?,?)",("rule","repo",1,"a"*64,"{}","approved"));store.db.execute("INSERT INTO analyses VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",("analysis","repo","b"*40,"c"*40,"2024-01-01T00:00:00Z","strict_replay","completed","rule",1,"a"*64,json.dumps({"execution":"pass","findings":[]}),"restart"));store.db.commit()
 port=free_port();first=start(database,port)
 try:assert get(f"http://127.0.0.1:{port}/api/v1/analyses/analysis")["status"]=="completed"
 finally:first.terminate();first.wait(timeout=5)
 second=start(database,port)
 try:assert get(f"http://127.0.0.1:{port}/api/v1/analyses/analysis")["outputs"]["execution"]=="pass"
 finally:second.terminate();second.wait(timeout=5)
