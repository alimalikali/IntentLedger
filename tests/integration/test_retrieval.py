from intentledger.retrieval import eligible,temporal_evidence_aware
def test_future_evidence_leakage():
 old={"id":"old","text":"adapter","available_at":"2024-01-01","relations":[]}; future={"id":"future","text":"adapter compelling","available_at":"2025-01-01","relations":[]}
 assert temporal_evidence_aware("adapter",[old],"2024-02-01")==temporal_evidence_aware("adapter",[old,future],"2024-02-01")
