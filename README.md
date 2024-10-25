# FastAPI + SQLModel + Alembic + PostgreSQL + redis + Celery

# Запуск проекта
```sh
$ cp example.env .env
```
 - скопирует окружение для контейнеров(по умолчанию работает)

если есть желание что-то поменять для postgres - то потом надо будет пойти в alembic.ini и поменять там урл
(пытался переобъявлять его в env.py, но из-за этого не создавались миграции)

```sh
$ docker-compose up -d --build
```
 - собираем и поднимаем контейнеры

```sh
$ docker-compose exec web alembic upgrade head
```
 - применяем миграции


## Ход работы:

- накидал жирными мазками сервисы на fast-api
- завернул в докер
- прикрутил postgres
- ооочень долго прикручивал alembic, тк пришлось прикручивать асинхронность, и переписывать alembic(миграции с FK так и не победил, решил не тратить много времени и просто оставил вместо FK связь через user_id:int)
- прикрутил редис, селери
- докинул бизнес-логику и в процессе понял, что надо было rabbit использовать, но переписывать и покрывать тестами не стал, тк итак много времени потратил на переписывание alembic
- так же из-за несовместимости библиотеки шифрования не стал реализовывать авторизацию, токены и тп, тк не хотел тратить еще больше времени :)




