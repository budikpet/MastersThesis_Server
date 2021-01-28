from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
import logging

logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)

sched = BlockingScheduler()

@sched.scheduled_job('interval', minutes=45)
def timed_job():
    print(f'This job is run every 45 minute. Current time is: {datetime.now()}')

# @sched.scheduled_job('cron', day_of_week='mon-fri', hour=17)
# def scheduled_job():
#     print('This job is run every weekday at 5pm.')

@sched.scheduled_job('cron', minute=0, hour=22)
def scheduled_job():
    print('This job is run every day at 22:00.')

@sched.scheduled_job('cron', day = 'last', minute=0, hour=22)
def scheduled_job():
    print('This job is run on a last day of the month at 21:00.')

sched.start()