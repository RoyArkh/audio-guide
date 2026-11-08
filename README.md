# audio-guide

A virtual audio guide: share your location, pick a story length and mood, and get a short podcast-style story about the place you're standing in. See [handoff.md](handoff.md) for the full plan.

## Local development

Requirements: Docker Desktop. [uv](https://docs.astral.sh/uv/) is optional and only needed for managing Python dependencies.

```sh
cp .env.example .env          # first time only
docker compose up --build     # starts Postgres + the API with hot reload
```

- API health: http://localhost:8000/api/health
- Interactive API docs: http://localhost:8000/api/docs
- Nearest notable place: http://localhost:8000/api/places/nearby?lat=48.8556&lng=2.2986
- **Make a story:** `POST /api/stories` with `{lat, lng, length, mood}` returns a `job_id`. Then poll `GET /api/stories/{job_id}` until `status` is `done` (with transcript, audio URL, and sources) or `failed` (with `error`). It needs `LLM_API_KEY` and `TTS_API_KEY` in `.env`: one free Gemini key from Google AI Studio works for both. After editing `.env`, run `docker compose up -d` so the container picks it up.
- Single pipeline steps, for trying out prompts and voices (only when `APP_ENV=dev`): `POST /api/scripts` writes a script, and `POST /api/audio` speaks a script. MP3s are saved in `backend/media/` and served at `/api/media/...`.
- Postgres (for psql / GUI tools): `localhost:5433`, with the user, password, and DB from `.env`

Migrations run automatically when the API container starts.

### Common commands

```sh
docker compose exec api pytest                          # run tests
docker compose exec db psql -U audioguide -d audioguide # SQL shell
docker compose exec api alembic revision --autogenerate -m "add places"  # new migration
docker compose exec api alembic upgrade head            # apply migrations
docker compose down          # stop (data is kept in the pgdata volume)
docker compose down -v       # stop AND delete the database
```

### Adding Python dependencies

```sh
cd backend
uv add some-package          # or: uv add --dev some-package
docker compose up --build    # rebuild the API image with the new lockfile
```

## Layout

```
backend/     FastAPI app (app/), Alembic migrations (migrations/), tests, Dockerfile
db/          Postgres image with PostGIS + pgvector
docker-compose.yml   local dev stack
```
