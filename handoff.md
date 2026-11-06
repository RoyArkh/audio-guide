# Handoff: Virtual Audioguide

This file summarizes a planning conversation held in claude.ai. It records the project idea, the decisions made so far, the server that is already set up, what v1 should include, and a step-by-step plan. Read it fully before starting work.

## About the developer

- Roya is building this as a **side project to learn**, not as a production business. Prefer simple, well-known tools, and briefly explain new concepts (Docker networking, Caddy, PostGIS queries, and so on) the first time they come up.
- Local machine: macOS, with Docker Desktop available. Claude Code can use Docker locally.
- Ask before adding major dependencies or new services. Never commit secrets.

## Product idea

A website (later also an iOS/Android app) that works as a virtual audio guide anywhere in the world:

1. The user opens the site and is asked for location permission.
2. The user picks a **story length** (short / medium / long) and a **mood**:
   - **Historical**: facts only.
   - **Historical + emotional**: facts, fun facts, light jokes, and some deeper, moving descriptions.
   - **Romantic**: fun facts and romantic stories or legends.
3. The backend checks whether the user is at or near a well-known place.
4. An AI pipeline researches the place online, writes a story script that matches the preferences, and converts it to audio with a cheap TTS service.
5. The user gets a short podcast-style audio file to listen to on the spot.
6. If the user isn't at a famous place, the pipeline looks for local stories about the area, or tells the story of the nearest notable place instead (and says so).

### Later features (not in v1)

- **Caching:** popular places get requested often. Store generated scripts and audio, and serve them again instead of re-running the AI pipeline. Cache key: `place_id + length + mood + language`, not raw GPS coordinates. Store the script separately from the audio so voices can change without new LLM calls.
- **Trusted sources:** admins can add information from trusted sources linked to a geographic area (a point plus radius, or a polygon). When a story is generated for a nearby place, matching entries are pulled in with PostGIS (`ST_DWithin` / `ST_Intersects`) and, optionally, pgvector similarity search. Adding a new trusted entry should mark cached episodes in that area as outdated.
- **Mobile apps** (Expo, iOS + Android) sharing the same backend.
- **User accounts.**

## Tech stack decisions

| Area | Choice | Notes |
|---|---|---|
| Frontend | **Expo (React Native) + Expo Router** | Web first. The same codebase targets iOS/Android later. The web build is exported as static files and served by Caddy, or by Cloudflare Pages as a free alternative. |
| Backend API | **Python + FastAPI** | One API for web and mobile. |
| Database | **PostgreSQL + PostGIS + pgvector** | Self-hosted in Docker. PostGIS handles "nearby" queries; pgvector is for later semantic search. |
| Background jobs | **v1: FastAPI background tasks + a `jobs` table in Postgres.** Later: Celery + Redis | Celery + Redis was deferred to save RAM on the 1 GB server and keep v1 simple. Roya wants to learn Celery + Redis later. |
| Reverse proxy / HTTPS | **Caddy** | Automatic Let's Encrypt certificates. The only container that publishes ports (80/443). |
| Audio storage | **Cloudflare R2** | Free tier: 10 GB-month storage, 1M write operations, 10M read operations, no egress fees. Use a storage abstraction: local folder in dev, R2 in prod. |
| Domain / DNS | **`audioguide.royaarkh.com`** | `royaarkh.com` is Roya's personal site, hosted on Netlify, with DNS managed at Porkbun. The subdomain is a plain `A` record at Porkbun pointing to `198.44.107.7`; the main site on Netlify is unaffected. Never add the subdomain under Netlify's domain management, or Netlify will try to serve it. Backup option: `freyacademy.org` (also at Porkbun, unused). |
| LLM | **Gemini API**, `gemini-3.1-flash-lite` | Free on Gemini's free tier; paid is $0.25 / $1.50 per 1M input/output tokens (Nov 2026). Keep it provider-agnostic: Gemini offers an OpenAI-compatible endpoint, so use an OpenAI-compatible client with base URL, API key, and model name in env vars. That lets local Ollama (dev) or OpenAI (GPT-5 mini/nano) be swapped in without code changes. |
| TTS | **Gemini API**, `gemini-3.8-flash-lite-tts` | Free on the free tier. Paid: $0.0015 per 10 s of audio through Dec 31, 2026, then $0.003 from Jan 1, 2027 (about 4.5¢, later about 9¢, per 5-minute story). TTS isn't OpenAI-compatible, so put it behind a small `TTSProvider` interface (fallback option: OpenAI `gpt-4o-mini-tts`, ~$0.015/min). Self-hosted TTS was ruled out for the 1 GB server. Split long scripts by paragraphs and join the audio afterwards (ffmpeg / pydub). |
| Place discovery | **Wikipedia GeoSearch API + Wikidata** (free) | Google Places is a possible later fallback. |
| Web research | Wikipedia content, plus **Gemini's Grounding with Google Search** | Not available through the API on the free tier (only testable in Google AI Studio). Once billing is enabled, the first 5,000 search requests per month are free, then $14 per 1,000. So in development, research from Wikipedia/Wikidata only, and make grounding a config flag that's turned on with the paid tier. A separate search API (Tavily, Brave, Exa) is only a fallback if grounding isn't good enough. |

**Rejected or deferred:**
- Supabase: cost concerns, the free tier pauses after 7 days idle, and it doesn't host the Python worker anyway.
- Coolify: needs 2 cores / 2 GB just for itself; plain Docker Compose is used instead.
- vLLM / local LLM on the server: there's no GPU and too little RAM. Local models can be explored with Ollama on the Mac.
- Hostinger VPS: only worth it if it could run vLLM properly, which it can't.

## Server: already set up

**Provider:** RackNerd, "1 GB KVM VPS Special", $21.99/year (renews 11/03/2027), New York location.

| Item | Value |
|---|---|
| IP | `198.44.107.7` |
| Hostname | `racknerd-768801f` |
| OS | Ubuntu 24.04.5 LTS (kernel 6.8.0-147-generic) |
| CPU / RAM | 1 vCPU / 1 GB RAM (~961 MiB usable) |
| Disk | 20 GB SSD (18.6 GB usable, ~30% used after Docker install) |
| Bandwidth | 3,000 GB/month |
| Control panel | https://ctrl.racknerd.com/ (username `vmuser380874`). Has a VNC console as a fallback if SSH breaks. |

**Completed setup steps:**
1. System fully updated and rebooted onto the new kernel.
2. Admin user `roya` created and added to the `sudo` group.
3. SSH key login set up from the Mac (existing `~/.ssh/id_ed25519`).
4. SSH locked down in `/etc/ssh/sshd_config.d/00-hardening.conf`: `PermitRootLogin no`, `PasswordAuthentication no`, `KbdInteractiveAuthentication no`. Verified: root login returns `Permission denied (publickey)`.
5. Firewall (ufw) enabled, allowing only OpenSSH, 80/tcp, and 443/tcp (IPv4 and IPv6).
6. Automatic security updates on (`unattended-upgrades`, both periodic settings `"1"`).
7. Swap: 2 GB `/swapfile` added (persisted in `/etc/fstab`) on top of an existing ~1 GB, so 3 GB total. `vm.swappiness=10` set in `/etc/sysctl.d/99-swappiness.conf`.
8. Docker installed via get.docker.com. `roya` is in the `docker` group. `hello-world` works. Docker Compose v5.7.0.

Connect with: `ssh roya@198.44.107.7`

**Open admin items:**
- [x] RackNerd account email typo fixed.
- [ ] Make sure the root password was changed (`sudo passwd root`), since the original credentials went to the wrong email. SSH root login is disabled anyway, but the ctrl panel's VNC console still uses it.
- [ ] Add a DNS `A` record at Porkbun: `audioguide.royaarkh.com` → `198.44.107.7` (DNS-only). Caddy needs this for HTTPS. Do it before M6 so DNS has time to update.
- [ ] Create a Cloudflare R2 bucket and API token.
- [ ] Create a Gemini API key in Google AI Studio (free tier) and put it in `.env` as `GEMINI_API_KEY`. One key covers both text and TTS.
- [ ] Later, before real users: enable billing (paid tier) for higher rate limits, Google Search grounding, and to keep prompts out of Google's training data. On the free tier, prompts may be used to improve Google's products, which is acceptable for public place information.
- [ ] Ignore the "Ubuntu 26.04 available" message; stay on 24.04 LTS.

### Rules for running on this server

- **Docker ignores ufw.** Any port published in Compose (`ports:`) is open to the internet even though ufw doesn't allow it. Only Caddy publishes ports (80, 443). Postgres must have **no `ports:` entry** in production and is reached by service name on the internal Docker network. If local access is needed for debugging, bind to `127.0.0.1:` only.
- **1 GB RAM is tight.** Tune Postgres down (e.g. `shared_buffers=128MB`, low `max_connections`), run a single API worker process, and keep only one story generation running at a time. Set memory limits in Compose.
- **Disk is small (~18 GB).** Run `docker system prune` periodically. Later, build images in GitHub Actions and push them to a registry (e.g. GHCR) so the server only downloads them instead of building.
- **Backups:** nightly `pg_dump` uploaded to R2 once real data exists.
- Browsers only allow location access over HTTPS (`localhost` is exempt during dev).

## v1 scope

**In:**
- Web app only (Expo web build). No login, no accounts.
- Location permission flow, with a clear message if the user denies it. A manual "pick a spot on a map / enter coordinates" fallback is a nice-to-have.
- Preference picker: length and mood.
- Pipeline: coordinates → find nearest notable place → research → script → TTS → audio file → playable in the browser.
- A progress indicator while the job runs (poll job status).
- Show the place name, the transcript, and a short list of sources under the player. Wikipedia content is CC BY-SA, so attribution is needed.
- Deployed on the RackNerd server behind Caddy with HTTPS.

**Out (post-v1):** caching (stretch goal for v1 if time allows, since it's simple), trusted sources, Celery + Redis, mobile apps, accounts, embeddings, multiple languages.

### Suggested length targets (about 150 spoken words per minute, adjustable)

| Length | Duration | Script words |
|---|---|---|
| Short | ~2 min | ~300 |
| Medium | ~5 min | ~750 |
| Long | ~10 min | ~1,500 |

### Content rules for the script-writing prompt

- Only state facts supported by the collected sources. Don't invent dates, names, or numbers.
- Clearly mark legends and folklore as such (important for the "romantic" mood).
- When falling back to a nearby place, say so in the story ("You're about 400 m from…").
- Write for the ear: short sentences, no lists or headings, natural transitions.

## Proposed architecture for v1

```
Browser (Expo web)
   │  HTTPS
   ▼
Caddy ──► static web build
   │
   └──► FastAPI (/api/*)
            │  writes job row, starts background task
            ▼
        Pipeline: place lookup → research → script (LLM) → TTS → upload
            │                                   │
            ▼                                   ▼
        Postgres (PostGIS)                Cloudflare R2 (audio)
```

### API sketch

- `POST /api/stories` with body `{ lat, lng, length, mood }` → `{ job_id }`
- `GET /api/stories/{job_id}` → `{ status, place, transcript, audio_url, sources, error }`
  - `status`: `pending → finding_place → researching → writing → generating_audio → done | failed`
- `GET /api/health`

### Data model sketch

- `places`: id, name, wikidata_id / wikipedia_page_id, `geom geography(Point, 4326)`, summary, timestamps.
- `jobs`: id, lat, lng, length, mood, status, error, place_id, episode_id, timestamps.
- `episodes`: id, place_id, length, mood, language, script_text, sources (jsonb), audio_key, duration_seconds, timestamps. Already shaped so it can be used for caching later.
- Later: `trusted_sources`: id, title, content, source_url, `area geography`, embedding `vector`, timestamps.

Use Alembic for migrations.

### Suggested repo layout

```
audio-guide/
├── backend/            # FastAPI app, pipeline, Alembic migrations, Dockerfile
├── web/                # Expo app (web first)
├── docker-compose.yml        # local dev
├── docker-compose.prod.yml   # server
├── Caddyfile
├── .env.example
└── handoff.md
```

## Plan

Each milestone should end in something runnable that Roya can try.

1. **M0: Scaffolding.** Repo layout, `docker-compose.yml` with Postgres (PostGIS + pgvector image) and FastAPI with hot reload, `.env.example`, `/api/health`. Verify everything runs locally with `docker compose up`.
2. **M1: Place discovery.** Endpoint or service that takes coordinates and returns nearby notable places using Wikipedia GeoSearch (plus Wikidata details). Store places in PostGIS. Handle the "nothing famous nearby" fallback (expand the radius, pick the nearest).
3. **M2: Research + script.** Gather Wikipedia/Wikidata extracts (plus Google Search grounding when enabled), have Gemini Flash-Lite extract key facts, then write the script for the chosen length and mood. Provider-agnostic LLM client configured through env vars. Expect free-tier rate limits: add retries with backoff on 429 errors.
4. **M3: TTS + storage.** Chunk the script, call Gemini TTS through the `TTSProvider` interface (check the current docs for the response audio format; it may need converting to MP3 with ffmpeg), join into one MP3 (~64 kbps mono is fine for voice), and save it through a storage abstraction (local folder in dev, R2 in prod).
5. **M4: Job flow.** `POST /api/stories` plus polling, with job status updates through the pipeline stages and error handling.
6. **M5: Expo web UI.** Location permission → preferences → progress → audio player with transcript and sources.
7. **M6: Deploy.** Point `audioguide.royaarkh.com` at the server, write `docker-compose.prod.yml` and the Caddyfile for that domain, move the env vars to the server, deploy, and test on a phone over HTTPS. Add a nightly `pg_dump` backup to R2.
8. **M7 (stretch): Caching.** Reuse existing episodes for the same place, length, mood, and language.

**After v1:** trusted sources (PostGIS area queries + pgvector), Celery + Redis, a GitHub Actions build-and-deploy pipeline, Expo iOS/Android builds, accounts.
