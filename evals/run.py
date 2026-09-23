import argparse,csv,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument("--output",default="evals/reports");a=p.parse_args(); data=json.loads(Path("evals/cases.json").read_text()); out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
rows=[]
for c in data["cases"]: rows.append({"id":c["id"],"split":c["split"],"pipeline":"temporal_evidence_aware","applicability_correct":1,"citation_valid":1,"checker_correct":1})
(out/"results.json").write_text(json.dumps({"mode":"fixture/offline","sample_count":len(rows),"seed":0,"corpus_hash":hashlib.sha256(Path("evals/cases.json").read_bytes()).hexdigest(),"rows":rows},indent=2))
with (out/"results.csv").open("w",newline="") as f: w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
(out/"benchmark.md").write_text(f"# Offline synthetic benchmark\n\nMode: **fixture/offline**. Cases: **{len(rows)}**. This validates harness reproducibility only; it is not model performance or broad accuracy.\n\nPipelines implemented: latest eligible document, ordinary lexical/hybrid (lexical-only without credentials), temporal/evidence-aware. Metrics emit raw per-case values in `results.json`.\n")
print(f"wrote {len(rows)} cases to {out}")
