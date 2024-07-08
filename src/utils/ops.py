from base64 import b64decode
from yaml import safe_load
from models.challenge import ChallengeConfig
from .docker import DockerHandler
from rsa import decrypt, PrivateKey
from config import config


class ChallOpsHandler:
    def __init__(self, enc_config: str):
        self.raw_cfg = b64decode(enc_config.encode()).decode("utf-8")
        self.cfg = ChallengeConfig.model_validate(safe_load(self.raw_cfg))
        self._docker = DockerHandler()
        assert self.verify_images(), "Invalid image(s) provided"

    def verify_images(self):
        for img in self.cfg.images:
            if not self._docker.verify_image(f"{img.name}:{img.tag}"):
                return False
        return True

    @property
    def config(self):
        return self.cfg

    @property
    def challenge(self):
        tmp = self.cfg.model_dump()
        tmp.pop("images")
        return tmp

    @property
    def flag(self):
        return (
            decrypt(
                b64decode(self.cfg.enc_flag.encode()),
                PrivateKey.load_pkcs1(config["PRIVATE_KEY"].encode()),
            )
            .strip()
            .decode()
        )
