from pathlib import Path

import click
import yaml

from read_yaml import read_config
from src.scraping import Scraper


@click.command()
@click.argument("general_cfg_path", type=click.Path(exists=True), default=Path("config/general.yaml"))
@click.argument("secret_cfg_path", type=click.Path(exists=True), default=Path("config/secret.yaml"))
@click.argument("pipeline_cfg_path", type=click.Path(exists=True), default=Path("config/pipeline.yaml"))
def main(
    general_cfg_path: Path,
    secret_cfg_path: Path,
    pipeline_cfg_path: Path,
):
    config = read_config(general_cfg_path, secret_cfg_path)
    pipeline_cfg = yaml.safe_load(pipeline_cfg_path.open("r"))
    Scraper(config, pipeline_cfg)()


if __name__ == "__main__":
    main()
