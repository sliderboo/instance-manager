from fastapi import Depends
from repository.schema import (
    User,
)
from repository.challenge import ChallengeRepository
from models.dto import NewChallengeRequest
from models.challenge import QueryChallengeModel
from models.user import QueryUserModel
from repository.user import UserRepository
from utils.ops import ChallOpsHandler
from utils.gate_keeper import auth
from worker import pull_images, start_challenge, clean_challenge
from repository import RedisStorage
from redis import Redis
import json


class ChallengeService:

    def __init__(
        self,
        user: User = Depends(auth),
        lock_store: Redis = Depends(RedisStorage.get),
        repo: ChallengeRepository = Depends(ChallengeRepository),
        user_repo: UserRepository = Depends(UserRepository),
    ) -> None:
        self._repo = repo
        self._user = user
        self._user_repo = user_repo
        self._lock_store = lock_store

    def create(self, challenge: NewChallengeRequest):
        if self._user.id != "bot":
            raise Exception("Only bot can create challenges")
        ops_handler = ChallOpsHandler(challenge.config, creds=challenge.creds)
        ops_handler.verify_images()
        pull_images.delay(challenge.config, challenge.creds)
        return self._repo.create(ops_handler.config)

    def create_instance(self, chall_id: int):
        if self._lock_store.get(f"start:{chall_id}") or self._lock_store.get(
            f"delete:{chall_id}"
        ):
            return False
        start_challenge.delay(chall_id, self._user.id)
        return True

    def reset_challenge(self, chall_id: int):
        challenge = self._repo.find_one(QueryChallengeModel(id=chall_id))
        if not challenge:
            return False
        if self._user.display_name not in [x.display_name for x in challenge.players]:
            return False
        clean_challenge(chall_id)
        start_challenge.delay(chall_id, self._user.id)
        return True

    def list_challenges(self, page):
        challenges = self._repo.list(page)
        challenges = [
            {
                "id": x.id,
                "title": x.title,
                "connection_info": x.connection_info,
                "players": [y.display_name for y in x.players],
            }
            for x in challenges
        ]
        joined_challenges = [
            {
                "id": x["id"],
            }
            for x in filter(
                lambda x: self._user.display_name in x["players"], challenges
            )
        ]
        return {
            "total": self._repo.count() or 0,
            "data": challenges,
            "join": joined_challenges,
        }

    def get_challenge(self, chall_id: int):
        challenge = self._repo.find_one(QueryChallengeModel(id=chall_id))
        if not challenge:
            return None
        player_names = [x.display_name for x in challenge.players]
        joined = self._user.display_name in player_names
        result = {
            "id": challenge.id,
            "title": challenge.title,
            "services": [
                {
                    "name": x.name,
                    "image": x.image,
                    "ports": json.loads(x.ports),
                }
                for x in challenge.services
            ],
            "players": player_names,
            "joined": joined,
        }
        if joined:
            connect_info = challenge.connection_info
            if not connect_info:
                raise Exception("Challenge not started")
            result["connection_info"] = json.loads(connect_info)
        return result

    def join_challenge(self, challenge_id: int):
        challenge = self._repo.find_one(QueryChallengeModel(id=challenge_id))
        if not challenge:
            return False
        if self._user in challenge.players:
            return False
        challenge = self._repo.add_user(challenge, self._user)
        self._lock_store.incr(f"chall:{challenge_id}:count")
        return challenge is not None

    def leave_challenge(self, challenge_id: int):
        remain_player = self._repo.remove_user(challenge_id, self._user.id)
        if len(remain_player) == 0:
            clean_challenge.delay(challenge_id)
        return remain_player

    def kick_user(self, challenge_id: int, email: str):
        try:
            kicked_user = self._user_repo.find_one(QueryUserModel(email=email))
            if "@" not in email:
                kicked_user = self._user_repo.find_one(
                    QueryUserModel(display_name=email)
                )
            remain_players = self._repo.remove_user(challenge_id, kicked_user.id)
            if len(remain_players) > 0:
                remain_players = [x.display_name for x in remain_players]
            return remain_players
        except:
            return []

    def kick_all(self, challenge_id: int):
        try:
            challenge = self._repo.find_one(QueryChallengeModel(id=challenge_id))
            for player in challenge.players:
                self._repo.remove_user(challenge_id, player.id)
            clean_challenge.delay(challenge_id)
            return True
        except:
            return False

    def check_exist(self, enc_config: str):
        ops = ChallOpsHandler(enc_config=enc_config)
        return self._repo.find_one(QueryChallengeModel(title=ops.cfg.title)) is not None

    def update(self, challenge: NewChallengeRequest):
        ops_handler = ChallOpsHandler(challenge.config, creds=challenge.creds)
        ops_handler.verify_images()
        pull_images.delay(challenge.config, challenge.creds)
        return self._repo.update(ops_handler.config)

    def get_challenge_status(self, chall_id: int):
        challenge = self._repo.find_one(QueryChallengeModel(id=chall_id))
        status = "stopped"
        if self._lock_store.get(f"start:{chall_id}"):
            status = "creating"
        if self._lock_store.get(f"delete:{chall_id}"):
            status = "deleting"
        if challenge.connection_info and self._lock_store.get(
            f"chall:{chall_id}:count"
        ):
            status = "running"
        if self._lock_store.get(f"pulling:{challenge.title}"):
            status = "pulling"
        return status
