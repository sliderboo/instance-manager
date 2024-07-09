from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped
from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    Table,
    Integer,
    Enum,
    Boolean,
    DateTime,
)
from sqlalchemy.orm import relationship, mapped_column
from typing import List
import datetime
from uuid import uuid4

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = mapped_column(String, primary_key=True, index=True, default=uuid4)
    email = mapped_column(String, unique=True)
    display_name = mapped_column(String, unique=True, index=True)
    is_admin = mapped_column(Boolean, default=False)

    joined_challanges: Mapped[List["Challenge"]] = relationship(
        "Challenge", secondary="joins", back_populates="players"
    )


class Service(Base):
    __tablename__ = "services"

    id = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)

    image = mapped_column(String, nullable=False)
    name = mapped_column(String, nullable=False)

    challenge_id = mapped_column(Integer, ForeignKey("challenges.id"))
    challenge = relationship("Challenge", back_populates="services")

    privileged = mapped_column(Boolean, default=False)
    cpu = mapped_column(String, default="0.5")
    memory = mapped_column(String, default="512M")

    ports = mapped_column(String, nullable=False)
    environment = mapped_column(String, nullable=False)
    cap_add = mapped_column(String, nullable=False)

    def __repr__(self):
        return f"<Service {self.name} with image: {self.image}>"


class Challenge(Base):
    __tablename__ = "challenges"

    id = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)

    title = mapped_column(String, unique=True, index=True)

    services: Mapped[List["Service"]] = relationship(
        "Service", back_populates="challenge"
    )

    players = relationship(
        "User", secondary="joins", back_populates="joined_challanges"
    )

    status = mapped_column(Enum("running", "stop", name="status"), default="stop")

    visible = mapped_column(Boolean, default=True)

    connection_info = mapped_column(String, nullable=True)

    def __repr__(self):
        return f"<Challenge {self.title} with status: {'running' if self.connection_info else 'stopped'}>"


joins = Table(
    "joins",
    Base.metadata,
    Column("id", Integer, primary_key=True, index=True, autoincrement=True),
    Column("challenge_id", Integer, ForeignKey(Challenge.id)),
    Column("user_id", String, ForeignKey(User.id)),
    Column("joined_at", DateTime, default=datetime.datetime.now),
)
