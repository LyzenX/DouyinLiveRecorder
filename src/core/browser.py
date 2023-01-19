# coding=utf-8
"""
:author: Lyzen
:date: 2023.01.13
:brief: 浏览器类
"""

from selenium import webdriver

from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from src.core import app


class NoCliService(Service):
    def __init__(self, executable_path: str,
                 port: int = 0, service_args=None,
                 log_path: str = None, env: dict = None):
        super(Service, self).__init__(
            executable_path,
            port,
            service_args,
            log_path,
            env,
            "Please see https://chromedriver.chromium.org/home"
        )
        self.creationflags = 0x8000000
        self.creation_flags = 0x8000000


class Browser:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument(
            'user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            ' (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36"')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        if app.win_mode:
            self.driver = webdriver.Chrome(options=options, service=NoCliService(ChromeDriverManager().install()))
        else:
            self.driver = webdriver.Chrome(options=options, service=Service(ChromeDriverManager().install()))
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
        })

    def open(self, url):
        self.driver.get(url)

    def quit(self):
        self.driver.quit()
