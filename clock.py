from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
from rq import Queue
from worker import conn
import zoo_scrapper

import logging
logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)

q = Queue(connection=conn)
sched = BlockingScheduler()

@sched.scheduled_job('interval', minutes=1)
def timed_job():
	print(f'JOB EXECUTED: This job is run every minute. Current time is: {datetime.now()}')
	result = q.enqueue(zoo_scrapper.run_test_job)
	print(f'POST JOB: {result}')

@sched.scheduled_job('interval', minutes=45)
def timed_job():
	print(f'JOB EXECUTED: This job is run every 45 minute. Current time is: {datetime.now()}')

@sched.scheduled_job('cron', minute=0, hour=2)
def scheduled_job():
	print('JOB EXECUTED: This job is run every day at 22:00.')

@sched.scheduled_job('cron', day = 'last', minute=0, hour=22, misfire_grace_time=None)
def scheduled_job():
	"""
	misfire_grace_time=None should make it certain that the job isn't discarted if scheduled execution is missed
	"""
	print('JOB EXECUTED: This job is run on a last day of the month at 21:00.')

sched.start()