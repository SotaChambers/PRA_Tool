from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel


class SecretConfig(BaseModel):
    id: str
    password: str


def read_yaml(yaml_path: Path) -> SecretConfig:
    return SecretConfig.parse_obj(yaml.safe_load(yaml_path.open("r")))
