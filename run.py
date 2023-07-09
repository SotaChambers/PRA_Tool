from time import sleep
from pathlib import Path
from read_yaml import read_config

from src.scraping import Scraper

config = read_config(
    Path("config/secret.yaml"),
    Path("config/general.yaml")
)

scraper = Scraper(config)()

sleep(3)
# ブラウザを閉じる
