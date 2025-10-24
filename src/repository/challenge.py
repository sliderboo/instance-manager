from repository import Storage
from sqlalchemy.orm import Session
from fastapi import Depends
from repository.schema import Challenge, Service, User
from models.challenge import ChallengeConfig, QueryChallengeModel
from sqlalchemy import and_
from sqlalchemy.sql import text
from json import dumps
from logging import getLogger

log = getLogger(__name__)


class ChallengeRepository:
    def __init__(self, db: Session = Depends(Storage.get)):
        self._session = db

    def create(self, challCfg: ChallengeConfig):
        try:
            chall = Challenge(
                title=challCfg.title,
                visible=challCfg.visible,
            )
            chall = self.add_and_refresh(chall)
            for service in challCfg.services:
                new_service = Service(
                    image=service.image,
                    name=service.name,
                    challenge_id=chall.id,
                    privileged=service.privileged,
                    cpu=str(service.cpu),
                    memory=service.memory,
                    ports=dumps(service.ports),
                    environment=dumps(service.environment or []),
                    cap_add=dumps(service.cap_add or []),
                )
                new_service = self.add_and_refresh(new_service)
                self._session.commit()
            self._session.refresh(chall)
            return chall
        except Exception as e:
            self._session.rollback()
            raise Exception(e)

    def update(self, challCfg: ChallengeConfig):
        try:
            chall = self.find_one(QueryChallengeModel(title=challCfg.title))
            if not chall:
                raise Exception("Challenge not found")
            for service in challCfg.services:
                service_db = (
                    self._session.query(Service)
                    .filter(
                        and_(
                            Service.challenge_id == chall.id,
                            Service.image == service.image,
                        )
                    )
                    .first()
                )
                if service_db:
                    for key, value in service.model_dump(exclude_none=True).items():
                        if type(value) == list:
                            value = dumps(value)
                        setattr(service_db, key, value)
                    self._session.commit()
                    self._session.refresh(service_db)
                else:
                    new_service = Service(
                        image=service.image,
                        name=service.name,
                        challenge_id=chall.id,
                        privileged=service.privileged,
                        cpu=str(service.cpu),
                        memory=service.memory,
                        ports=dumps(service.ports),
                        environment=dumps(service.environment or []),
                        cap_add=dumps(service.cap_add or []),
                    )
                    new_service = self.add_and_refresh(new_service)
            self._session.refresh(chall)
            return chall
        except Exception as e:
            self._session.rollback()
            raise Exception(e)

    def list(self, page: int = 1):
        return (
            self._session.query(Challenge)
            .filter(Challenge.visible == True)
            .limit(50)
            .offset((page - 1) * 50)
            .all()
        )

    def find_one(self, query: QueryChallengeModel):
        return (
            self._session.query(Challenge)
            .filter_by(**query.model_dump(exclude_none=True))
            .first()
        )

    def add_array(self, array):
        if array:
            for item in array:
                self._session.add(item)
            self._session.commit()
        return array

    def count(self):
        return self._session.query(Challenge).count()

    def add_and_refresh(self, obj):
        self._session.add(obj)
        self._session.commit()
        self._session.refresh(obj)
        return obj

    def change_status(self, challenge, connection_info: dict = None):
        if connection_info:
            challenge.connection_info = dumps(connection_info)
            challenge.status = "running"
        else:
            challenge.connection_info = None
            challenge.status = "stop"
        challenge = self.add_and_refresh(challenge)
        return challenge

    def add_user(self, challenge, user):
        try:
            challenge.players.append(user)
            challenge = self.add_and_refresh(challenge)
            return challenge
        except Exception as e:
            self._session.rollback()
            return None

    def remove_user(self, challenge_id, user_id):
        try:
            challenge = self.find_one(QueryChallengeModel(id=challenge_id))
            if not challenge:
                return []
            user = self._session.query(User).filter_by(id=user_id).first()
            if not user:
                return []
            challenge.players.remove(user)
            challenge = self.add_and_refresh(challenge)
            return challenge.players
        except:
            return []

    def fetch_user_join(self, minutes: int):
        try:
            results = self._session.execute(
                text(
                    "SELECT * FROM joins WHERE joined_at < NOW() - INTERVAL ':minutes' MINUTE"
                ),
                {"minutes": minutes},
            ).fetchall()
            log.debug(f"Results: {results}")
            return [
                {"challenge_id": result[1], "user_id": result[2]} for result in results
            ]
        except Exception as e:
            log.debug(f"Error: {e}")
            return []

    def delete(self, challenge_id: int):
        try:
            challenge = self.find_one(QueryChallengeModel(id=challenge_id))
            if not challenge:
                return False
            
            # Delete the challenge (cascade will handle related services and joins)
            self._session.delete(challenge)
            self._session.commit()
            # Reset sequence if no challenges left
            if self.count() == 0:
                self._session.execute(text("ALTER SEQUENCE challenges_id_seq RESTART WITH 1;"))
                self._session.commit()
            return True
        except Exception as e:
            log.debug(f"Error deleting challenge: {e}")
            self._session.rollback()
            return False
