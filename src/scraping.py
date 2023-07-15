from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


class Scraper:
    def __init__(self, config, pipeline_cfg):
        self.id = config.secret.id
        self.password = config.secret.password
        self.pipeline_cfg = pipeline_cfg

        chrome_options = Options()
        chrome_options.add_experimental_option("detach", True)

        webdriver_service = Service("driver/chromedriver")
        self.driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
        self.driver.get(config.general.url)

    def __call__(self):
        for actions in self.pipeline_cfg.values():  # 各ページで行う動作
            for value in actions.values():  # 各ページで行う1つずつの動作
                if value["action"] == "input":
                    self.driver.find_element(By.XPATH, value["xpath"]).send_keys(value["content"])
                elif value["action"] == "click":
                    self.driver.find_element(By.XPATH, value["xpath"]).click()

        # self.shotdown()

    def shotdown(self):
        self.driver.quit()
