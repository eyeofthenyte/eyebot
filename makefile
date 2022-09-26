IMAGE_NAME="eyebot"
VERSION="latest"

build:
  docker build --tag ${IMAGE_NAME}:${VERSION} ./eyebot/
kill:
  @docker kill $(docker ps --filter="ancestor=${IMAGE_NAME}" --format="{{.ID}}")
start: kill
  docker run --rm -itd ${IMAGE_NAME}:${VERSION}