from datetime import datetime
import io
import logging
import sys

class LogService():
    def __init__(self, name, config) -> None:
        self.logger = logging.Logger(
            name=name,
            level=config["level"],
        )

        output = config["output"]
        if output == "syslog":
            output = sys.stdout
        else:
            output = io.open(output, mode="a")

        handler = logging.StreamHandler(output)
        handler.setFormatter(logging.Formatter(
            datefmt="%Y/%m/%d %H:%M:%S",
            fmt="[%(asctime)s][%(levelname)s] %(name)s - %(message)s"
        ))

        self.logger.addHandler(handler)

    def info(self, message):
        self.logger.info(msg=message)

    def error(self, message):
        self.logger.error(msg=message)

    def warn(self, message):
        self.logger.warn(msg=message)

    def log(self, message):
        self.logger.log(level=logging.DEBUG, msg=message)