# --输入爬取关键字-- 返回搜索结果的所有文档链接
"""
主要使用requests库
"""
import requests
import re
from pyquery import PyQuery as pq
from urllib.parse import quote  # 将内容转化为URL编码库  --如中文转化为编码
from Question_bank.BaiduWK.setting import BASE_URL, ENCONDING


class DocURLS:
    def __init__(self, key_word):
        self.url = BASE_URL + quote(key_word)
        self.session = requests.session()

    def get_doc_urls(self, page_url):
        """
        爬取当前页的文档链接
        :param page_url: 索引页的链接--某一页
        :return:
        """
        try:
            response = self.session.get(page_url)
            # print(response.apparent_encoding)  # 当前页编码为GB2312
            response.encoding = ENCONDING
            html = response.text
            doc = pq(html)
            all_a = doc('dl > dt > p.fl > a').items()
            url_list = []
            for a in all_a:
                tit = a.attr("title")  # 'WebElement' 获取节点属性
                # 得到文档的链接--干扰链接(VIP充值链接)
                doc_url = a.attr("href")
                if re.search('https://.*?search', doc_url):
                    item = {'title': tit, 'url': doc_url}  # 每个链接设为dict格式 方便数据库写入 也方便获取属性
                    url_list.append(item)
            return url_list
        except Exception as e:
            print('Error', e.args)

    def get_all_urls(self, str_page):
        """
        获取所有文档的链接
        MAX_PN--最大偏移值
        num决定偏移量；i是计数器
        :return: 列表all_doc_urls(所有文档的‘标题：链接’--list元素格式)
        """
        # 将所有索引页的链接放入list中
        try:
            num = 0  # 偏移值从0（第一页）开始、10（第二页）、20（第三页）...
            page_urls = []
            int_page = int(str_page) - 1
            while num <= int_page:  # 应该由用户选择爬取的数目--1代表爬两页
                page_urls.append(self.url + '&pn={}'.format(str(num * 10)))
                num += 1
            # 每个索引页的文档链接爬取
            i = 1
            all_doc_urls = []
            for url in page_urls:
                print('正在爬取第' + str(i) + '页的文档链接')
                for item in self.get_doc_urls(page_url=url):
                    all_doc_urls.append(item)
                print('第' + str(i) + '页爬取成功!')
                i += 1
            return all_doc_urls
        except Exception as e:
            print('Error', e.args)
