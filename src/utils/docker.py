from docker import DockerClient
from config import config


class DockerHandler:
    def __init__(self):
        self._client = DockerClient(base_url=config["DOCKER"]["HOST"])
        if config["DOCKER"]["REGISTRY"]:
            self._client.login(
                username=config["DOCKER"]["USERNAME"],
                password=config["DOCKER"]["PASSWORD"],
                registry=config["DOCKER"]["REGISTRY"],
            )
        assert self._client.ping(), "Docker daemon is not running"

    def verify_image(self, image_name: str):
        try:
            image_name = self.normalize_image(image_name)
            image = self._client.images.get_registry_data(image_name)
            assert image, "Image not found"
            return True
        except:
            return False

    def normalize_image(self, image_name: str):
        return config["DOCKER"]["USERNAME"] + "/" + image_name
