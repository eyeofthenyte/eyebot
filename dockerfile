FROM python:3.12.13-slim-bookworm

ARG EYEBOT_VERSION=2.0.0

LABEL org.opencontainers.image.title="EyeBot" \
      org.opencontainers.image.version="${EYEBOT_VERSION}" \
      org.opencontainers.image.source="https://github.com/eyeofthenyte/eyebot"

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    EYEBOT_VERSION=${EYEBOT_VERSION}

WORKDIR /app

# The name generator executes the JavaScript race modules with Node.js.
RUN apt-get update \
    && apt-get install --no-install-recommends --yes ca-certificates nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN python -m pip install --requirement requirements.txt
RUN python -m pip check
RUN python -c "import aiohttp, atproto, cryptography, discord, facebook, feedparser, googleapiclient, google_auth_oauthlib, gspread, instagrapi, kickapi, requests, substack_api, TikTokApi, tweepy, twitchio, yaml"

COPY . .

RUN mkdir -p /app/data/guilds /app/data/secrets /app/data/public_media \
    && groupadd --system --gid 10001 eyebot \
    && useradd --system --uid 10001 --gid eyebot --home-dir /app eyebot \
    && chown --recursive eyebot:eyebot /app

USER eyebot

CMD ["python", "src/eyebot.py"]
