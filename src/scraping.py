from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


class Scraper:
    def __init__(self, config: dict, pipeline_cfg: dict):
        self._id = config.secret.id
        self._password = config.secret.password
        self.pipeline_cfg = pipeline_cfg

        chrome_options = Options()
        chrome_options.add_experimental_option("detach", True)

        webdriver_service = Service("driver/chromedriver")
        self.driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
        self.driver.get(config.general.url)

    @property
    def id(self) -> str:
        return self._id

    @property
    def password(self) -> str:
        return self._password

    def __call__(self):
        for action_name, actions in self.pipeline_cfg.items():  # 各ページで行う動作
            if action_name == "login":
                self._login(actions=actions, id=self.id, password=self.password)
            else:
                for value in actions.values():  # 各ページで行う1つずつの動作
                    if value["action"] == "input":
                        self._input_content(value["xpath"], value["content"])
                    elif value["action"] == "click":
                        self._click_button(value["xpath"])

        # self.shotdown()

    def _login(self, actions: dict, id: str, password: str) -> None:
        self._input_content(actions["input_id"]["xpath"], id)
        self._input_content(actions["input_password"]["xpath"], password)
        self._click_button(actions["click_submit"]["xpath"])

    def _input_content(self, xpath: str, content: str) -> None:
        self.driver.find_element(By.XPATH, xpath).send_keys(content)

    def _click_button(self, xpath: str) -> None:
        self.driver.find_element(By.XPATH, xpath).click()

    def shotdown(self) -> None:
        self.driver.quit()
