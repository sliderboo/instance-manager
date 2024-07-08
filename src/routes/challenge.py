from fastapi import APIRouter, status, Depends
from utils.api import APIResponse
from services.challenge import ChallengeService
from models.dto import NewChallengeRequest, InstanceRequest
from utils.gate_keeper import auth

router = APIRouter()


@router.post("/create")
def create_challenge(
    newChallReq: NewChallengeRequest,
    service: ChallengeService = Depends(ChallengeService),
):
    chall = service.create(newChallReq)
    return APIResponse.as_json(
        code=status.HTTP_201_CREATED,
        status="Challenge created successfully",
        data={
            "id": chall.id,
            "title": chall.title,
            "description": chall.description,
            "category": chall.category,
            "images": [x.name for x in chall.images],
        },
    )


@router.post("/request")
def request_spawn_instance(
    instance: InstanceRequest,
    service: ChallengeService = Depends(ChallengeService),
):
    instance = service.request_instance(instance.challenge_id)
    return APIResponse.as_json(
        code=status.HTTP_201_CREATED,
        status="Instance created successfully",
        data={
            "id": instance.id,
            "image": instance.image.name,
            "status": instance.status,
        },
    )
