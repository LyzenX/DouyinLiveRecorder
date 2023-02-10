# coding=utf-8
"""
:author: Lyzen
:date: 2023.02.07
:brief: 弹幕录制
"""

import time

from selenium.webdriver.common.by import By

from dylr.core import record_manager, app
from dylr.core.browser import Browser
from dylr.util import logger, cookie_utils


danmu_recording = []


def start_recording(room, browser=None, rec=None, start_time=None):
    global danmu_recording

    if room in danmu_recording:
        logger.warning(f'{room.room_name}({room.room_id})的弹幕已经在录制了')
        return

    if start_time is None:
        start_time = time.localtime()

    start_time_str = time.strftime('%Y%m%d_%H%M%S', start_time)
    filename = f"download/{room.room_name}/{start_time_str}.xml"

    if browser is None:
        # 新开浏览器，需要填入 cookie 并刷新
        logger.debug(f'start recording danmu for {room.room_name}({room.room_id}). browser not passed.')
        browser = Browser()
        browser.open(f'https://live.douyin.com/{room.room_id}')
        cookies = cookie_utils.str2cookies(cookie_utils.get_danmu_cookie())
        for cookie in cookies:
            browser.driver.add_cookie(cookie)
        browser.driver.refresh()
        browser.driver.implicitly_wait(10)
        time.sleep(1)
        browser.send_cdp_cmd()
        # 尝试加载直播，即寻找 video 标签
        # 如果没找到，可能是网页未加载完成，重试
        # 也可能是直播未开始，多次重试失败后停止录制
        for retry in range(1, 4):
            video_tags = browser.driver.find_elements(By.TAG_NAME, "video")
            if not video_tags:
                if retry == 3:
                    logger.error(f'{room.room_name}({room.room_id})录制弹幕失败：无法加载直播。')
                    return
                else:
                    logger.error(f'{room.room_name}({room.room_id})录制弹幕失败：无法加载直播，正在重试({retry})')
                    browser.driver.refresh()
                    time.sleep(1)
    else:
        # 开播检测传来了浏览器，不必刷新网页
        cookies = cookie_utils.str2cookies(cookie_utils.get_danmu_cookie())
        for cookie in cookies:
            browser.driver.add_cookie(cookie)
        logger.debug(f'start recording danmu for {room.room_name}({room.room_id}). browser passed.')

    logger.info_and_print(f'开始录制 {room.room_name}({room.room_id}) 的弹幕')
    danmu_recording.append(room)

    # 判断是否能加载弹幕
    # 可能的bug：如果长时间没人进入直播间，则可能会认为无法加载弹幕
    # 但多次失败并不会停止线程，弹幕录制线程只会在直播结束后才停止，故该bug只会稍稍影响性能(前几分钟不断刷新网页)
    retry = 0
    while retry < 3:
        # 判断弹幕是否可以加载出来
        tag = browser.driver.find_elements(By.CLASS_NAME, "webcast-chatroom___item")
        if len(tag) > 0:
            break
        # 弹幕加载不出来
        retry += 1
        cookie_utils.record_cookie_failed()
        logger.warning(f'Cannot find danmu of {room.room_name}({room.room_id}). Try refreshing.')
        cookies = cookie_utils.str2cookies(cookie_utils.get_danmu_cookie())
        for cookie in cookies:
            browser.driver.add_cookie(cookie)
        browser.driver.refresh()
        browser.driver.implicitly_wait(10)
        time.sleep(1)
        browser.send_cdp_cmd()
    if retry == 3:
        logger.error_and_print(f'{room.room_name}({room.room_id}) 弹幕录制失败：无法加载弹幕，可能是cookie失效了？')

    # 写入文件头部数据
    with open(filename, 'a', encoding='UTF-8') as file:
        file.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n"
                   "<?xml-stylesheet type=\"text/xsl\" href=\"#s\"?>\n"
                   "<i>\n")

    start_time = int(time.mktime(start_time))
    danmu = {}
    retry = 1
    while True:
        # 直播结束，弹幕录制也结束
        if rec is not None and rec.stop_signal:
            break
        if '直播已结束' in browser.driver.find_element(By.CLASS_NAME, 'basicPlayer').text:
            break
        if not record_manager.is_recording(room):
            break
        # 房间被删除，结束录制
        if room not in record_manager.rooms:
            break

        # 一直没弹幕，重新获取
        if len(danmu) == 0 and retry <= 3 and time.time() - start_time > 30 * retry:
            logger.warning(f'Cannot find danmu of {room.room_name}({room.room_id}). Try refreshing.')
            cookies = cookie_utils.str2cookies(cookie_utils.get_danmu_cookie())
            for cookie in cookies:
                browser.driver.add_cookie(cookie)
            browser.driver.refresh()
            browser.driver.implicitly_wait(10)
            time.sleep(1)
            browser.send_cdp_cmd()
            # browser.driver.get_screenshot_as_file(f'./logs/debug{room.room_id}-{retry}.png')
            retry += 1
            continue

        # 分析并从 html 中获取弹幕
        elements = browser.driver.find_elements(By.CLASS_NAME, 'webcast-chatroom___item')
        for element in elements:
            if app.stop_all_threads:
                # 软件被强制停止，写入文件尾，以免弹幕文件不完整而无法使用
                if len(danmu) > 0:
                    with open(filename, 'a', encoding='UTF-8') as file:
                        file.write('</i>')
                break
            if not record_manager.is_recording(room):
                # 直播结束，弹幕录制也结束
                break

            try:
                data_id = str(element.get_attribute('data-id'))
                if data_id in danmu:
                    continue

                inner_div = element.find_elements(By.TAG_NAME, 'div')[0]

                # 忽略欢迎来到直播间的提示
                if inner_div.get_attribute('class') == 'webcast-chatroom__room-message':
                    continue

                text = inner_div.text
                # 忽略用户来了的提示
                if '：' not in text and '来了' in text:
                    continue
                # 忽略送礼
                if '送出了 × ' in text:
                    continue
                # 去除用户名前面的各种花里胡哨的前缀
                if '\n' in text:
                    text = text[text.index('\n')+1:].strip()

                # print(text)  # 在控制台中输出弹幕

                user = text[:text.index('：')]
                mes = text[text.index('：')+1:]

                now = time.time()
                danmu[data_id] = {
                    'user': user,
                    'message': mes,
                    'time': now
                }

                second = now - start_time
                # 写入单条数据
                with open(filename, 'a', encoding='UTF-8') as file:
                    file.write(f"  <d p=\"{round(second, 2)},1,25,16777215,"
                               f"{int(now*1000)},0,1602022773,0\" user=\"{user}\">{mes}</d>\n")

            except Exception:
                pass
        time.sleep(0.2)
    # 写入文件尾
    with open(filename, 'a', encoding='UTF-8') as file:
        file.write('</i>')
    logger.info_and_print(f'{room.room_name}({room.room_id}) 弹幕录制结束')
    danmu_recording.remove(room)
    browser.quit()  # 关闭浏览器，清除缓存
