from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
from rq import Queue
from worker import conn
import zoo_scraper

import logging

def add_web_scraping_job(interval_time: int):
	print(f'JOB EXECUTED: This job is run every {interval_time}. Current time is: {datetime.now()}')
	result = q.enqueue(zoo_scraper.run_test_job)

def main():
	# Set logging to DEBUG which prints additional information
	logging.basicConfig()
	logging.getLogger('apscheduler').setLevel(logging.DEBUG)

	q = Queue(connection=conn)
	sched = BlockingScheduler()

	# misfire_grace_time=None should make it certain that the job isn't discarted if scheduled execution is missed
	sched.add_job(add_web_scraping_job, args = ['day at 22:00'] 'cron', minute=0, hour=2, misfire_grace_time=None)
	sched.add_job(add_web_scraping_job, args = ['last day of the month at 22:00'] 'cron', day='last', minute=0, hour=2, misfire_grace_time=None)
	sched.add_job(add_web_scraping_job, args = ['45 minutes'] 'interval', minutes=45)

	sched.start()