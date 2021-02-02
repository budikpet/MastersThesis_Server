from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
from rq import Queue
from .worker import conn
from scrapers.zoo_scraper import run_test_job

import logging

# Set logging to DEBUG which prints additional information
logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)

q = Queue(connection=conn)


def add_web_scraping_job(interval_time: int):
    print(
        f'JOB EXECUTED: This job is run every {interval_time}. Current time is: {datetime.now()}')
    # TODO: If no internet connection then reschedule here or in zoo_scraper
    result = q.enqueue(run_test_job)


def main():
    sched = BlockingScheduler()

    # misfire_grace_time=None should make it certain that the job isn't discarted if scheduled execution is missed
    sched.add_job(add_web_scraping_job, args=[
                  'day at 22:00'], trigger='cron', minute=0, hour=2, misfire_grace_time=None)
    sched.add_job(add_web_scraping_job, args=['last day of the month at 22:00'],
                  trigger='cron', day='last', minute=0, hour=2, misfire_grace_time=None)
    sched.add_job(add_web_scraping_job, args=[
                  '45 minutes'], trigger='interval', minutes=45)
    # sched.add_job(add_web_scraping_job, args = ['1 minute'], trigger='interval', minutes=1)

    print("Jobs scheduled.")
    sched.start()
