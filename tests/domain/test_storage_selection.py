import os,subprocess,sys

def test_postgresql_selection_fails_closed_without_sqlite_fallback(tmp_path):
 env={**os.environ,"PYTHONPATH":"services/api","INTENTLEDGER_STORAGE":"postgresql","INTENTLEDGER_DB_PATH":str(tmp_path/"must-not-exist.db")};result=subprocess.run([sys.executable,"-c","import intentledger.store"],env=env,text=True,capture_output=True);assert result.returncode!=0;assert "refusing to fall back to SQLite" in result.stderr;assert not (tmp_path/"must-not-exist.db").exists()
