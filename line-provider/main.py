import os
import json

import datetime
from datetime import timezone

from fastapi import Depends, FastAPI
from redis import Redis

from schemas import EventSchema, EventsListSchema
from celery_app import create_event_task

app = FastAPI()
redis_host = os.getenv('REDIS_HOST', 'redis')
redis_port = int(os.getenv('REDIS_PORT', '6379'))
redis_db = int(os.getenv('REDIS_DB', '0'))


async def get_redis_client() -> Redis:
    redis_client = Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
    try:
        yield redis_client
    finally:
        redis_client.close()


@app.get("/get_events", response_model=EventsListSchema)
async def get_events(
        redis_client: Redis = Depends(get_redis_client)
):
    events_keys = redis_client.keys(f'provider-event:*')
    events = []
    for key in events_keys:
        event_data = json.loads(redis_client.get(key))
        if event_data:
            try:
                expiration_time = datetime.datetime.strptime(
                    event_data.get('expiration_time'), "%Y-%m-%d %H:%M:%S"
                ).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            now = datetime.datetime.now(timezone.utc)

            if expiration_time >= now:
                event_data['expiration_time'] = str(expiration_time - now)
                events.append(EventSchema(**event_data))

    if events:
        events = sorted(events, key=lambda x: x.expiration_time, reverse=True)

    return EventsListSchema(events=events)


@app.post("/create_event")
async def create_event(
        event: EventSchema,
):
    task = create_event_task.apply_async(queue='events', exchange='events', kwargs={'event_data': event.dict()})

    return {'task_id': task.id}



