"""
# ---------------------------------------------------------------------
# scheduler_job.py
# app/services/scheduler/scheduler_job.py
# APScheduler job runner for Grylli (periodic task scheduling)
# ---------------------------------------------------------------------
"""

from datetime import timedelta

# ------------------------ Imports (PEP8 order) -----------------------
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.services.scheduler.scheduler import (
    create_daily_backup,
    execute_due_reminders,
    process_checkins_and_overdue_actions,
)
from app.utils.logging import log_info_message


# ---------------------------------------------------------------------
# start_scheduler
# ---------------------------------------------------------------------
def start_scheduler(app):
    """
    Initialize and start the APScheduler with background jobs for Grylli.

    Sets up:
        - A periodic task to process check-ins and overdue actions.
        - A daily backup task for the database.

    Args:
        app (Flask): The Flask application instance (provides context/config).
    """
    scheduler = BackgroundScheduler()

    # Wrapper for check-in/reminder/overdue logic (runs with app context)
    def task_wrapper():
        with app.app_context():
            log_info_message("🌀 APScheduler processing check-in reminders and overdue actions...")
            process_checkins_and_overdue_actions()

    # Wrapper for daily backup logic (runs with app context)
    def backup_wrapper():
        with app.app_context():
            log_info_message("📦 Running daily backup...")
            create_daily_backup()

    # Wrapper for reminder
    def reminder_wrapper():
        with app.app_context():
            log_info_message("⏰ APScheduler executing due reminders...")
            execute_due_reminders()

    # Get schedule settings from app config
    checkin_minutes = app.config.get("SCHEDULER_CHECKIN_INTERVAL_MINUTES", 1)
    backup_hour = app.config.get("SCHEDULER_BACKUP_CRON_HOUR", 2)
    backup_minute = app.config.get("SCHEDULER_BACKUP_CRON_MINUTE", 0)

    # Schedule the check-in/reminder/overdue job
    scheduler.add_job(
        task_wrapper,
        trigger=IntervalTrigger(minutes=checkin_minutes),
        id="process_checkins_and_overdue_actions",
        name="Process check-in reminders and execute overdue actions",
        replace_existing=True,
    )

    # Schedule the daily backup job
    scheduler.add_job(
        backup_wrapper,
        trigger=CronTrigger(hour=backup_hour, minute=backup_minute),
        id="daily_backup_job",
        name="Create daily Grylli DB backup",
        replace_existing=True,
    )

    reminder_interval = app.config.get(
        "SCHEDULER_REMINDER_INTERVAL_MINUTES", 5
    )  # or your preferred default

    scheduler.add_job(
        reminder_wrapper,
        trigger=IntervalTrigger(minutes=reminder_interval),
        id="execute_due_reminders",
        name="Execute scheduled reminders",
        replace_existing=True,
    )

    scheduler.start()
    log_info_message("✅ APScheduler started.")
