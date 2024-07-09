from celery import Celery
from config import config
from utils.ops import ChallOpsHandler
from utils.docker import DockerHandler
from repository import Storage, RedisStorage
from repository.challenge import ChallengeRepository
from repository.user import UserRepository
from models.challenge import QueryChallengeModel
from models.user import QueryUserModel
from utils.io import get_valid_port
import json
import string

worker = Celery(
    "worker", broker=f"redis://{config['REDIS_HOST']}:{config['REDIS_PORT']}/1"
)


def normalize(name):
    for c in string.punctuation:
        name = name.replace(c, "")
    return name.replace(" ", "_").lower().strip()


@worker.task(name="worker.pull_images")
def pull_images(config: str, creds: dict):
    lock_store = next(RedisStorage.get())
    ops_handler = ChallOpsHandler(config, creds=creds)
    lock_store.set(f"pulling:{ops_handler.cfg.title}", 1)
    try:
        ops_handler.pull_images()
    except Exception as e:
        print(f"Failed to pull images: {e}")
    lock_store.delete(f"pulling:{ops_handler.cfg.title}")


@worker.task(name="worker.start_challenge")
def start_challenge(chall_id: int, creator_id: str):
    storage = next(Storage.get())
    repo: ChallengeRepository = ChallengeRepository(storage)
    user_repo = UserRepository(storage)
    lock_store = next(RedisStorage.get())
    docker = DockerHandler()
    challenge = repo.find_one(QueryChallengeModel(id=chall_id))
    res = None
    try:
        lock_store.set(f"start:{chall_id}", 1)
        containers = []
        connection_info = {
            "host": config["CHALLENGE_HOST"]["HOST"],
            "ports": {},
        }
        chall_net = docker.create_challenge_network(
            f"chall-{normalize(challenge.title)}-network"
        )
        if not chall_net:
            lock_store.delete(f"chall:{chall_id}")
            raise Exception("Cannot create network for challenge")
        for service in challenge.services:
            valid_ports = []
            if service.ports:
                ports = json.loads(service.ports)
            else:
                ports = []
            for _ in range(len(ports)):
                valid_ports.append(get_valid_port(lock_store))
            connection_info["ports"].update({x: y for x, y in zip(ports, valid_ports)})
            cap_add = json.loads(service.cap_add) if service.cap_add else []
            environment = json.loads(service.environment) if service.environment else []
            container = docker.create_container(
                service.image,
                name=f"chall-{normalize(challenge.title)}-{normalize(service.name)}",
                network=chall_net.name,
                cpu_shares=int(float(service.cpu) * 1024),
                mem_limit=service.memory,
                privileged=service.privileged,
                detach=True,
                cap_add=cap_add,
                environment=environment,
                ports={f"{x}/tcp": y for x, y in zip(ports, valid_ports)},
                restart_policy={
                    "Name": "always",
                },
            )
            containers.append(container)
            docker.attach_container(container, chall_net, service.name)

        for container in containers:
            container.start()

        challenge = repo.change_status(challenge, connection_info=connection_info)
        repo.add_user(challenge, user_repo.find_one(QueryUserModel(id=creator_id)))
        lock_store.set(f"chall:{chall_id}:count", 1)
        res = f'Starting challenge "{challenge.title}" successful'
    except Exception as e:
        clean_challenge(challenge.id)
        for port in connection_info["ports"].values():
            lock_store.delete(f"port:{port}")
        lock_store.delete(f"chall:{chall_id}:count")
        res = f"Failed to start challenge {challenge.title}: {e}"
    finally:
        lock_store.delete(f"start:{chall_id}")
        return res


@worker.task(name="worker.clean_challenge")
def clean_challenge(chall_id: int, tries=0):
    storage = next(Storage.get())
    repo: ChallengeRepository = ChallengeRepository(storage)
    lock_store = next(RedisStorage.get())
    docker = DockerHandler()
    if tries > 3:
        lock_store.delete(f"delete:{chall_id}")
        print(f"Failed to clean challenge {chall_id}")
        return
    try:
        lock_store.set(f"delete:{chall_id}", 1)
        lock_store.delete(f"chall:{chall_id}")
        lock_store.delete(f"chall:{chall_id}:count")
        challenge = repo.find_one(QueryChallengeModel(id=chall_id))
        if challenge.connection_info:
            connection_info = json.loads(challenge.connection_info)
            for port in connection_info["ports"].values():
                lock_store.delete(f"port:{port}")
        challenge = repo.change_status(challenge, connection_info=None)
        for service in challenge.services:
            container = docker.get_container(
                f"chall-{normalize(challenge.title)}-{normalize(service.name)}"
            )
            if container:
                container.stop()
                container.remove()
        docker.remove_network(f"chall-{normalize(challenge.title)}-network")
        lock_store.delete(f"delete:{chall_id}")
    except Exception as e:
        print(f"Failed to clean challenge {chall_id}: {e}")
        clean_challenge(chall_id, tries + 1)
