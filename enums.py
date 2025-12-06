from enum import Enum


class ClientStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


class SchedulerStatus(Enum):
    PENDING = "PENDING"
    LEASED = "LEASED"
    COMPLETED = "COMPLETED"
    DEAD = "DEAD"


SCHEDULER_TO_CLIENT_STATUS = {
    SchedulerStatus.PENDING.value: ClientStatus.PENDING.value,
    SchedulerStatus.LEASED.value: ClientStatus.RUNNING.value,
    SchedulerStatus.COMPLETED.value: ClientStatus.DONE.value,
    SchedulerStatus.DEAD.value: ClientStatus.FAILED.value,
}


def get_client_status(scheduler_status: str) -> str:
    return SCHEDULER_TO_CLIENT_STATUS.get(scheduler_status, scheduler_status)
