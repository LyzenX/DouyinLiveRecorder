# coding=utf-8
import time

from dylr.core import config
from dylr.util import logger
from dylr.plugin import plugin
from dylr.core.browser import Browser

cookie_cache = None
# 记录cookie访问失败的次数
cookie_failed = 0
max_cookie_failed = 5


def record_cookie_failed():
    global cookie_failed
    cookie_failed += 1
    logger.debug_and_print('检测开播时返回系统繁忙')
    if cookie_failed == max_cookie_failed:
        logger.fatal_and_print('多次重试无法访问资源，可能是cookie失效')
        plugin.on_cookie_invalid()

    # 自动获取 cookie
    if not config.is_using_custom_cookie() and cookie_failed == max_cookie_failed:
        auto_get_cookie()


def str2cookies(s: str):
    secs = s.split(';')
    res = []
    for cookie in secs:
        key, value = cookie.split('=', 1)
        cookie_dict = {
            'domain': '.douyin.com',
            'name': key.strip(),
            'value': value.strip(),
            "expires": value.strip(),
            'path': '/',
            'httpOnly': False,
            'HostOnly': False,
            'Secure': False
        }
        res.append(cookie_dict)
    return res


def cookies2str(cookies):
    res = ''
    for cookie in cookies:
        res += cookie['name'] + '=' + cookie['value'] + ';'
    res = res.strip(";")
    return res


def auto_get_cookie():
    global cookie_cache, cookie_failed
    logger.info_and_print(f'获取cookie中...')

    browser = Browser()
    browser.open('https://www.douyin.com')
    browser.driver.set_page_load_timeout(10)
    time.sleep(1)
    browser.driver.refresh()
    browser.driver.set_page_load_timeout(10)
    time.sleep(1)
    cookie_cache = cookies2str(browser.driver.get_cookies())
    logger.info_and_print(f'cookie获取完成')

    cookie_failed = 0

    browser.quit()


def get_danmu_cookie():
    cookie_only_used_for_danmu = config.get_cookie_only_used_for_danmu()
    if cookie_only_used_for_danmu is not None and len(cookie_only_used_for_danmu) > 0:
        return cookie_only_used_for_danmu
    else:
        return cookie_cache
