from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from repository.challenge import ChallengeRepository
from repository import Storage
from worker import clean_challenge
import logging

log = logging.getLogger(__name__)


def delete_joined_users():
    storage = next(Storage.get())
    challenge_repo = ChallengeRepository(storage)
    need_removes = challenge_repo.fetch_user_join(15)
    log.info(f"Need remove: {need_removes}")
    for need_remove in need_removes:
        remain_players = challenge_repo.remove_user(
            need_remove["challenge_id"], need_remove["user_id"]
        )
        if len(remain_players) == 0:
            clean_challenge.delay(need_remove["challenge_id"])
            log.debug(f"Challenge {need_remove['challenge_id']} cleaned")
        log.info(
            f"User {need_remove['user_id']} removed from {need_remove['challenge_id']}"
        )


scheduler = BackgroundScheduler()
# crate job run every 30 minutes
scheduler.add_job(
    delete_joined_users,
    trigger=IntervalTrigger(minutes=15),
    id="delete_joined_users",
    name="Delete joined users",
)
