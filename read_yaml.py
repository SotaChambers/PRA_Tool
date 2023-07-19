from pathlib import Path

import yaml
from pydantic import BaseModel


class SecretConfig(BaseModel):
    id: str
    password: str


class GeneralConfig(BaseModel):
    url: str
    keyword: str
    max_num_people: int
    scout_list_path: str
    chatgpt_input: str


class Config(BaseModel):
    secret: SecretConfig
    general: GeneralConfig


def read_secret_yaml(yaml_path: Path) -> SecretConfig:
    return SecretConfig.parse_obj(yaml.safe_load(yaml_path.open("r")))


def read_general_config(yaml_path: Path) -> GeneralConfig:
    return GeneralConfig.parse_obj(yaml.safe_load(yaml_path.open("r")))


def read_config(secret_path: Path, general_path: Path) -> Config:
    secret_config = read_secret_yaml(secret_path)
    general_config = read_general_config(general_path)
    return Config(secret=secret_config, general=general_config)
