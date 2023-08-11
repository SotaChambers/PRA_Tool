from pathlib import Path
from typing import Literal

import click
from loguru import logger

from read_yaml import read_config
from src.scraping import Scraper
from utils.utils import get_dt_now


@click.command()
@click.argument("general_cfg_path", type=click.Path(exists=True), default=Path("config/general.yaml"))
@click.argument("secret_cfg_path", type=click.Path(exists=True), default=Path("config/secret.yaml"))
@click.option("--mode", type=str, default="dummy")
def main(
    general_cfg_path: Path,
    secret_cfg_path: Path,
    mode: Literal["dummy", "main"] = "dummy",
):
    dt_now = get_dt_now()
    logger.add(f"logs/{dt_now}.log", rotation="500MB")
    logger.info("Start RPA Tool...")

    config = read_config(secret_path=secret_cfg_path, general_path=general_cfg_path)
    Scraper(config, mode)()


if __name__ == "__main__":
    main()
