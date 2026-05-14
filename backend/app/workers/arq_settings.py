"""arq worker entrypoint registering scheduled jobs."""

from arq.connections import RedisSettings
from arq.cron import cron

from app.core.config import get_settings
from app.workers.directory_sync import sync_staff_directory
from app.workers.hubspot import run_pending_hubspot_jobs
from app.workers.notify import run_pending_host_emails
from app.workers.retention import retention_cleanup


async def _staff_directory_job(ctx: dict) -> int:  # noqa: ARG001
    return await sync_staff_directory()


async def _host_email_job(ctx: dict) -> int:  # noqa: ARG001
    return await run_pending_host_emails()


async def _hubspot_job(ctx: dict) -> int:  # noqa: ARG001
    return await run_pending_hubspot_jobs()


async def _retention_job(ctx: dict) -> dict[str, int]:  # noqa: ARG001
    return await retention_cleanup()


def _redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(get_settings().redis_url)


class WorkerSettings:
    redis_settings = _redis_settings()
    functions = [
        _staff_directory_job,
        _host_email_job,
        _hubspot_job,
        _retention_job,
    ]
    cron_jobs = [
        cron(_staff_directory_job, hour={6, 18}, minute=0),
        cron(_host_email_job, minute=set(range(0, 60, 2))),
        cron(_hubspot_job, minute=set(range(0, 60, 5))),
        cron(_retention_job, hour=3, minute=15),
    ]
