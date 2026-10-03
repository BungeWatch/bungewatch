import logging
from uuid import UUID
from arq.connections import RedisSettings

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.pipeline.summarize import run_summarization_for_bill

logger = logging.getLogger("bungewatch.worker")


async def summarize_bill_job(ctx, bill_id: str) -> str | None:
    """
    Thin wrapper: open a session, delegate entirely to run_summarization_for_bill.
    No chunking logic, no AI-calling logic here anymore — if that ever
    needs to change, it changes in exactly one place (summarize.py).
    """
    async with AsyncSessionLocal() as db:
        summary_id = await run_summarization_for_bill(db, UUID(bill_id))
        return str(summary_id) if summary_id else None


class WorkerSettings:
    functions = [summarize_bill_job]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_tries = 3
    job_timeout = 120