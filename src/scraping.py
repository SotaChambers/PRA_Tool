from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


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
        self._login()
        self._home_to_scout()
        self._scout_to_condition_list()
        # self._condition_list_to_candidate_list()
        # self._candidate_list_to_candidate_detail()
        # self._candidate_detail_to_scout_msg_box()

        # self.shotdown()

    def _login(self) -> None:
        self.driver.find_element(By.XPATH, '//*[@id="head_hunter_email"]').send_keys(self.id)
        self.driver.find_element(By.XPATH, '//*[@id="head_hunter_password"]').send_keys(self.password)
        self.driver.find_element(By.XPATH, '//*[@id="new_head_hunter"]/div/input').click()

    def _home_to_scout(self):
        self.driver.find_element(By.XPATH, "/html/body/header/nav/ul/li[2]/a").click()

    def _scout_to_condition_list(self):
        self.driver.find_element(By.XPATH, '//*[@id="AG-RS-01"]/div/div[1]/ul/li[2]/a').click()

    def _condition_list_to_candidate_list(self):
        keyword = "インフラエンジニア"
        base_xpath = '//*[@id="AG-SK-01"]/div/div[1]/table/tbody/tr[{}]/td[1]/p'
        index = 1
        try:
            while True:
                xpath = base_xpath.format(index)
                self.driver.find_element(By.XPATH, xpath)
                index += 1
        except NoSuchElementException:
            max_list_num = index - 1
        except Exception as e:
            assert f"Error occurred: {e}"

        for i in range(1, max_list_num + 1):
            xpath = base_xpath.format(i)
            tmp_keyword = self.driver.find_element(By.XPATH, xpath).text
            if tmp_keyword == keyword:
                self.driver.find_element(By.XPATH, f'//*[@id="AG-SK-01"]/div/div[1]/table/tbody/tr[{i}]/td[6]/a').click()
                break
        # TODO: 見つからなかった時のエラー書く

    def _candidate_list_to_candidate_detail(self):
        start_idx = 4
        base_xpath = '//*[@id="drawer"]/div[{}]/div'
        # for i in range(start_idx, 5): # TODO: ここはユーザーが一気に何回作りたいかで変える
        xpath = base_xpath.format(4)
        element = self.driver.find_element(By.XPATH, xpath)
        element_id = element.get_attribute("id")
        import re

        match = re.search("customer-masked-id-(.+)", element_id)
        self.user_id = match.group(1)
        new_tab_link = f"/agent/customers/{self.user_id}?from=resume_search"
        # 新しいタブを開く
        self.driver.execute_script("window.open('');")
        # 新しいタブに移動
        self.driver.switch_to.window(self.driver.window_handles[-1])
        # スカウトページにアクセス
        self.driver.get("https://agt.directscout.recruit.co.jp" + new_tab_link)

    def _candidate_detail_to_scout_msg_box(self):
        new_tab_link = f"/agent/customers/{self.user_id}/scouts/new?from=resume_detail"
        self.driver.get("https://agt.directscout.recruit.co.jp" + new_tab_link)

    def shotdown(self) -> None:
        self.driver.quit()
