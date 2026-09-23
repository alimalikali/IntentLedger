from typing import Protocol
class Provider(Protocol):
    label:str
    def propose(self,evidence:list[dict])->dict: ...
class FixtureProvider:
    label="Demo fixture provider"
    def propose(self,evidence):
        ids=[e["id"] for e in evidence]
        return {"provider_mode":self.label,"statement":"Services use the payment adapter.","evidence_ids":ids,"requires_review":True}
class UnavailableLiveProvider:
    label="Live provider unavailable"
    def propose(self,evidence): return {"provider_mode":self.label,"status":"unavailable","reason":"credentials/model not configured"}
