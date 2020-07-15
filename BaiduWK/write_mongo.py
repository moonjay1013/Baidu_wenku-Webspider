# --向MongoDB中存储通过GUI运行爬取的数据
from Question_bank.BaiduWK.setting import MongoDB_HOST, MongoDB_PORT
import pymongo


class MongoDBClient:
    def __init__(self, host=MongoDB_HOST, port=MongoDB_PORT):
        self.client = pymongo.MongoClient(host=host, port=port)  # ('mongodb://localhost:27017/')
        self.db = self.client.spiders  # 存入数据库spiders

    def write_doc_urls(self, data):
        """
        将craw_urls.py生成的链接list循环遍历存入MongoDB
        :return:
        """
        # 创建集合（co_urls: 文档链接）
        collection = self.db['co_urls']
        if collection.insert_one(data):
            print('Success write a piece of data')
        else:
            print('Failed to save!!!')

    def write_doc_content(self, data):
        """
        将craw_doc.py生成的doc内容list循环遍历存入MongoDB
        :return:
        """
        # 创建集合（co_doc: 文档链接）
        collection = self.db['co_doc']
        if collection.insert_one(data):
            print('Success write a piece of data')
        else:
            print('Failed to save!!!')
