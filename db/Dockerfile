# Official Postgres image (multi-arch: works on Apple Silicon and the amd64 server)
# plus PostGIS and pgvector from the PostgreSQL apt repo that the image already
# has configured. $PG_MAJOR is set by the base image (18 here).
FROM postgres:18-trixie

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-${PG_MAJOR}-postgis-3 \
        postgresql-${PG_MAJOR}-pgvector \
    && rm -rf /var/lib/apt/lists/*
