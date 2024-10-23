import os
from celery import Celery
from redis import Redis

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_TIMEZONE = os.getenv('CELERY_TIMEZONE', 'UTC')
CELERY_SCHEDULE = float(os.getenv('CELERY_SCHEDULE', '30.0'))


redis_host = os.getenv('REDIS_HOST', 'redis')
redis_port = int(os.getenv('REDIS_PORT', '6379'))
redis_db = int(os.getenv('REDIS_DB', '0'))

celery_app = Celery('bet-maker', broker=CELERY_BROKER_URL)

celery_app.conf.timezone = CELERY_TIMEZONE


celery_app.conf.task_queues = {
    'bets': {
        'exchange': 'bets',
        'routing_key': 'bets',
    },
}


async def get_redis_client() -> Redis:
    redis_client = Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
    try:
        yield redis_client
    finally:
        redis_client.close()


@celery_app.task(queue='bets')
def create_bet_task():
    pass
