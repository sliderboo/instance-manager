from repository.schema import Base
from repository.schema.user import User
from sqlalchemy import Column, String, ForeignKey, Table, Integer, Enum
from sqlalchemy.orm import relationship, mapped_column
import enum


class Image(Base):
    __tablename__ = "images"

    id = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)

    name = mapped_column(String)

    challenge_id = mapped_column(String, ForeignKey("challenges.id"))
    challenge = relationship("Challenge", back_populates="images")

    save_path = mapped_column(String)
    config = mapped_column(String)


joins = Table(
    "joins",
    Base.metadata,
    Column("instance_id", String, ForeignKey("instances.id")),
    Column("user_id", String, ForeignKey(User.id)),
)


class InstanceStatus(enum.Enum):
    STOPPED = 0
    RUNNING = 1
    CRASHED = 2


class Instance(Base):
    __tablename__ = "instances"

    id = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)

    challenge_id = mapped_column(String, ForeignKey("challenges.id"))
    challenge = relationship("Challenge", back_populates="instances")

    creator = mapped_column(String, ForeignKey(User.id))
    created_at = mapped_column(String)

    players = relationship(
        "User", secondary="joins", back_populates="joined_instances", lazy="select"
    )

    re_spawn = mapped_column(Integer, default=0)
    status = mapped_column(Enum(InstanceStatus), default=InstanceStatus.RUNNING)


class Challenge(Base):
    __tablename__ = "challenges"

    id = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)

    author = mapped_column(String, ForeignKey(User.id))
    title = mapped_column(String)
    description = mapped_column(String)
    difficulty = mapped_column(String)

    images: list[Image] = relationship("Image", backref="challenge")
    instances: list["Instance"] = relationship("Instance", backref="challenge")
