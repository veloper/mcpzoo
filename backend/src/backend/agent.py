"""Scheduler agent for background jobs."""
import logging, time

import schedule

from src.backend.jobs import SnapshotSystemCleanupJob, SnapshotSystemJob


# ===============
# Configuration
# ===============

logging.basicConfig()
schedule_logger = logging.getLogger('schedule')
schedule_logger.setLevel(level=logging.INFO)

# ==============
# Scheduling
# ==============

schedule.every(5).seconds.do(SnapshotSystemJob.execute)
schedule.every(5).minutes.do(SnapshotSystemCleanupJob.execute)

# ==============
# Scheduler Loop
# ==============
if __name__ == "__main__":
    print("Starting scheduler agent...")
    while True:
        schedule.run_pending()
        time.sleep(1)
