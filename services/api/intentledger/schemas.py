from datetime import datetime
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field
class Strict(BaseModel):model_config=ConfigDict(extra="forbid")
class RepositoryCreate(Strict):path:str;display_name:str|None=None
class IngestionRequest(Strict):revision:str="HEAD";rule:dict|None=None
class AnalysisRequest(Strict):repository_id:str;base:str;head:str;evidence_cutoff:datetime;mode:Literal["strict_replay","current_reconstruction"]="strict_replay";idempotency_key:str
class ReviewRequest(Strict):target_id:str;version:int=Field(ge=1);content_hash:str=Field(pattern=r"^[0-9a-f]{64}$");action:Literal["approve","reject","activate"];reviewer:str;rationale:str;idempotency_key:str
class PRComment(Strict):identity:str;author:str;timestamp:datetime;body:str;snapshots:list[dict]=[]
class PRImport(Strict):repository:str;identifier:str;title:str;body:str="";base_sha:str|None=None;head_sha:str|None=None;merge_sha:str|None=None;state:Literal["open","closed","merged"];created_at:datetime;updated_at:datetime;merged_at:datetime|None=None;comments:list[PRComment]=[]
