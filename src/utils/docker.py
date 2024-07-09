from docker import DockerClient
from config import config


class DockerHandler:
    def __init__(self, creds: dict = None):
        self._client = DockerClient(base_url=config["DOCKER"]["HOST"])
        creds = creds or {}
        self._registry = config["DOCKER"]["REGISTRY"]
        self._username = creds.get("username", config["DOCKER"]["USERNAME"])
        self._password = creds.get("password", config["DOCKER"]["PASSWORD"])

        if config["DOCKER"]["REGISTRY"] and self._username and self._password:
            self._client.login(
                username=self._username,
                password=self._password,
                registry=self._registry,
            )
        if not self._client.ping():
            raise Exception("Failed to connect to docker")

    def verify_image(self, image_name: str):
        auth_config = None
        if self._username and self._password and self._registry in image_name:
            auth_config = {
                "username": self._username,
                "password": self._password,
            }
        try:
            image = self._client.images.get_registry_data(
                image_name,
                auth_config=auth_config,
            )
            return image is not None
        except:
            return False

    def remove_challenge(self, name: str):
        try:
            self._client.networks.get(name).remove()
        except:
            pass
        try:
            self._client.containers.prune()
        except:
            pass

    def create_container(self, image_name: str, **kwargs):
        container = self._client.containers.create(image_name, **kwargs)
        return container

    def pull_image(self, image_name: str):
        try:
            if ":" in image_name:
                image_name, tag = image_name.split(":")
            self._client.images.pull(image_name, tag=tag)
            return True
        except:
            return False

    def create_challenge_network(self, name: str):
        try:
            return self._client.networks.create(name)
        except:
            return None

    def attach_container(self, container, network, alias):
        try:
            network.connect(container, aliases=[alias])
            return True
        except:
            return False

    def get_container(self, container_name):
        try:
            container = self._client.containers.get(container_name)
            return container
        except:
            return None

    def remove_network(self, network_name):
        try:
            network = self._client.networks.get(network_name)
            network.remove()
            return True
        except:
            False
