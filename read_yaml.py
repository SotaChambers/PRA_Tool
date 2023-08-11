from pathlib import Path

import yaml
from pydantic import BaseModel, validator


class SecretConfig(BaseModel):
    id: str
    password: str
    API_TOKEN: str


class GeneralConfig(BaseModel):
    url: str
    driver_path: str
    keyword: str
    max_num_people: int
    scout_list_path: str
    engine: str
    cost_1k: float
    chatgpt_input: str

    @validator("driver_path", pre=True, always=True)
    def check_driver_path_exists(cls, v):
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Driverが存在しません. {v}")
        return v

    @validator("scout_list_path", pre=True, always=True)
    def check_scout_list_path_exists(cls, v):
        path = Path(v)
        if not path.exists():
            raise ValueError(f"スカウトリストが存在しません. {v}")
        return v


class Config(BaseModel):
    secret: SecretConfig
    general: GeneralConfig


def read_secret_yaml(yaml_path: Path) -> SecretConfig:
    return SecretConfig.parse_obj(yaml.safe_load(yaml_path.open("r", encoding="utf-8")))


def read_general_config(yaml_path: Path) -> GeneralConfig:
    return GeneralConfig.parse_obj(yaml.safe_load(yaml_path.open("r", encoding="utf-8")))


def read_config(secret_path: Path, general_path: Path) -> Config:
    secret_config = read_secret_yaml(secret_path)
    general_config = read_general_config(general_path)
    return Config(secret=secret_config, general=general_config)
