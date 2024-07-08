from fastapi import Depends
from repository.schema import (
    User,
    Challenge,
    Image,
    ImagePorts,
    ImageEnvironment,
    ImageCapAdd,
    Instance,
)
from repository.challenge import ChallengeRepository
from models.dto import NewChallengeRequest
from utils.ops import ChallOpsHandler
from utils.gate_keeper import auth


class ChallengeService:

    def __init__(
        self,
        user: User = Depends(auth),
        repo: ChallengeRepository = Depends(ChallengeRepository),
    ) -> None:
        self._repo = repo
        self._user = user

    def create(self, challenge: NewChallengeRequest):
        assert self._user.id == "bot", "User is not authorized to create challenges"
        ops_handler = ChallOpsHandler(challenge.config)
        return self._repo.create(ops_handler.config, ops_handler.flag)

    def request_instance(self, chall_id):
        exist_instance = self._db.query(Instance).filter()
