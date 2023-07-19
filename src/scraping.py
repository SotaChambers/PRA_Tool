import re
from time import sleep
import pandas as pd
from loguru import logger
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


class Scraper:
    def __init__(self, config: dict):
        self._id = config.secret.id
        self._password = config.secret.password
        self.keyword = config.general.keyword
        self.max_num_people = config.general.max_num_people
        self.scout_list_path = config.general.scout_list_path
        self.chatgpt_input = config.general.chatgpt_input

        self.target_company_name, self.target_salary, self.target_content = self._read_scout_list()

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

    def _read_scout_list(self) -> tuple:
        logger.info("Start Read Excel...")
        df = pd.read_excel(self.scout_list_path)
        target_company_name = df[df["検索条件"] == self.keyword].iloc[0, 2]
        target_salary = df[df["検索条件"] == self.keyword].iloc[0, 3]
        target_content = df[df["検索条件"] == self.keyword].iloc[0, 4]
        logger.info("End Read Excel...")
        return target_company_name, target_salary, target_content

    def __call__(self):
        self._login()
        self._home_to_scout()
        self._scout_to_condition_list()
        self._condition_list_to_candidate_list()
        self._candidate_list_to_candidate_detail()

        # self.shotdown()

    def _login(self) -> None:
        logger.info("Login...")
        self.driver.find_element(By.XPATH, '//*[@id="head_hunter_email"]').send_keys(self.id)
        self.driver.find_element(By.XPATH, '//*[@id="head_hunter_password"]').send_keys(self.password)
        self.driver.find_element(By.XPATH, '//*[@id="new_head_hunter"]/div/input').click()

    def _home_to_scout(self):
        logger.info("Click スカウト Button...")
        self.driver.find_element(By.XPATH, "/html/body/header/nav/ul/li[2]/a").click()

    def _scout_to_condition_list(self):
        logger.info("Click 検索条件リスト Button...")
        self.driver.find_element(By.XPATH, '//*[@id="AG-RS-01"]/div/div[1]/ul/li[2]/a').click()

    def _condition_list_to_candidate_list(self):
        logger.info(f"Select Keyword : {self.keyword}...")
        keyword = self.keyword
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
        logger.info(f"All List Number : {max_list_num}...")

        for i in range(1, max_list_num + 1):
            xpath = base_xpath.format(i)
            tmp_keyword = self.driver.find_element(By.XPATH, xpath).text
            if tmp_keyword == keyword:
                logger.info(f"Click 検索 Button of {self.keyword}...")
                self.driver.find_element(By.XPATH, f'//*[@id="AG-SK-01"]/div/div[1]/table/tbody/tr[{i}]/td[6]/a').click()
                return
        # 見つからなかった時のエラー
        logger.error(f"Not Found {self.keyword}")
        raise NotImplementedError("検索ワードが見つかりませんでした")

    def _candidate_list_to_candidate_detail(self):
        start_idx = 4
        base_xpath = '//*[@id="drawer"]/div[{}]/div'
        logger.info("Select Candidate...")
        for i in range(start_idx, start_idx + self.max_num_people):
            logger.info(f"No. {i}")
            xpath = base_xpath.format(i)
            element = self.driver.find_element(By.XPATH, xpath)
            element_id = element.get_attribute("id")

            # user_idを取得
            match = re.search("customer-masked-id-(.+)", element_id)
            self.user_id = match.group(1)
            new_tab_link = f"/agent/customers/{self.user_id}?from=resume_search"

            # プロフィールを取得
            self.driver.find_element(By.ID, f"customer-masked-id-{self.user_id}").click()
            sleep(3)
            self.company_name = self.driver.find_element(
                By.XPATH, '//*[@id="drawer"]/div[3]/div[2]/div/div[1]/div/div[1]/div[4]/div/div/div[1]/table/tbody/tr[1]/td/p'
            ).text
            self.salary = self.driver.find_element(
                By.XPATH, '//*[@id="drawer"]/div[3]/div[2]/div/div[1]/div/div[1]/div[4]/div/div/div[1]/table/tbody/tr[6]/td/p'
            ).text
            self.profile = self.driver.find_element(
                By.XPATH,
                '//*[@id="drawer"]/div[3]/div[2]/div/div[1]/div/div[1]/div[4]/div/div/div[1]/table/tbody/tr[7]/td/pre',
            ).text
            logger.info(f"企業名 : {self.company_name}, 年収 : {self.salary}, プロフィール : \n {self.profile}")

            # TODO: 一旦txtファイルで出力
            Path("output.txt").write_text(f"{self.company_name}\n\n{self.salary}\n\n{self.profile}")

            # 新しいタブを開く
            self.driver.execute_script("window.open('');")
            # 新しいタブに移動
            self.driver.switch_to.window(self.driver.window_handles[-1])
            # スカウトページにアクセス
            self.driver.get("https://agt.directscout.recruit.co.jp" + new_tab_link)

            self._create_msg()

            # TODO: メインタブに戻る
            self.driver.switch_to.window(self.driver.window_handles[0])

    def _create_msg(self):
        new_tab_link = f"/agent/customers/{self.user_id}/scouts/new?from=resume_detail"
        self.driver.get("https://agt.directscout.recruit.co.jp" + new_tab_link)
        msg = self.chatgpt_input.format(
            self.company_name, self.salary, self.profile, self.target_company_name, self.target_salary, self.target_content
        )
        logger.info(f"Message to ChatGPT is \n {msg}")
        # TODO: タイトルと本文の入力xpathを取得，ChatGPTに投げる，[タイトル]と[本文]を入力

    def shotdown(self) -> None:
        self.driver.quit()
