import json
import os
import datetime
import random
from datetime import timezone

from fastapi import Depends, HTTPException, FastAPI
from fastapi.responses import JSONResponse
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from redis import Redis

from app import get_session, init_db
from app import Bet, User, BetState
from app import BetCreateSchema, UserCreateSchema, UserSchema,  BetsListSchema, EventsListSchema, EventSchema, EventState

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


@app.get("/events", response_model=EventsListSchema)
async def get_events(
        redis_client: Redis = Depends(get_redis_client)
):
    events_keys = redis_client.keys(f'provider-event:*')
    events = []
    for key in events_keys:
        event_data = json.loads(redis_client.get(key))
        events.append(EventSchema(**event_data))
    return EventsListSchema(events=events)


@app.post("/create_user", response_model=UserCreateSchema)
async def create_user(
        user: UserSchema,
        session: AsyncSession = Depends(get_session)
):

    command = select(User).where(User.email == user.email)
    request = await session.execute(command)
    new_user = request.scalars().first()
    if new_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(username=user.username, email=user.email, hashed_password=user.hashed_password)
    # new_user.set_password(user.password)

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return UserCreateSchema(**new_user.dict())


@app.get('/bets', response_model=BetsListSchema)
async def get_bets(
        user_id: int,
        session: AsyncSession = Depends(get_session),
        redis_client: Redis = Depends(get_redis_client)
):
    command = select(Bet).where(Bet.user_id == user_id)
    request = await session.execute(command)
    bets = request.scalars().all()
    if not bets:
        return JSONResponse(status_code=204, content={"message": "no bets"})

    result = []
    for bet in bets:
        bet_uuid = str(bet.event_uuid)
        event_data_json = redis_client.get(f'provider-event:{bet_uuid}')
        if event_data_json:
            event_data = json.loads(event_data_json)
            if (
                    event_data['state'] != EventState.not_completed
                    and bet.state == BetState.not_completed
            ):
                choices = [BetState.won, BetState.lost]
                new_state = random.choice(choices)
                bet.state = new_state
                session.add(bet)
                await session.commit()
        result.append(bet.dict())

    return BetsListSchema(bets=result)


@app.post('/bet', response_model=BetCreateSchema)
async def create_bet(
        bet_schema: BetCreateSchema,
        session: AsyncSession = Depends(get_session),
        redis_client: Redis = Depends(get_redis_client)
):
    bet_schema = bet_schema.dict()
    event_data = redis_client.get(f'provider-event:{bet_schema["event_uuid"]}')
    if not event_data:
        return JSONResponse(status_code=204, content={"message": "Event not found"})

    event_data = json.loads(event_data)

    if datetime.datetime.strptime(
            event_data['expiration_time'], "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=timezone.utc) < datetime.datetime.now(timezone.utc):
        return JSONResponse(status_code=400, content={"message": "Event has expired"})

    if event_data['state'] != EventState.not_completed:
        return JSONResponse(status_code=400, content={"message": "Event is already completed"})

    bet_schema['odds'] = event_data['coefficient']

    bet = Bet(**bet_schema)
    print(f'bet is {bet}')
    session.add(bet)
    await session.commit()
    await session.refresh(bet)
    print(bet.dict())
    return BetCreateSchema(**bet.dict())


@app.get("/ping")
async def pong():
    await init_db()
    return {"ping": "pong!"}
