import datetime
import os
import json
import random
from uuid import uuid4
from datetime import timezone

from redis import Redis
from celery import Celery

from schemas import EventState

redis_host = os.getenv('REDIS_HOST', 'redis')
redis_port = int(os.getenv('REDIS_PORT', '6379'))
redis_db = int(os.getenv('REDIS_DB', '0'))
redis_expiration_key_time = int(os.getenv('REDIS_EXPIRATION_KEY_TIME', '1800'))


CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_TIMEZONE = os.getenv('CELERY_TIMEZONE', 'UTC')
CELERY_SCHEDULE = float(os.getenv('CELERY_SCHEDULE', '30.0'))

celery_app = Celery('line-provider', broker=CELERY_BROKER_URL)

celery_app.conf.timezone = CELERY_TIMEZONE


celery_app.conf.task_queues = {
    'events': {
        'exchange': 'events',
        'routing_key': 'events',
    },
}

celery_app.conf.beat_schedule = {
    'create_event': {
        'task': 'tasks.create_event_task',
        'schedule': CELERY_SCHEDULE,
    },
    'process_events': {
        'task': 'tasks.process_events',
        'schedule': CELERY_SCHEDULE,
    },
}


def get_redis_client() -> Redis:
    redis_client = Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
    try:
        return redis_client
    finally:
        redis_client.close()


@celery_app.task(queue='events', exchange='events', name='tasks.create_event_task')
def create_event_task(event_data: dict = None):
    if not event_data:
        end_time = datetime.datetime.now(timezone.utc) + datetime.timedelta(minutes=1)
        event_data = dict(
            uuid=str(uuid4()),
            coefficient=float(1.5),
            expiration_time=end_time.strftime("%Y-%m-%d %H:%M:%S"),
            state=EventState.not_completed,
        )
    try:
        datetime.datetime.strptime(
            event_data.get('expiration_time'), "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=timezone.utc)
    except ValueError:
        return

    redis_client = get_redis_client()
    redis_client.set(
        f'provider-event:{event_data.get("uuid")}',
        json.dumps(event_data),
        ex=redis_expiration_key_time
    )


@celery_app.task(queue='events', exchange='events', name='tasks.process_events')
def process_events():
    redis_client = get_redis_client()
    events_keys = redis_client.keys(f'provider-event:*')
    for key in events_keys:
        event_data = json.loads(redis_client.get(key))
        if event_data:
            expiration_time = datetime.datetime.strptime(
                event_data.get('expiration_time'), "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=timezone.utc)

            now = datetime.datetime.now(timezone.utc)
            diff = expiration_time - now

            if diff < datetime.timedelta(seconds=10):
                choices = [EventState.first_won, EventState.second_won]
                new_state = random.choice(choices)
                event_data['state'] = new_state

                redis_client.set(
                    f'provider-event:{event_data.get("uuid")}',
                    json.dumps(event_data),
                    ex=redis_expiration_key_time
                )
