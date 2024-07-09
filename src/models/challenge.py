from pydantic import BaseModel
from typing import List, Optional, Union


class QueryChallengeModel(BaseModel):
    title: Optional[str] = None
    id: Optional[int] = None


class ServiceConfig(BaseModel):
    image: str
    name: str
    cpu: Union[int, str, None, float] = "0.5"
    memory: Optional[str] = "1G"
    ports: Optional[List[int]] = []
    privileged: Optional[bool] = False
    environment: Optional[List[str]] = []
    cap_add: Optional[List[str]] = []


class ChallengeConfig(BaseModel):
    title: str
    visible: Optional[bool] = True
    services: List[ServiceConfig]
