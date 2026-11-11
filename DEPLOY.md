# Deploying to the server

Production runs on the RackNerd server (`roya@198.44.107.7`) with `docker-compose.prod.yml`:

- **Caddy** serves the web app and HTTPS, and passes `/api/*` to the API. It's the only container with open ports (80/443), and it asks for a username and password before showing anything.
- **api** is FastAPI and the story pipeline. Audio goes to Cloudflare R2.
- **db** is Postgres, reachable only by the other containers.

## One-time setup

### 1. DNS (Porkbun)

In Porkbun, open `royaarkh.com` → DNS, and add a record:

| Type | Host | Answer |
|---|---|---|
| A | `audioguide` | `198.44.107.7` |

Check it on the Mac with `dig +short audioguide.royaarkh.com`. Once it prints `198.44.107.7`, it's ready. This can take from a few minutes to an hour. If it still shows `pixie.porkbun.com`, look for another record for `audioguide` (or a `*` wildcard) and remove it.

### 2. Cloudflare R2

1. Cloudflare dashboard → **R2 Object Storage** → **Create bucket**, named `audio-guide`. Leave public access off: the API gives listeners signed links that expire after a day.
2. In the bucket's **Settings** → **Object lifecycle rules**, add a rule that deletes objects with the prefix `backups/` after 30 days. That keeps a month of database backups.
3. R2 overview → **Manage API tokens** → **Create API token**, with permission **Object Read & Write**, limited to the `audio-guide` bucket. Copy the **Access Key ID** and **Secret Access Key**, because the secret is shown only once. The **Account ID** is on the R2 overview page.

### 3. The server's `.env`

```sh
ssh roya@198.44.107.7
mkdir -p ~/audio-guide && cd ~/audio-guide
cat > .env <<EOF
POSTGRES_USER=audioguide
POSTGRES_PASSWORD=$(openssl rand -hex 24)
POSTGRES_DB=audioguide
LLM_API_KEY=
TTS_API_KEY=
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET=audio-guide
SITE_USER=roya
SITE_PASSWORD_HASH=''
EOF
chmod 600 .env   # only you can read it
nano .env        # fill in the empty values; save with Ctrl+O, Enter, then Ctrl+X
```

The database password is generated randomly and never needs to be typed. The Gemini key goes into both `LLM_API_KEY` and `TTS_API_KEY`. This file never leaves the server.

### 4. The website password

The site asks for `SITE_USER` and a password, so strangers can't use up your Gemini credits. The server stores only a hash of the password, never the password itself. Make the hash on the server. It asks for the password twice:

```sh
docker run --rm -it caddy:2.11.9-alpine caddy hash-password
```

It prints something like `$2a$14$Ab...`. Copy it into `.env` **between the single quotes**, e.g. `SITE_PASSWORD_HASH='$2a$14$Ab...'`. Without the quotes Docker Compose mangles the `$` signs and the password never works. Pick a long password and keep it in a password manager.

To change it later: make a new hash, replace it in `.env`, then run `dc up -d caddy` (see `dc` below).

## Deploy

On the Mac, from the repo folder:

```sh
scripts/deploy.sh
```

It builds the web app, copies the code to the server, and rebuilds and restarts the containers. It deploys your working folder as it is, so commit first. The first run takes several minutes, because the server builds the images. Later runs are faster.

Then check it:

```sh
curl -u roya https://audioguide.royaarkh.com/api/health   # asks for the site password
```

Open https://audioguide.royaarkh.com on your phone, log in, allow location, and make a story.

## Looking around on the server

```sh
ssh roya@198.44.107.7
cd ~/audio-guide
alias dc="docker compose -f docker-compose.prod.yml"
dc ps                  # are all three containers up?
dc logs -f api         # follow the API's logs (Ctrl+C stops following)
dc logs caddy          # HTTPS certificate problems show up here
docker stats --no-stream   # memory used by each container
```

## Database backups

Try it once by hand. It should print something like `Saved backups/2026-11-08.dump (40 KB)`, and the file appears in the R2 bucket:

```sh
~/audio-guide/scripts/backup.sh
```

Then run it every night at 3:30 (server time). Open `crontab -e` and add this line:

```
30 3 * * * $HOME/audio-guide/scripts/backup.sh >> $HOME/backup.log 2>&1
```

To restore, download a `.dump` from the R2 bucket, copy it to the server (e.g. with `scp`), and run:

```sh
dc exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists' < 2026-11-08.dump
```

## When something goes wrong

- **The site doesn't load or shows a certificate error:** DNS probably isn't pointing at the server yet. `dc logs caddy` shows why; Caddy keeps retrying by itself.
- **The password is never accepted:** check that the hash in `.env` is inside single quotes, then `dc up -d caddy`.
- **502 Bad Gateway on `/api/...`:** the API container is down or restarting. Check `dc logs api`.
- **A story fails:** its error is shown in the app, and `dc logs api` has the details.
