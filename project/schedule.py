import atexit
from apscheduler.schedulers.background import BackgroundScheduler

INTERVAL_SECONDS = 3600  # 1 HORA


def scheduler_run():
    from .gdrive import gdrive_backup_database, gdrive_clean_backups
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=gdrive_backup_database, trigger="interval", seconds=INTERVAL_SECONDS)
    scheduler.add_job(func=gdrive_clean_backups, trigger="interval", seconds=INTERVAL_SECONDS + 5)
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
