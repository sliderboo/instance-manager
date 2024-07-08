from repository import Storage
from sqlalchemy.orm import Session
from fastapi import Depends
from models.challenge import ChallengeConfig
from repository.schema import (
    Challenge,
    Image,
    ImagePorts,
    ImageEnvironment,
    ImageCapAdd,
)


class ChallengeRepository:
    def __init__(self, db: Session = Depends(Storage.get)):
        self._session = db

    def create(self, challCfg: ChallengeConfig, flag: str):
        try:
            chall = Challenge(
                title=challCfg.title,
                description=challCfg.description,
                category=challCfg.category,
                author=challCfg.author,
                flag=flag,
            )
            chall = self.add_and_refresh(chall)
            for image in challCfg.images:
                new_image = Image(
                    name=image.name,
                    tag=image.tag,
                    custom_host_name=image.custom_host_name,
                    challenge_id=chall.id,
                )
                new_image = self.add_and_refresh(new_image)
                image.ports = self.add_array(
                    [
                        ImagePorts(image_id=new_image.id, value=port)
                        for port in image.ports
                    ]
                    if image.ports
                    else None
                )
                image.environment = self.add_array(
                    [
                        ImageEnvironment(image_id=new_image.id, key=key, value=value)
                        for key, value in image.environment.items()
                    ]
                    if image.environment
                    else None
                )
                image.cap_add = self.add_array(
                    [
                        ImageCapAdd(image_id=new_image.id, value=cap)
                        for cap in image.cap_add
                    ]
                    if image.cap_add
                    else None
                )
                self._session.commit()
            self._session.refresh(chall)
            return chall
        except:
            self._session.rollback()
            raise Exception("Failed to create challenge")

    def add_array(self, array):
        if array:
            for item in array:
                self._session.add(item)
            self._session.commit()
        return array

    def add_and_refresh(self, obj):
        self._session.add(obj)
        self._session.commit()
        self._session.refresh(obj)
        return obj
