from repository.schema import Base
from repository.schema.user import User
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship


class Image(Base):
    pass


class Challenge(Base):
    __tablename__ = "challenges"

    author = Column(String, ForeignKey(User.id))
    title = Column(String)
    description = Column(String)
    difficulty = Column(String)
    config = Column(String)

    images: list[Image] = relationship("Image", backref="challenge")
