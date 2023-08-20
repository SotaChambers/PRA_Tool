import re
from time import sleep
from typing import Literal

import openai
import pandas as pd
from loguru import logger
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


class Scraper:
    def __init__(self, config: dict, mode: Literal["dummy", "main"] = "dummmy") -> None:
        self.mode = mode
        self._id = config.secret.id
        self._password = config.secret.password
        self.keyword = config.general.keyword
        self.max_num_people = config.general.max_num_people
        self.scout_list_path = config.general.scout_list_path
        self.chatgpt_input = config.general.chatgpt_input
        self.api_token = config.secret.API_TOKEN
        self.engine = config.general.engine
        self.cost_1k = config.general.cost_1k

        self.target_company_name, self.target_salary, self.target_content = self._read_scout_list()

        chrome_options = Options()
        chrome_options.add_experimental_option("detach", True)

        webdriver_service = Service(config.general.driver_path)
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

    def __call__(self) -> None:
        try:
            self._login()
            self._home_to_scout()
            self._scout_to_condition_list()
            self._condition_list_to_candidate_list()
            self._candidate_list_to_candidate_detail()
        except Exception as e:
            logger.error(f"Error occurred: {e}")
            logger.error("エラーが発生しました．管理者へ連絡してください")

    def _input(self, mode: Literal["xpath", "id"], key, content):
        if mode == "xpath":
            self.driver.find_element(By.XPATH, key).send_keys(content)
        elif mode == "id":
            self.driver.find_element(By.ID, key).send_keys(content)

    def _click(self, mode: Literal["xpath", "id"], key):
        if mode == "xpath":
            self.driver.find_element(By.XPATH, key).click()
        elif mode == "id":
            self.driver.find_element(By.ID, key).click()

    def _get_text(self, mode: Literal["xpath", "id"], key):
        if mode == "xpath":
            return self.driver.find_element(By.XPATH, key).text
        elif mode == "id":
            return self.driver.find_element(By.ID, key).text
        elif mode == "class":
            return self.driver.find_element(By.CLASS_NAME, key).text

    def _login(self) -> None:
        logger.info("Login")
        self._input("id", "head_hunter_email", self.id)
        self._input("id", "head_hunter_password", self.password)
        self._click("xpath", '//*[@id="new_head_hunter"]/div/input')

    def _home_to_scout(self) -> None:
        logger.info("_home_to_scout")
        self._click("xpath", "/html/body/header/nav/ul/li[2]/a")

    def _scout_to_condition_list(self) -> None:
        logger.info("_scout_to_condition_list")
        self._click("xpath", '//*[@id="AG-RS-01"]/div/div[1]/ul/li[2]/a')

    def _condition_list_to_candidate_list(self) -> None:
        logger.info("_condition_list_to_candidate_list")
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
            tmp_keyword = self._get_text("xpath", xpath)
            if tmp_keyword == keyword:
                logger.info(f"Click 検索 Button of {self.keyword}...")
                self._click("xpath", f'//*[@id="AG-SK-01"]/div/div[1]/table/tbody/tr[{i}]/td[6]/a')
                return
        # 見つからなかった時のエラー
        logger.error(f"Not Found {self.keyword}")
        raise NotImplementedError("検索ワードが見つかりませんでした")

    def _candidate_list_to_candidate_detail(self) -> None:
        logger.info("_condition_list_to_candidate_list")
        start_idx = 4
        base_xpath = '//*[@id="drawer"]/div[{}]/div'
        logger.info("Select Candidate...")
        for i in range(start_idx, start_idx + self.max_num_people):
            logger.info(f"{i - 3} 人目の対応開始...")
            xpath = base_xpath.format(i)
            element = self.driver.find_element(By.XPATH, xpath)
            element_id = element.get_attribute("id")

            # user_idを取得
            match = re.search("customer-masked-id-(.+)", element_id)
            self.user_id = match.group(1)
            new_tab_link = f"/agent/customers/{self.user_id}?from=resume_search"

            # プロフィールを取得
            self._click("id", f"customer-masked-id-{self.user_id}")
            sleep(3)
            self.company_name = self._get_text("class", "d-customer-company-name")
            profile = self._get_text("class", "d-customer-job-description")

            logger.info(f"文字数は{len(profile)}")
            self.profile = profile[:2000]
            logger.info(f"企業名 : {self.company_name}, プロフィール : \n {self.profile}")

            # 新しいタブを開く
            self.driver.execute_script("window.open('');")
            # 新しいタブに移動
            self.driver.switch_to.window(self.driver.window_handles[-1])
            # スカウトページにアクセス
            self.driver.get("https://agt.directscout.recruit.co.jp" + new_tab_link)

            # ChatGPTに投げるメッセージを作成
            msg_for_gpt = self._create_msg()
            # ChatGPTに投げる
            msg = self._send_gpt(msg_for_gpt, self.mode)
            # 返ってきたメッセージをタイトルと本文に分ける
            title, body = self._separete_title_body(msg)
            # タイトルと本文の入力xpathを取得，ChatGPTに投げる，[タイトル]と[本文]を入力
            title_element = self.driver.find_element(By.ID, "message_title")
            title_element.clear()
            title_element.send_keys(title)
            body_element = self.driver.find_element(By.XPATH, '//*[@id="message_body"]')
            body_element.clear()
            body_element.send_keys(body)

            # メインタブに戻る
            self.driver.switch_to.window(self.driver.window_handles[0])

    def _create_msg(self) -> str:
        new_tab_link = f"/agent/customers/{self.user_id}/scouts/new?from=resume_detail"
        self.driver.get("https://agt.directscout.recruit.co.jp" + new_tab_link)
        msg = self.chatgpt_input.format(
            self.company_name, self.profile, self.target_company_name, self.target_salary, self.target_content
        )
        logger.info(f"Message to ChatGPT is \n {msg}")
        return msg

    def _send_gpt(self, msg: str, mode: str = "dummy") -> str:
        openai.api_key = self.api_token
        if mode == "dummy":
            logger.info("ChatGPT Dummyモードで実行中...お金は掛かっていません")
            response = {
                "choices": [{"message": {"content": "【タイトル】xxxx\n【本文】\n初めまして、MichaelPageの山本と申します。\nこれはテストです。\nご連絡お待ちしています。"}}]
            }
            response = response["choices"][0]["message"]["content"]
        elif mode == "main":
            logger.info("ChatGPT 本番モードで実行中...お金が掛かります")
            response = response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo", messages=[{"role": "user", "content": msg}]
            )
            # お金の計算
            tokens_used = response["usage"]["total_tokens"]
            cost = tokens_used * self.cost_1k / 1000
            logger.info(f"このリクエストで使用されたトークン数: {tokens_used}")
            logger.info(f"推定料金（USD）: {cost}")
            response = response["choices"][0]["message"]["content"]
        else:
            raise NotImplementedError("modeが不正です")

        logger.info(f"ChatGPTからの返答: \n {response}")
        return response

    def _separete_title_body(self, msg: str) -> tuple[str, str]:
        title = msg.split("\n")[0].replace("【タイトル】", "")
        body = "\n".join(msg.split("\n")[1:]).replace("【本文】", "")
        return title, body

    def shotdown(self) -> None:
        self.driver.quit()
