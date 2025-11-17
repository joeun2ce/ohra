import asyncio
import argparse
import logging
from datetime import datetime, timedelta, timezone
from ohra.workers.sync.scripts import confluence, jira

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def sync_job(source: str, last_sync_time: datetime):
    if source == "confluence":
        await confluence.main(last_sync_time=last_sync_time)
    elif source == "jira":
        await jira.main(last_sync_time=last_sync_time)
    elif source == "all":
        confluence_result = await confluence.main(last_sync_time=last_sync_time)
        jira_result = await jira.main(last_sync_time=last_sync_time)

        confluence_vectors = confluence_result[2] if confluence_result else 0
        jira_vectors = jira_result[2] if jira_result else 0
        total_vectors = confluence_vectors + jira_vectors

        logger.info(f"{total_vectors} vectors stored (confluence: {confluence_vectors}, jira: {jira_vectors})")


async def main():
    parser = argparse.ArgumentParser(description="OHRA document sync worker")
    parser.add_argument("source", choices=["confluence", "jira", "all"], help="Source to sync")
    parser.add_argument(
        "--since",
        type=str,
        help="Sync documents updated since this date (YYYY-MM-DD). Default: 24 hours ago",
        default=None,
    )
    parser.add_argument(
        "--schedule",
        type=int,
        help="Run periodically every N hours. Default: run once and exit",
        default=None,
    )

    args = parser.parse_args()

    if args.since:
        try:
            last_sync_time = datetime.strptime(args.since, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            logger.error(f"Invalid date format: {args.since}. Use YYYY-MM-DD")
            return
    else:
        last_sync_time = datetime.now(timezone.utc) - timedelta(hours=24)

    logger.info(f"Syncing documents updated since: {last_sync_time}")

    if args.schedule:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        async def scheduled_job():
            sync_time = datetime.now(timezone.utc) - timedelta(hours=24)
            logger.info(f"Scheduled sync: documents updated since {sync_time}")
            await sync_job(args.source, sync_time)

        scheduler = AsyncIOScheduler()
        scheduler.add_job(scheduled_job, "interval", hours=args.schedule)
        scheduler.start()
        logger.info(f"Scheduler started. Running every {args.schedule} hours.")

        try:
            await scheduled_job()
            while True:
                await asyncio.sleep(3600)
        except KeyboardInterrupt:
            logger.info("Shutting down scheduler...")
            scheduler.shutdown()
    else:
        await sync_job(args.source, last_sync_time)


if __name__ == "__main__":
    asyncio.run(main())
