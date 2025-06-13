from typing_extensions import Self
import yaml
from yaml.loader import SafeLoader

class ConfigService():
    def __init__(self, configPath) -> None:
        with open(configPath) as f:
            self.config = yaml.load(f, Loader=SafeLoader)
        super().__init__()

    def get(self):
        return self.config