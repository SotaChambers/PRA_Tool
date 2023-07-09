
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

class Scraper:
    def __init__(self, config):
        self.id = config.secret.id
        self.password = config.secret.password

        chrome_options = Options()
        chrome_options.add_experimental_option("detach", True)

        webdriver_service = Service("driver/chromedriver")
        self.driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
        self.driver.get(config.general.url)

    def __call__(self):
        self.login()
        self.home()
        self.point()
        # self.shotdown()

    def login(self):
        for id, input in zip(["id", "pass"], [self.id, self.password]):
            self.driver.find_element(By.ID, id).send_keys(input)
        self.driver.find_element(By.XPATH, "//*[@id='input_form']/form/p/input").click()

    def home(self):
        self.driver.find_element(By.ID, "LnkV0800_002Top").click()

    def point(self):
        point = self.driver.find_element(By.ID, "LblNormalPoint").text
        date = self.driver.find_element(By.ID, "LblNormalExpirationDate").text
        print(f"現在 {point} Point 所有しています．{date} にポイントは失効します．")

    def shotdown(self):
        self.driver.quit()
