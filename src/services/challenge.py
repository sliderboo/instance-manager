from fastapi import Depends
from sqlalchemy.orm import Session
from repository import Storage
from repository.schema import (
    User,
    Challenge,
    Image,
    ImagePorts,
    ImageEnvironment,
    ImageCapAdd,
    Instance,
)
from models.dto import NewChallengeRequest
from utils.ops import ChallOpsHandler
from utils.gate_keeper import auth


class ChallengeService:

    def __init__(
        self, user: User = Depends(auth), db: Session = Depends(Storage.get)
    ) -> None:
        self._db = db
        self._user = user

    def create(self, challenge: NewChallengeRequest):
        try:
            assert self._user.can_author, "User is not authorized to create challenges"
            ops_handler = ChallOpsHandler(challenge.config)
            challenge = Challenge(
                **{
                    "title": ops_handler.config.title,
                    "description": ops_handler.config.description,
                    "author_id": self._user.id,
                    "category": ops_handler.config.category,
                }
            )
            self._db.add(challenge)
            self._db.commit()
            self._db.refresh(challenge)
            for image in ops_handler.config.images:
                new_image = Image(
                    **{
                        "name": image.name,
                        "challenge_id": challenge.id,
                        "tag": image.tag,
                        "privileged": image.privileged,
                        "custom_host_name": image.custom_host_name,
                    }
                )
                self._db.add(new_image)
                self._db.commit()
                self._db.refresh(new_image)
                if image.ports:
                    for port in image.ports:
                        self._db.add(ImagePorts(value=port, image_id=new_image.id))
                    self._db.commit()
                if image.environment:
                    for key, value in image.environment.items():
                        self._db.add(
                            ImageEnvironment(
                                key=key, value=value, image_id=new_image.id
                            )
                        )
                    self._db.commit()
                if image.cap_add:
                    for cap in image.cap_add:
                        self._db.add(ImageCapAdd(value=cap, image_id=new_image.id))
                    self._db.commit()
            self._db.refresh(challenge)
            return challenge
        except Exception as e:
            self._db.rollback()
            raise Exception(e)
