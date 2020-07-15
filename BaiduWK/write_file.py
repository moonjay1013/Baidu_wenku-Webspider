import os
import re
from requests import session
from Question_bank.BaiduWK.write_mongo import MongoDBClient


class WriteFile:
    def __init__(self):
        self.mgc = MongoDBClient()
        # 文件存储路径
        self.path = r'D:\PycharmProjects\1_11\Question_bank\BaiduWK'

    def write_urls_md(self):
        os.chdir(self.path)
        collection = self.mgc.db['co_urls']
        url_count = collection.find({}).count()
        all_url = collection.find({})
        url_root = 'URLs'
        if not os.path.exists(url_root):  # 根目录
            os.makedirs(url_root)
        os.chdir(url_root)
        count_str = '###共'+str(url_count)+'页文档链接'+'\n'
        content = ''
        count = 0
        page_count = 1
        for i in all_url:
            if count % 10 == 0:  # 10个链接一页
                page_str = '####第'+str(page_count)+'页\n'
                page_count += 1
                content += page_str
            title = '##### '+str(count+1)+'、'+i['title']+'\n'
            url = '>'+'['+i['url']+']('+i['url']+' "'+i['title']+'"'+')\n'
            content += title+url
            count += 1
        # print(count_str+content)
        if not os.path.exists('doc_urls.md'):
            with open('doc_urls.md', 'a+', encoding='utf-8') as f:  # 写入md文件
                f.write(count_str + content)
            # 文件所在的绝对路径os.path.abspath('doc_urls.md'))
            return "已写入到" + os.path.abspath('doc_urls.md')
        else:
            return '文件已存在文件夹：' + os.path.dirname(os.path.abspath('doc_urls.md'))

    def write_doc_md(self, from_url):
        """
        无法将图片文档的图片写为jpg格式存到本地 就将其写为md格式  可以方便查看
        还需要优化
        :return:
        """
        os.chdir(self.path)
        collection = self.mgc.db['co_doc']
        # doc_count = collection.find({}).count()
        # count_str = '###共' + str(doc_count) + '个文档' + '\n'
        doc = collection.find({'from_url': from_url})
        url_root = 'DOCs'
        if not os.path.exists(url_root):  # 根目录
            os.makedirs(url_root)
        os.chdir(url_root)
        # 全部数据一次性写入md文件
        '''
        for i in all_doc:
            title = '##### '+'    ' + i['title'] + '\n'
            doc_pic_url1 = i['content'].replace('、 https', '![](https')
            doc_pic_url2 = doc_pic_url1.replace(' end_url', ' "文档图片")\n')
            content = title + '>' + doc_pic_url2
            file_name = i['title'] + '.md'
            if not os.path.exists(file_name):
                with open(file_name, 'a+', encoding='utf-8') as f:  # 写入md文件
                    f.write(content)
            else:
                print('文件'+file_name+'已存在！')
        '''
        for i in doc:
            title = '##### ' + i['title'] + '\n'
            content = title + i['content']
            if re.search("http.*?end_url", content):
                pdf_pic_url = content.replace('、 https', '![](https').replace(' end_url', ' "文档图片")\n')
                content = pdf_pic_url
            file_name = i['title'] + '.md'
            if not os.path.exists(file_name):
                with open(file_name, 'a+', encoding='utf-8') as f:  # 写入md文件
                    f.write(content)
                return "已写入到" + os.path.abspath(file_name)
            else:
                return '文件' + file_name + '已存在文件夹：' + os.path.dirname(os.path.abspath(file_name))

    def write_ppt_pic(self, from_url):
        os.chdir(self.path)
        collection = self.mgc.db['co_doc']
        result = collection.find_one({'from_url': from_url})
        title = result.get('title')
        content = result.get('content')
        pic_urls = re.findall('https:.*?jpg.*\d', content)
        len_count = len(pic_urls)
        if not os.path.exists('Pic_Doc\\'+title):  # 根目录
            os.makedirs('Pic_Doc\\'+title)
        os.chdir('Pic_Doc\\'+title)
        i = 1
        for url in pic_urls:
            # print(url)  # 每张图片的url
            pic_name = str(i) + '.jpg'
            response = session().get(url)
            if not os.path.exists(pic_name):
                with open(pic_name, 'wb') as f:
                    f.write(response.content)
                print('  [下载进度]:%.2f%%' % float(i / len_count * 100) + '\r')
                i += 1
            else:
                break
        return str(len_count) + '张ppt图片已下载到' + os.path.dirname(os.path.abspath('1.jpg'))

    def doc_analysis(self, from_url):
        collection = self.mgc.db['co_doc']
        result = collection.find({'from_url': from_url})
        for i in result:
            content_str = i['content']
            # 第一步 格式规整
            if re.search('答案：[ABCD]', content_str):
                after_str_1 = content_str.replace("：", ":").replace("答案", "答").replace("解答", "答").replace("答:","Answer:")
                after_str = after_str_1.replace("）", ")").replace("（", "(")
                # 第二步 字段匹配
                answers = re.findall('Answer:(.*)\s', after_str)
                # 第三步 清除答案 练习页选项匹配
                after_re_str = re.sub('Answer:(.*)\s', '', after_str)
                pattern = re.compile('[abcd]\s\)|[abcd]\)|[ABCDE]、|[ABCDE]\s、|\s[ABCDE]\s')
                pattern_match = re.findall(pattern, after_re_str)  # 选项匹配（有重复）
                # 去重（将所有匹配到的选项放入list中，因为不必考虑顺序，故可以使用set方法去重）
                list_pa = []
                for pa_ma in pattern_match:
                    list_pa.append(pa_ma)
                after_list = set(list_pa)
                # 为所有的选项前加上 选择框 供用户练习使用
                for item in after_list:
                    after_re_str = after_re_str.replace(item, '<input type="checkbox"/>' + item)
                question_dict = {"title": i['title'], "content": after_re_str}
            else:
                after_str = content_str.replace("）", ")").replace("（", "(").replace("．", ".")
                answers = re.findall('\(\s[ABCD]\s\)|\(\s[ABCD],[ABCD]\s\)|\(\s[ABCD]\s[ABCD]\s\)', after_str)
                after_re_str = re.sub('\(\s[ABCD]\s\)|\(\s[ABCD],[ABCD]\s\)|\(\s[ABCD]\s[ABCD]\s\)', '', after_str)
                pattern = re.compile('[ABCD]\.|[ABCD]、|[ABCD]\.\s|[ABCD]、\s|[ABCD]\)')
                pattern_match = re.findall(pattern, after_re_str)
                list_pa = []
                for pa_ma in pattern_match:
                    list_pa.append(pa_ma)
                after_list = set(list_pa)
                # 为所有的选项前加上 选择框 供用户练习使用
                for item in after_list:
                    after_re_str = after_re_str.replace(item, '<input type="checkbox"/>' + item)
                question_dict = {"title": i['title'], "content": after_re_str}
            # 第四步 将答案提取出来
            i_1, i_2, i_3 = 1, 1, 1
            answer_list = []
            answer_dict = {}
            for answer in answers:
                after_result = answer.replace(" ", "").replace('(', '').replace(')', '')
                res_len = len(after_result)
                if res_len == 1:
                    sub_tit = "单选题"
                    answer_dict = {"sub_tit": sub_tit, "index": i_1, "answer": after_result}
                    i_1 += 1
                elif 1 < res_len <= 4:
                    sub_tit = "多选题"
                    answer_dict = {"sub_tit": sub_tit, "index": i_2, "answer": after_result}
                    i_2 += 1
                elif res_len > 4:
                    sub_tit = "简答题"
                    answer_dict = {"sub_tit": sub_tit, "index": i_3, "answer": after_result}
                    i_3 += 1
                answer_list.append(answer_dict)
            analysis_list = [question_dict, answer_list]
            return analysis_list


if __name__ == '__main__':
    wf = WriteFile()
    result = wf.doc_analysis('https://wenku.baidu.com/view/52f8185c905f804d2b160b4e767f5acfa1c783fe.html?from=search')
    print(result[0].get('content'))
    for i in result[1]:
        print(i)
