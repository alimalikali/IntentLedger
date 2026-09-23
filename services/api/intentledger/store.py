"""Durable local workflow store.

The offline path uses SQLite so it can run without containers. PostgreSQL remains the
production-shaped deployment target owned by SQLAlchemy/Alembic; this store deliberately
uses the same immutable-version and exact-hash semantics for the local demo.
"""
from __future__ import annotations
import hashlib,json,os,sqlite3,subprocess,uuid
from datetime import datetime,timezone
from pathlib import Path
from .checker import compare,resolve

STORAGE_BACKEND=os.getenv("INTENTLEDGER_STORAGE","sqlite")
if STORAGE_BACKEND not in {"sqlite","postgresql"}:raise RuntimeError("INTENTLEDGER_STORAGE must be sqlite or postgresql")
if STORAGE_BACKEND=="postgresql":raise RuntimeError("PostgreSQL workflow adapter is not implemented; refusing to fall back to SQLite")
if os.getenv("DATABASE_URL","").startswith("postgresql") and "INTENTLEDGER_STORAGE" not in os.environ:raise RuntimeError("DATABASE_URL selects PostgreSQL; set INTENTLEDGER_STORAGE explicitly (no SQLite fallback)")

def now(): return datetime.now(timezone.utc).isoformat()
def row(value): return dict(value) if value else None
class DatabaseStore:
 def __init__(self,path=None):
  self.path=path or os.getenv("INTENTLEDGER_DB_PATH",".intentledger/intentledger.db"); Path(self.path).parent.mkdir(parents=True,exist_ok=True); self.db=sqlite3.connect(self.path,check_same_thread=False);self.db.row_factory=sqlite3.Row;self.migrate()
 def migrate(self):
  self.db.executescript("""
  PRAGMA foreign_keys=ON;
  CREATE TABLE IF NOT EXISTS repositories(id TEXT PRIMARY KEY,display_name TEXT NOT NULL,canonical_path TEXT NOT NULL UNIQUE,default_branch TEXT NOT NULL,ingestion_status TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS source_snapshots(id TEXT PRIMARY KEY,repository_id TEXT NOT NULL REFERENCES repositories(id),source_identity TEXT NOT NULL,source_version TEXT NOT NULL,content_hash TEXT NOT NULL,text TEXT NOT NULL,locator TEXT NOT NULL,available_at TEXT,UNIQUE(repository_id,source_identity,source_version,content_hash));
  CREATE TABLE IF NOT EXISTS rule_versions(id TEXT PRIMARY KEY,repository_id TEXT NOT NULL REFERENCES repositories(id),version INTEGER NOT NULL,content_hash TEXT NOT NULL,parameters TEXT NOT NULL,approval_state TEXT NOT NULL,UNIQUE(repository_id,version),UNIQUE(id,content_hash));
  CREATE TABLE IF NOT EXISTS analyses(id TEXT PRIMARY KEY,repository_id TEXT NOT NULL REFERENCES repositories(id),base_sha TEXT NOT NULL,head_sha TEXT NOT NULL,evidence_cutoff TEXT NOT NULL,mode TEXT NOT NULL,status TEXT NOT NULL,rule_id TEXT NOT NULL REFERENCES rule_versions(id),rule_version INTEGER NOT NULL,rule_hash TEXT NOT NULL,outputs TEXT NOT NULL,idempotency_key TEXT NOT NULL,UNIQUE(repository_id,idempotency_key));
  CREATE TABLE IF NOT EXISTS review_events(id TEXT PRIMARY KEY,repository_id TEXT NOT NULL REFERENCES repositories(id),target_id TEXT NOT NULL,target_version INTEGER NOT NULL,content_hash TEXT NOT NULL,action TEXT NOT NULL,reviewer TEXT NOT NULL,rationale TEXT NOT NULL,idempotency_key TEXT NOT NULL UNIQUE,created_at TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS findings(id TEXT PRIMARY KEY,analysis_id TEXT NOT NULL REFERENCES analyses(id),fingerprint TEXT NOT NULL,disposition TEXT NOT NULL,payload TEXT NOT NULL,UNIQUE(analysis_id,fingerprint,disposition));
  """);self.db.commit()
 def register(self,path,display_name=None):
  canonical=str(Path(path).resolve(strict=True)); subprocess.run(["git","-C",canonical,"rev-parse","--git-dir"],check=True,capture_output=True); branch=subprocess.run(["git","-C",canonical,"branch","--show-current"],check=True,text=True,capture_output=True).stdout.strip() or "main"; existing=self.db.execute("SELECT * FROM repositories WHERE canonical_path=?",(canonical,)).fetchone()
  if existing:return row(existing)
  rid=str(uuid.uuid4());self.db.execute("INSERT INTO repositories VALUES(?,?,?,?,?)",(rid,display_name or Path(canonical).name,canonical,branch,"registered"));self.db.commit();return row(self.db.execute("SELECT * FROM repositories WHERE id=?",(rid,)).fetchone())
 def repositories(self):return [row(x) for x in self.db.execute("SELECT * FROM repositories ORDER BY display_name")]
 def evidence(self,evidence_id):
  value=self.db.execute("SELECT * FROM source_snapshots WHERE id=?",(evidence_id,)).fetchone();result=row(value)
  if result:result["locator"]=json.loads(result["locator"])
  return result
 def evidence_for_repository(self,repository_id):
  return [self.evidence(x["id"]) for x in self.db.execute("SELECT id FROM source_snapshots WHERE repository_id=? ORDER BY source_identity,source_version",(repository_id,))]
 def analyses(self,repository_id):return [self.analysis(x["id"]) for x in self.db.execute("SELECT id FROM analyses WHERE repository_id=? ORDER BY rowid DESC",(repository_id,))]
 def ingest(self,repository_id,revision="HEAD",rule=None):
  repo=self.db.execute("SELECT * FROM repositories WHERE id=?",(repository_id,)).fetchone()
  if not repo:raise KeyError("repository not found")
  sha=resolve(repo["canonical_path"],revision);paths=subprocess.run(["git","-C",repo["canonical_path"],"ls-tree","-r","--name-only",sha],check=True,text=True,capture_output=True).stdout.splitlines();added=0
  for path in paths:
   if not (path.lower().startswith(("docs/adr","adr")) and path.lower().endswith(".md")):continue
   text=subprocess.run(["git","-C",repo["canonical_path"],"show",f"{sha}:{path}"],check=True,text=True,capture_output=True).stdout;digest=hashlib.sha256(text.encode()).hexdigest();identity=f"git:{path}";before=self.db.total_changes
   self.db.execute("INSERT OR IGNORE INTO source_snapshots VALUES(?,?,?,?,?,?,?,?)",(str(uuid.uuid4()),repository_id,identity,sha,digest,text,json.dumps({"revision":sha,"path":path}),None));added+=self.db.total_changes-before
  if rule:
   canonical=json.dumps(rule,sort_keys=True,separators=(",",":"));digest=hashlib.sha256(canonical.encode()).hexdigest();existing=self.db.execute("SELECT * FROM rule_versions WHERE repository_id=? AND content_hash=?",(repository_id,digest)).fetchone()
   if not existing:self.db.execute("INSERT INTO rule_versions VALUES(?,?,?,?,?,?)",(str(uuid.uuid4()),repository_id,1,digest,canonical,"pending"))
  self.db.execute("UPDATE repositories SET ingestion_status='complete' WHERE id=?",(repository_id,));self.db.commit();return {"repository_id":repository_id,"revision":sha,"snapshots_added":added,"status":"complete"}
 def create_analysis(self,repository_id,base,head,cutoff,mode,key):
  old=self.db.execute("SELECT * FROM analyses WHERE repository_id=? AND idempotency_key=?",(repository_id,key)).fetchone()
  if old:return self.analysis(old["id"])
  repo=self.db.execute("SELECT * FROM repositories WHERE id=?",(repository_id,)).fetchone();rule=self.db.execute("SELECT * FROM rule_versions WHERE repository_id=? ORDER BY version DESC LIMIT 1",(repository_id,)).fetchone()
  if not repo or not rule:raise KeyError("repository or rule not found")
  aid=str(uuid.uuid4());b,h=resolve(repo["canonical_path"],base),resolve(repo["canonical_path"],head);self.db.execute("INSERT INTO analyses VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(aid,repository_id,b,h,cutoff,mode,"awaiting_review",rule["id"],rule["version"],rule["content_hash"],json.dumps({"coverage":{"status":"not_executed"},"findings":[]}),key));self.db.commit();return self.analysis(aid)
 def analysis(self,analysis_id):
  value=self.db.execute("SELECT * FROM analyses WHERE id=?",(analysis_id,)).fetchone()
  if not value:return None
  result=row(value);result["outputs"]=json.loads(result["outputs"]);result["findings"]=[json.loads(x["payload"]) for x in self.db.execute("SELECT payload FROM findings WHERE analysis_id=? ORDER BY disposition,payload",(analysis_id,))];return result
 def review(self,target_id,version,content_hash,action,reviewer,rationale,key):
  old=self.db.execute("SELECT * FROM review_events WHERE idempotency_key=?",(key,)).fetchone()
  if old:return row(old)
  rule=self.db.execute("SELECT * FROM rule_versions WHERE id=?",(target_id,)).fetchone()
  if not rule or rule["version"]!=version or rule["content_hash"]!=content_hash:raise ValueError("stale rule version or content hash")
  rid=str(uuid.uuid4());self.db.execute("INSERT INTO review_events VALUES(?,?,?,?,?,?,?,?,?,?)",(rid,rule["repository_id"],target_id,version,content_hash,action,reviewer,rationale,key,now()));self.db.execute("UPDATE rule_versions SET approval_state=? WHERE id=?",("approved" if action=="approve" else "rejected",target_id));self.db.commit();return row(self.db.execute("SELECT * FROM review_events WHERE id=?",(rid,)).fetchone())
 def execute(self,analysis_id):
  analysis=self.db.execute("SELECT * FROM analyses WHERE id=?",(analysis_id,)).fetchone()
  if not analysis:raise KeyError("analysis not found")
  approval=self.db.execute("SELECT 1 FROM review_events WHERE target_id=? AND target_version=? AND content_hash=? AND action='approve' ORDER BY created_at DESC LIMIT 1",(analysis["rule_id"],analysis["rule_version"],analysis["rule_hash"])).fetchone()
  if not approval:raise PermissionError("exact frozen rule version is not approved")
  repo=self.db.execute("SELECT * FROM repositories WHERE id=?",(analysis["repository_id"],)).fetchone();rule=self.db.execute("SELECT * FROM rule_versions WHERE id=? AND content_hash=?",(analysis["rule_id"],analysis["rule_hash"])).fetchone()
  if not rule:raise PermissionError("frozen rule changed")
  output=compare(repo["canonical_path"],analysis["base_sha"],analysis["head_sha"],json.loads(rule["parameters"]));self.db.execute("DELETE FROM findings WHERE analysis_id=?",(analysis_id,))
  for finding in output["findings"]:self.db.execute("INSERT INTO findings VALUES(?,?,?,?,?)",(str(uuid.uuid4()),analysis_id,finding["fingerprint"],finding["disposition"],json.dumps(finding)))
  self.db.execute("UPDATE analyses SET status='completed',outputs=? WHERE id=?",(json.dumps(output),analysis_id));self.db.commit();return self.analysis(analysis_id)
store=DatabaseStore()
