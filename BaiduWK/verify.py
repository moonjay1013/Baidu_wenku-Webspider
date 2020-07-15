# --该页处理IP多次请求百度文库而弹出的验证页面
# url为https://wenku.baidu.com/wkvcode.html
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import time
import re
from pyquery import PyQuery as pq
from urllib.parse import quote
from Question_bank.BaiduWK.setting import BASE_URL


class VerifyRobots:
    def __init__(self, key_word):
        #self.url = 'https://wenku.baidu.com/wkvcode.html?source=search&type=1&callback=https%3A%2F%2Fwenku.baidu.com%2Fsearch%2Fmain%3Fpv%3Dsearch%26word%3Djava%25E9%25A2%2598%25E5%25BA%2593%26url%3D%2Fsearch%3Fword%3Djava%25E9%25A2%2598%25E5%25BA%2593'
        self.url = BASE_URL + quote(key_word)
        self.web = webdriver.Chrome()
        self.wait = WebDriverWait(self.web, 10)

    def get_button(self):
        click_btn = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'vcode-slide-button')))
        return click_btn

    def get_track(self):# 最大距离260px
        track = []
        current = 0
        t = 0.2
        a = 6  # 加速度
        v = 0  # 初速度
        while current < 260:
            v0 = v
            v = v0 + a * t
            move = v0 * t + 1/2 * a * t * t  # 移动距离
            current += move  # 当前位移
            track.append(round(move))
        return track

    def move_to_verify(self, btn, track):
        ActionChains(self.web).click_and_hold(btn).perform()
        for x in track:
            ActionChains(self.web).move_by_offset(xoffset=x, yoffset=0).perform()
        time.sleep(0.5)
        ActionChains(self.web).release().perform()

    def get_index_page(self, html):
        """
        加载到搜索结果页，返回总偏移数   gui.py显示
        :return: offset是网页隐藏的尾页链接，通过re库解析到偏移值
        """
        doc = pq(html)
        # 搜索结果--相关文档数
        doc_nums = doc('div.clearfix > span').text()
        # 最大偏移值--得到总页数
        page_href = doc('div.page-content > a.last').attr('href')  # last page's url is hidden
        max_pn = int(re.match('^\?word.*?pn=(\d+)$', page_href).group(1))
        page = int(max_pn / 10)
        page += 1
        return doc_nums + ' - ' + '共' + str(page) + '页'

    def run(self):
        try:
            self.web.get(self.url)
            html = self.web.page_source
            return self.get_index_page(html)
        except Exception:
            btn = self.get_button()
            track = self.get_track()
            self.move_to_verify(btn=btn, track=track)
            time.sleep(3)
            return self.get_index_page(self.web.page_source)
        finally:
            self.web.close()


if __name__ == '__main__':
    vr = VerifyRobots('java题库')
    print(vr.run())