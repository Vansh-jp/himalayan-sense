import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.core.config import settings
from app.core.database import SessionLocal
from app.services.risk_service import recalculate_all_zones_risk
from app.services.weather_service import ingest_weather_for_all_zones

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def run_weather_sync_job():
    logger.info("[Scheduler] Executing scheduled weather ingestion...")
    db = SessionLocal()
    try:
        res = ingest_weather_for_all_zones(db)
        logger.info(f"[Scheduler] Weather sync completed: {res.get('zones_updated')} zones updated.")
    except Exception as exc:
        logger.error(f"[Scheduler] Weather sync job failed: {exc}")
    finally:
        db.close()


def run_risk_recalc_job():
    logger.info("[Scheduler] Executing scheduled risk re-evaluation...")
    db = SessionLocal()
    try:
        res = recalculate_all_zones_risk(db)
        logger.info(f"[Scheduler] Risk recalculation completed: {res.get('zones_evaluated')} zones evaluated.")
    except Exception as exc:
        logger.error(f"[Scheduler] Risk recalculation job failed: {exc}")
    finally:
        db.close()


def start_scheduler():
    if not settings.ENABLE_SCHEDULER:
        logger.info("Scheduler disabled via configuration.")
        return

    interval_minutes = settings.WEATHER_SYNC_INTERVAL_MINUTES or 30

    scheduler.add_job(
        run_weather_sync_job,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="open_meteo_weather_sync",
        replace_existing=True,
    )

    scheduler.add_job(
        run_risk_recalc_job,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="himalayasense_risk_recalculation",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(f"Scheduler started with {interval_minutes}m interval.")


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler shutdown cleanly.")
