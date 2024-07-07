from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped
from sqlalchemy import Column, String, ForeignKey, Table, Integer, Enum, Boolean
from sqlalchemy.orm import relationship, mapped_column
from typing import List
import enum

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    display_name = Column(String)

    can_author = Column(Boolean, default=False)

    joined_instances: Mapped[List["Instance"]] = relationship(
        "Instance", secondary="joins", back_populates="players"
    )

    spawned_instances: Mapped[List["Instance"]] = relationship(
        "Instance", back_populates="creator"
    )

    created_challenges: Mapped[List["Instance"]] = relationship(
        "Challenge", back_populates="author"
    )


class ImagePorts(Base):
    __tablename__ = "image_ports"

    id = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)

    image_id = mapped_column(Integer, ForeignKey("images.id"))
    image = relationship("Image", back_populates="ports", foreign_keys=[image_id])

    value = mapped_column(String)


class ImageEnvironment(Base):
    __tablename__ = "image_environment"

    id = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)

    image_id = mapped_column(Integer, ForeignKey("images.id"))
    image = relationship("Image", back_populates="environment", foreign_keys=[image_id])

    key = mapped_column(String)
    value = mapped_column(String)


class ImageCapAdd(Base):
    __tablename__ = "image_cap_add"

    id = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)

    image_id = mapped_column(Integer, ForeignKey("images.id"))
    image = relationship("Image", back_populates="cap_add", foreign_keys=[image_id])

    value = mapped_column(String)


class Image(Base):
    __tablename__ = "images"

    id = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)

    name = mapped_column(String)
    custom_host_name = mapped_column(String, nullable=True)
    tag: Mapped[str] = mapped_column(String, default="latest")

    challenge_id = mapped_column(Integer, ForeignKey("challenges.id"))
    challenge = relationship("Challenge", back_populates="images")

    privileged = mapped_column(Boolean, default=False)

    ports: Mapped["ImagePorts"] = relationship("ImagePorts", back_populates="image")
    environment: Mapped["ImageEnvironment"] = relationship(
        "ImageEnvironment", back_populates="image"
    )
    cap_add: Mapped[List["ImageCapAdd"]] = relationship(
        "ImageCapAdd", back_populates="image"
    )

    instances: Mapped[List["Instance"]] = relationship(
        "Instance", back_populates="image"
    )


joins = Table(
    "joins",
    Base.metadata,
    Column("instance_id", Integer, ForeignKey("instances.id")),
    Column("user_id", String, ForeignKey(User.id)),
)


class InstanceStatus(enum.Enum):
    STOPPED = 0
    RUNNING = 1
    CRASHED = 2


class Instance(Base):
    __tablename__ = "instances"

    id = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)

    image_id = mapped_column(Integer, ForeignKey("images.id"))
    image = relationship("Image", back_populates="instances")

    creator_id = mapped_column(String, ForeignKey(User.id))
    creator = relationship("User", back_populates="spawned_instances")
    created_at = mapped_column(String)

    players = relationship("User", secondary="joins", back_populates="joined_instances")

    re_spawn = mapped_column(Integer, default=0)
    status = mapped_column(Enum(InstanceStatus), default=InstanceStatus.RUNNING)


class Challenge(Base):
    __tablename__ = "challenges"

    id = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)

    author_id = mapped_column(String, ForeignKey(User.id))
    author = relationship("User", back_populates="created_challenges")
    title = mapped_column(String)
    description = mapped_column(String)
    category = mapped_column(String)

    images: Mapped[List["Image"]] = relationship("Image", back_populates="challenge")

    flag = mapped_column(String, default="flag{this_is_a_flag}")
