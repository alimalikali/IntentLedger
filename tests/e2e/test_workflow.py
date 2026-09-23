def test_primary_workflow_contract():
 from intentledger.domain import rule_hash
 h=rule_hash({"kind":"adapter_boundary"}); assert len(h)==64
