from pydantic import BaseModel
from typing import Optional, Dict


class NewChallengeRequest(BaseModel):
    config: str
    creds: Optional[Dict[str, str]] = None


class InstanceRequest(BaseModel):
    challenge_id: int
