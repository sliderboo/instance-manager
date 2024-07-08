from pydantic import BaseModel


class NewChallengeRequest(BaseModel):
    config: str

class InstanceRequest(BaseModel):
    challenge_id: int
