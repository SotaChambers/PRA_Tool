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

    def _login(self) -> None:
        logger.info("Login開始")
        self.driver.find_element(By.XPATH, '//*[@id="head_hunter_email"]').send_keys(self.id)
        self.driver.find_element(By.XPATH, '//*[@id="head_hunter_password"]').send_keys(self.password)
        self.driver.find_element(By.XPATH, '//*[@id="new_head_hunter"]/div/input').click()
        logger.info("Login終了")

    def _home_to_scout(self) -> None:
        logger.info("_home_to_scout開始")
        logger.info("Click スカウト Button...")
        self.driver.find_element(By.XPATH, "/html/body/header/nav/ul/li[2]/a").click()
        logger.info("_home_to_scout終了")

    def _scout_to_condition_list(self) -> None:
        logger.info("_scout_to_condition_list開始")
        logger.info("Click 検索条件リスト Button...")
        self.driver.find_element(By.XPATH, '//*[@id="AG-RS-01"]/div/div[1]/ul/li[2]/a').click()
        logger.info("_scout_to_condition_list終了")

    def _condition_list_to_candidate_list(self) -> None:
        logger.info("_condition_list_to_candidate_list開始")
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
                logger.info("_condition_list_to_candidate_list終了")
                return
        # 見つからなかった時のエラー
        logger.error(f"Not Found {self.keyword}")
        raise NotImplementedError("検索ワードが見つかりませんでした")

    def _candidate_list_to_candidate_detail(self) -> None:
        logger.info("_condition_list_to_candidate_list開始")
        start_idx = 4
        base_xpath = '//*[@id="drawer"]/div[{}]/div'
        logger.info("Select Candidate...")
        for i in range(start_idx, start_idx + self.max_num_people):
            logger.info(f"{i} 人目の対応開始...")
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
            # adhoc: 送受信履歴がある(3)かないか(4)でXPathが変わる
            try:
                self.company_name = self.driver.find_element(
                    By.XPATH,
                    '//*[@id="drawer"]/div[3]/div[2]/div/div[1]/div/div[1]/div[4]/div/div/div[1]/table/tbody/tr[1]/td/p',
                ).text
                self.salary = self.driver.find_element(
                    By.XPATH,
                    '//*[@id="drawer"]/div[3]/div[2]/div/div[1]/div/div[1]/div[4]/div/div/div[1]/table/tbody/tr[6]/td/p',
                ).text
                profile = self.driver.find_element(
                    By.XPATH,
                    '//*[@id="drawer"]/div[3]/div[2]/div/div[1]/div/div[1]/div[4]/div/div/div[1]/table/tbody/tr[7]/td/pre',
                ).text
            except NoSuchElementException:
                self.company_name = self.driver.find_element(
                    By.XPATH,
                    '//*[@id="drawer"]/div[3]/div[2]/div/div[1]/div/div[1]/div[3]/div/div/div[1]/table/tbody/tr[1]/td/p',
                ).text
                self.salary = self.driver.find_element(
                    By.XPATH,
                    '//*[@id="drawer"]/div[3]/div[2]/div/div[1]/div/div[1]/div[3]/div/div/div[1]/table/tbody/tr[6]/td/p',
                ).text
                profile = self.driver.find_element(
                    By.XPATH,
                    '//*[@id="drawer"]/div[3]/div[2]/div/div[1]/div/div[1]/div[3]/div/div/div[1]/table/tbody/tr[7]/td/pre',
                ).text
                logger.info(f"文字数は{len(self.profile)}")
            self.profile = profile[:2000]
            logger.info(f"企業名 : {self.company_name}, 年収 : {self.salary}, プロフィール : \n {self.profile}")

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
            title_element = self.driver.find_element(By.XPATH, '//*[@id="message_title"]')
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
            self.company_name, self.salary, self.profile, self.target_company_name, self.target_salary, self.target_content
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
            response = response["choices"][0]["text"]
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
