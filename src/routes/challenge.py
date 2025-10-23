from fastapi import APIRouter, status, Depends, Query
from utils.api import APIResponse
from services.challenge import ChallengeService
from models.dto import NewChallengeRequest, InstanceRequest

router = APIRouter()


@router.post("/init")
async def create_challenge(
    newChallReq: NewChallengeRequest,
    service: ChallengeService = Depends(ChallengeService),
):
    chall = None
    is_update = False
    if not service.check_exist(newChallReq.config):
        chall = service.create(newChallReq)
    else:
        chall = service.update(newChallReq)
        is_update = True
    return APIResponse.as_json(
        code=status.HTTP_201_CREATED if not is_update else status.HTTP_200_OK,
        status=(
            "Challenge created successfully"
            if not is_update
            else "Challenge updated successfully"
        ),
        data={
            "id": chall.id,
            "title": chall.title,
            "images": [x.image for x in chall.services],
        },
    )


@router.post("/start")
async def request_spawn_instance(
    instance: InstanceRequest,
    service: ChallengeService = Depends(ChallengeService),
):
    success = service.create_instance(instance.challenge_id)
    return APIResponse.as_json(
        code=status.HTTP_200_OK,
        status=(
            "Instance started successfully"
            if success
            else "Instance is already running"
        ),
        data=success,
    )


@router.get("/{challenge_id}")
async def get_challenge(
    challenge_id: int,
    service: ChallengeService = Depends(ChallengeService),
):
    challenge = service.get_challenge(challenge_id)
    return APIResponse.as_json(
        code=status.HTTP_200_OK,
        status="Challenge retrieved successfully",
        data=challenge,
    )


@router.get("/{challenge_id}/status")
async def get_instance_status(
    challenge_id: int,
    service: ChallengeService = Depends(ChallengeService),
):
    chall_status = service.get_challenge_status(challenge_id)
    return APIResponse.as_json(
        code=status.HTTP_200_OK,
        status="Instance status retrieved successfully",
        data=chall_status,
    )


@router.get("/{challenge_id}/kick")
async def kick_user(
    challenge_id: int,
    email: str = Query(..., title="Email of the user to kick"),
    service: ChallengeService = Depends(ChallengeService),
):
    if not service._user or not service._user.is_admin:
        return APIResponse.as_json(
            code=status.HTTP_403_FORBIDDEN, status="You are not allowed to kick user"
        )
    remain_users = service.kick_user(challenge_id, email)
    return APIResponse.as_json(
        code=status.HTTP_200_OK,
        status="User kicked successfully",
        data=remain_users,
    )


@router.get("/{challenge_id}/kick_all")
async def kick_all(
    challenge_id: int,
    service: ChallengeService = Depends(ChallengeService),
):
    if not service._user or not service._user.is_admin:
        return APIResponse.as_json(
            code=status.HTTP_403_FORBIDDEN, status="You are not allowed to kick user"
        )
    success = service.kick_all(challenge_id)
    return APIResponse.as_json(
        code=status.HTTP_200_OK,
        status="All users kicked successfully" if success else "No users to kick",
    )


@router.post("/join")
async def request_join_instance(
    instance: InstanceRequest,
    service: ChallengeService = Depends(ChallengeService),
):
    join_status = service.join_challenge(instance.challenge_id)
    return APIResponse.as_json(
        code=status.HTTP_200_OK,
        status=(
            "Joined challenge successfully"
            if join_status
            else "Already joined challenge"
        ),
    )


@router.post("/leave")
async def request_stop_instance(
    instance: InstanceRequest,
    service: ChallengeService = Depends(ChallengeService),
):
    leave_status = service.leave_challenge(instance.challenge_id)
    return APIResponse.as_json(
        code=status.HTTP_200_OK,
        status=(
            "Left challenge successfully" if leave_status else "Already left challenge"
        ),
    )


@router.delete("/{challenge_id}")
async def delete_challenge(
    challenge_id: int,
    service: ChallengeService = Depends(ChallengeService),
):
    # Check if user is admin or bot
    if not service._user or (service._user.id != "bot" and not service._user.is_admin):
        return APIResponse.as_json(
            code=status.HTTP_403_FORBIDDEN, 
            status="You are not allowed to delete challenges"
        )
    
    success = service.delete_challenge(challenge_id)
    return APIResponse.as_json(
        code=status.HTTP_200_OK if success else status.HTTP_404_NOT_FOUND,
        status="Challenge deleted successfully" if success else "Challenge not found",
    )


@router.get("/list")
async def list_challenges(
    page: int,
    service: ChallengeService = Depends(ChallengeService),
):
    challenges = service.list_challenges(page)
    return APIResponse.as_json(
        code=status.HTTP_200_OK,
        status="Challenges retrieved successfully",
        data=challenges,
    )
