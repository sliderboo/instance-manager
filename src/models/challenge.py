from pydantic import BaseModel
from typing import List, Optional


class QueryChallengeModel(BaseModel):
    author: Optional[str] = None
    category: Optional[str] = None
    title: Optional[str] = None
    id: Optional[int] = None


class ImageConfig(BaseModel):
    name: str
    tag: Optional[str] = "latest"
    ports: Optional[List[int]] = None
    privileged: Optional[bool] = False
    environment: Optional[dict] = None
    cap_add: Optional[List[str]] = None
    custom_host_name: Optional[str] = None


class ChallengeConfig(BaseModel):
    title: str
    description: str
    category: str
    author: str

    enc_flag: str

    images: List[ImageConfig]
