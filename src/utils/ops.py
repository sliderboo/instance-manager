from base64 import b64decode
from models.challenge import ChallengeConfig
from .docker import DockerHandler
from yaml import safe_load


class ChallOpsHandler:
    def __init__(self, enc_config: str, creds: dict = None):
        self.raw_cfg = b64decode(enc_config.encode()).decode("utf-8")
        self.cfg = ChallengeConfig.model_validate(safe_load(self.raw_cfg))
        self._docker = DockerHandler(creds)

    def verify_images(self):
        for ser in self.cfg.services:
            if not self._docker.verify_image(ser.image):
                raise Exception(f"Image {ser.image} not found")

    def pull_images(self):
        for ser in self.cfg.services:
            if not self._docker.pull_image(ser.image):
                raise Exception(f"Failed to pull image {ser.image}")

    @property
    def config(self):
        return self.cfg

    @property
    def challenge(self):
        tmp = self.cfg.model_dump()
        tmp.pop("images")
        return tmp

    @property
    def images(self):
        return [x.image for x in self.cfg.services]
