from datetime import datetime,timezone
import pytest
from intentledger.domain import *
def test_scope_exception_and_acceptance():
 d=[Decision("old","accepted","a",("src/**",)),Decision("new","accepted","b",("src/services/**",),("src/services/legacy/**",)),Decision("idea","proposed","c",("src/**",))]
 r=[Relation("new","old","supersedes",("src/services/**",))]
 assert applicable(d,r,"src/services/pay.ts",lambda x:True)==(Applicability.SUPPORTED,["new"])
 assert applicable(d,r,"src/services/legacy/pay.ts",lambda x:True)==(Applicability.SUPPORTED,["old"])
def test_ancestry_not_timestamp():
 d=[Decision("branch","accepted","not-main",("src/**",))]
 assert applicable(d,[],"src/a.ts",lambda x:False)[0]==Applicability.NOT_APPLICABLE
def test_conflict_abstains():
 d=[Decision("a","accepted","1",("src/**",)),Decision("b","accepted","2",("src/**",))]
 assert applicable(d,[Relation("a","b","contradicts",("src/**",))],"src/x.ts",lambda _:True)[0]==Applicability.CONFLICTED
def test_unknown_anchor_and_availability():
 assert applicable([Decision("a","accepted",None,("src/**",))],[],"src/x.ts",lambda _:True)[0]==Applicability.INSUFFICIENT
 cutoff=datetime(2024,1,1,tzinfo=timezone.utc); assert not evidence_eligible(None,cutoff); assert not evidence_eligible(datetime(2025,1,1,tzinfo=timezone.utc),cutoff)
def test_cycle_rejected():
 with pytest.raises(ValueError): validate_relation_graph([Relation("a","b","supersedes",("**",)),Relation("b","a","supersedes",("**",))])
def test_rule_change_invalidates_hash(): assert rule_hash({"x":1})!=rule_hash({"x":2})
