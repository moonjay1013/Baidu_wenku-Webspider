# --输入待爬取文档的链接--返回该文档的所有可视内容
"""
主要使用selenium库与requests库
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from pyquery import PyQuery as pq
import re, json
import time
import requests

from Question_bank.BaiduWK.write_mongo import MongoDBClient


class DocContent:
    def __init__(self, doc_url):
        self.url = doc_url
        self.browser = webdriver.Chrome()
        self.wait = WebDriverWait(self.browser, 10)
        self.session = requests.session()

    # pdf和vip付费内容使用selenium库爬取
    def get_doc_page(self):
        """
        #文档最后一页的div的下面是id='doc_bottom_wrap'的div 其class属性隐含文档页数
        :return: int类型的文档页数
        """
        bottom = self.browser.find_element_by_id('doc_bottom_wrap')
        page_str = bottom.get_attribute('class')
        page = int(re.match('^(\d+).*?hidden-doc-banner', page_str).group(1))
        return page

    def parse_doc_type(self, content):
        """
        doc文档 对内容爬取的css_selector为'div.reader-txt-layer div.ie-fix > p'
        txt文档 css_selector为'div.reader-page-wrap > p.p-txt'
        pdf文档 css_selector为'div.reader-pic-layer div.ie-fix > div.reader-pic-item'
        ppt文档 css_selector为''
        付费看全文的文档 none_type
        :param content:网页源码
        :return: type
        """
        try:
            type = re.search(r"docType.*?\:.*?\'(.*?)\'\,", content).group(1)
        except AttributeError:
            return 'none_type'
        return type

    def get_more(self):
        try:
            #  法①
            '''
            # 先找到 阅读更多上的广告 的位置
            area_more = browser.find_element_by_css_selector(
                '#html-reader-go-more > div.banner-core-wrap.super-vip > div.doc-banner-text')
            # 拖动到对应的位置
            browser.execute_script("arguments[0].scrollIntoView();", area_more)
            # 模拟点击，继续阅读  
            continue_read = browser.find_element_by_css_selector('div.continue-to-read > div.banner-more-btn > span')
            continue_read.click()
            '''
            # 法②
            # 模拟调用js访问（模拟点击了继续阅读的按钮）
            js = 'document.getElementsByClassName("moreBtn goBtn")[0].click();'
            self.browser.execute_script(js)
            print('等待加载更多...')
            next_area = self.wait.until(EC.presence_of_element_located((By.ID, 'next_doc_box')))
            if next_area:
                print('该页已加载完成！')
        except Exception as e:
            print('加载失败！', e.args)

    def get_title(self):
        title_area = self.browser.find_element_by_class_name('doc-header-title')
        return title_area

    def get_complete_html(self):
        """
        parse_selenium()  return文字文档内容
        parse_pic_url()  return图片文档的图片链接
        都需要得到当前文档页的源码，该方法为两方法重复部分
        :return: 部分源码重复的html源码
        """
        try:
            html = ''
            title_area = self.get_title()
            self.browser.execute_script("arguments[0].scrollIntoView();", title_area)
            # 将标题构造成好识别的字符串放在网页源码开始，以免后面获取标题还需从源码中解析去重
            html += 'title_begin' + title_area.text + 'title_end'
            print('滑回文档头...')
            # 模拟滑动滚动条
            page = self.get_doc_page()
            print('文档共', page, '页')
            a = 0
            while True:
                a += 1
                # 循环滚动滚动条到下一页，每一次滚动都把html加到string类型的html中
                html += self.browser.page_source
                print('正在爬取第', a, '页...')
                self.browser.execute_script("window.scrollBy(0, 1050)")
                time.sleep(0.3)
                if a >= page:
                    break
            return html
        except Exception as e:
            print('Error occured when get_complete_html', e.args)

    def parse_doc(self):
        # selenium库爬取doc类型的文档
        try:
            html = self.get_complete_html()
            doc = pq(html)  # 肯定有重复的部分 全部解析一一解析 各条结果放入list
            divs = doc('.reader-container-inner .mod').items()
            fore_res = []
            # print('去重前:')
            for div in divs:
                for item in div.find('div.reader-txt-layer div.ie-fix > p').items():
                    # print(i,' : ',item.text())
                    fore_res.append(item.text())
            # 列表去重(set方法) 法①--会改变顺序
            '''
            res_list = set(fore_res)  
            print('去重后:')
            for r in res_list:
                print(r.replace(" ", ""))
            '''
            # 列表去重(使用空列表 循环遍历有重复的放入) 法②
            res_list = []
            for s in fore_res:
                if s not in res_list:
                    res_list.append(s)
            str_doc = ''
            for r in res_list:  # 将空串剔除
                if r.strip() != "":  # 空字符串判断
                    str_doc += r.replace("\u2002", " ") + '\n'  # 原网页的空格会变成Unicode字符\u2002
                    # 将稳定标题title和文档内容字符串str_doc写为dict格式，方便存储查看
            title = re.search('title_begin(.*?)title_end', html).group(1)
            doc_dict = {'title': title, 'from_url': self.url, 'type': 'doc', 'content': str_doc}
            return doc_dict
        except Exception as e:
            print('Error occured when parse_doc！', e.args)

    def parse_doc_requests(self):
        """
        # 使用requests库爬取doc类型文档
        requests库请求文json格式内容  较于selenium库更快 爬取内容排版更好看
        :return:
        """
        try:
            content = self.fetch_url(self.url)
            url_list = re.findall('(https.*?0.json.*?)\\\\x22}', content)  # 网页中隐藏的内容链接--较之selenium格式好看
            url_list = [addr.replace("\\\\\\/", "/") for addr in url_list]
            page = self.get_doc_page()
            print('文档共', page, '页')
            result = ''
            for url in url_list[:-int(page)]:  # 截取从头开始到倒数第page个url之前
                # print(url)
                content = self.fetch_url(url)
                y = 0
                txt_list = re.findall('"c":"(.*?)".*?"y":(.*?),', content)
                for item in txt_list:
                    if not y == item[1]:
                        y = item[1]
                        n = '\n'
                    else:
                        n = ''
                    result += n
                    result += item[0].encode('utf-8').decode('unicode_escape', 'ignore')
            # print(result)
            title = self.get_title().text
            doc_dict = {'title': title, 'from_url': self.url, 'type': 'doc', 'content': result}
            return doc_dict
        except Exception as e:
            print('Error occured when parse_txt', e.args)

    def parse_pdf(self):
        """
        这类链接的文档页为纯图片，无法提取到文字
        获取<div class="reader-pic-item">节点 获得节点的style属性值 通过re库解析出文档图片
        :return:返回列表项为dict类型（页索引,页图片链接）
        """
        try:
            html = self.get_complete_html()
            doc = pq(html)  # 肯定有重复的部分 全部解析一一解析 各条结果放入list
            divs = doc('.reader-container-inner .mod').items()
            # print('去重前:')
            fore_list = []
            for div in divs:
                for item in div.find('div.reader-pic-layer div.ie-fix > div.reader-pic-item').items():  # 匹配每一页的文档div
                    attr_style = item.attr('style')
                    fore_pic_url = re.search('\((.*?)\);', attr_style).group(1)  # 解析文档图片链接
                    fore_list.append(fore_pic_url)
            # print('去重后:')
            after_list = []
            for s in fore_list:
                if s not in after_list:
                    after_list.append(s)
            count_pic = 1
            str_pic_doc = 'PDF文档内容为图片，无文字可爬取。图片链接如下：'+'\n'
            for r in after_list:
                str_pic_doc += str(count_pic) + ' 、 ' + r + ' end_url\n'
                count_pic += 1
            title = re.search('title_begin(.*?)title_end', html).group(1)
            pic_doc_dict = {'title': title, 'from_url': self.url, 'type': 'pdf', 'content': str_pic_doc}
            return pic_doc_dict
        except Exception as e:
            print('Error occured when parse_pdf！', e.args)

    def parse_vip_page(self):
        """
        vip内容 看不到全部的结果
        :return:
        """
        try:
            need_money = self.browser.find_element_by_class_name('btn-pay')
            print('Tip: ', need_money.text)  # 该页需要多少money才能解锁
            title_area = self.browser.find_element_by_class_name('doc-title')
            title = title_area.text
            html = self.browser.page_source  # 直接获取当前能看的部分源码，对其内容进行提取
            doc = pq(html)
            divs = doc('.reader-container .reader-page ').items()
            res_txt = ''
            for div in divs:
                for item in div.find('div.reader-txt-layer div.ie-fix > p').items():
                    if item.text().strip() != "":  # 空字符串判断
                        # print(item.text())
                        res_txt += item.text().replace("\u2002", " ") + '\n'
            doc_dict = {'title': title, 'from_url': self.url, 'type': 'vip_doc', 'content': res_txt}
            return doc_dict
        except Exception as e:
            print('Error occured when parse_vip_page！', e.args)

# txt和ppt文档使用requests库爬取
    def get_id(self):
        doc_id = re.search('view/(.*?).html', self.url).group(1)
        return doc_id

    def fetch_url(self, content_url):
        request_content = self.session.get(content_url).content.decode('gbk')
        return request_content

    def parse_txt(self):
        """
        利用requests库对文档的json响应页面进行分析 爬取到的内容更加规范 爬取速度较于selenium动态爬取更快
        :return: 文档内容
        """
        try:
            doc_id = self.get_id()
            txt_url = 'https://wenku.baidu.com/api/doc/getdocinfo?callback=cb&doc_id=' + doc_id
            content = self.fetch_url(txt_url)
            md5 = re.search('"md5sum":"(.*?)"', content).group(1)
            pn = re.search('"totalPageNum":"(.*?)"', content).group(1)
            rsign = re.search('"rsign":"(.*?)"', content).group(1)
            content_url = 'https://wkretype.bdimg.com/retype/text/' + doc_id + '?rn=' + pn + '&type=txt' + md5 + '&rsign=' + rsign
            content = json.loads(self.fetch_url(content_url))
            result = ''
            for item in content:
                for i in item['parags']:
                    result += i['c'].replace('\\r', '\r').replace('\\n', '\n')
            title = self.get_title().text
            txt_dict = {'title': title, 'from_url': self.url, 'type': 'txt', 'content': result}
            return txt_dict
        except Exception as e:
            print('Error occured when parse_txt', e.args)

    def parse_ppt(self):
        doc_id = self.get_id()
        content_url = "https://wenku.baidu.com/browse/getbcsurl?doc_id=" + doc_id + "&pn=1&rn=99999&type=ppt"
        content = json.loads(self.fetch_url(content_url))  # fetch_url()返回str类型
        # print(content, type(content))  # list格式
        pic_url_str = 'PPT文档，无文字内容。图片链接如下：'+'\n'
        for item in content:
            #ppt_item = {'pic_url': item.get('zoom'), 'index': item.get('page')}
            # print(ppt_pic)
            # 转化为适合存入数据库的个数  多条链接合并成一条数据
            pic_url_str += str(item.get('page')) + ' 、 ' + item.get('zoom') + ' end_url\n'
        title = self.get_title().text
        ppt_pic_dict = {'title': title, 'from_url': self.url, 'type': 'ppt', 'content': pic_url_str}
        return ppt_pic_dict

    def run(self):
        """
        方法调度 将爬取内容存入数据库
        :return: 文档标题+'\n'+文档内容 用于测试程序和gui.py显示
        """
        try:
            self.browser.get(self.url)
            get_type_html = self.browser.page_source
            mgc = MongoDBClient()  # 新建数据库对象
            print('已连接到MongoDB数据库！\n')
            doc_type = self.parse_doc_type(get_type_html)
            if doc_type == 'txt' or doc_type == 'doc' or doc_type == 'pdf' or doc_type == 'ppt':
                # 使用requests库不需要点击加载更多 txt、doc以及ppt类型文档使用该方式
                if doc_type == 'txt':
                    print('Tip: 文档类型--txt')
                    txt_content = self.parse_txt()
                    mgc.write_doc_content(txt_content)  # 写入数据库
                    return txt_content.get('title') + '\n' + txt_content.get('content')
                elif doc_type == 'doc':
                    print('Tip: 文档类型--doc')
                    # 以下两行代码是用selenium库实现doc类型文档内容爬取的--爬取到的内容格式不规范，速度慢（暂且淘汰）
                    # self.get_more()
                    # doc_content = self.parse_doc()
                    doc_content = self.parse_doc_requests()
                    mgc.write_doc_content(doc_content)  # 写入数据库
                    return doc_content.get('title') + '\n' + doc_content.get('content')
                elif doc_type == 'pdf':
                    self.get_more()  # selenium库动态爬取
                    print('Tip: 文档类型--pdf')
                    pdf_content = self.parse_pdf()
                    mgc.write_doc_content(pdf_content)  # 写入数据库
                    return pdf_content.get('title') + '\n' + pdf_content.get('content')
                else:
                    print('Tip: 文档类型--ppt')
                    ppt_content = self.parse_ppt()
                    mgc.write_doc_content(ppt_content)  # 写入数据库
                    return ppt_content.get('title') + '\n' + ppt_content.get('content')
            elif doc_type == 'none_type':
                print('Tip: 其他类型文档')
                other_content = self.parse_vip_page()
                mgc.write_doc_content(other_content)
                return other_content.get('title') + '\n' + other_content.get('content')
        except ConnectionError as e:
            print(e.args, '连接超时')
        finally:
            print('已存入数据库！正在断开连接...\n')
            self.browser.close()  # 关闭窗口


if __name__ == '__main__':
    # 需要注意的付费文档链接
    # url = 'https://wenku.baidu.com/view/8c3fd6e66aec0975f46527d3240c844769eaa0a0.html?from=search'
    # 文档内容为图片的链接 type='pdf'
    # url = 'https://wenku.baidu.com/view/542086f2b8f3f90f76c66137ee06eff9aef84916.html?from=search'
    # 普通文字文档 type='doc' 小于50页
    # url = 'https://wenku.baidu.com/view/dd96caed32687e21af45b307e87101f69f31fbd2.html?from=search'

    # ppt文档 type='ppt'
    url = 'https://wenku.baidu.com/view/c1cde6c432687e21af45b307e87101f69f31fb54.html?from=search'
    # txt格式文档
    # url = 'https://wenku.baidu.com/view/cbb4af8b783e0912a3162a89.html?from=search'

    dc = DocContent(doc_url=url)
    print(dc.run())
