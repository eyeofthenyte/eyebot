IMAGE_NAME ?= eyebot
VERSION ?= 2.1.0

.PHONY: build start stop restart logs

build:
	IMAGE_NAME=$(IMAGE_NAME) EYEBOT_VERSION=$(VERSION) docker compose build

start:
	IMAGE_NAME=$(IMAGE_NAME) EYEBOT_VERSION=$(VERSION) docker compose up --detach --build

stop:
	docker compose down

restart:
	IMAGE_NAME=$(IMAGE_NAME) EYEBOT_VERSION=$(VERSION) docker compose up --detach --build --force-recreate

logs:
	docker compose logs --follow eyebot
