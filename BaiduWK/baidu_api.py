# 在flask中，请求消息被封装到request对象--是一个全局的，在任何地方都可以使用 （与requests库区别    ）
from flask import Flask, render_template, request  # render_template()方法可以渲染模板
from flask_bootstrap import Bootstrap
from flask_paginate import Pagination, get_page_parameter  # 类函数,获取当前翻页的参数
from Question_bank.BaiduWK.write_mongo import MongoDBClient
from Question_bank.BaiduWK.write_file import WriteFile

app = Flask(__name__)
# app.debug = True
# app.config['JSON_AS_ASCII'] = False  # 解决urls_content()方法return的jsonify()中文乱码
bootstrap = Bootstrap(app)
mgc = MongoDBClient()
wf = WriteFile()
global_page = None  # 不同路由直接传参  获取内容页的当前页码，通过数据库查询语句找到当前页的'from_url'


@app.route("/")
def index():
    return render_template('api_web.html')


@app.route("/links")
def links():
    collection = mgc.db.co_urls  # pymongo.cursor.Cursor object
    per_page = int(request.args.get('per_page', 10))  # 每一页显示数量
    # 获取当前为第几页
    page = request.args.get(get_page_parameter(), type=int, default=1)
    url_count = collection.count()
    prev_label = '上一页'
    next_label = '下一页'
    # 使用的是Boostrap3的CDN, 那么就要设置bs_version=3, 否则会无法正常显示
    pagination = Pagination(bs_version=3, page=page, total=url_count, prev_label=prev_label, next_label=next_label,
                            per_page=per_page)
    # 将collection对象也传回前台，数据库数据--根据页码动态查询实现分页显示
    return render_template('urls_page.html', page=page, per_page=per_page, count=url_count, collection=collection,
                           pagination=pagination)


@app.route("/contents")
def contents():  # 内容显示使用<pre>节点 不然无法正常显示内容排版
    global global_page
    collection = mgc.db.co_doc
    doc_count = collection.count()
    per_page = int(request.args.get('per_page', 1))  # 每一页显示数量
    # 获取当前为第几页
    page = request.args.get(get_page_parameter(), type=int, default=1)
    prev_label = '上一页'  # 默认为'<<'
    next_label = '下一页'
    # 使用的是Boostrap3的CDN, 那么就要设置bs_version=3, 否则会无法正常显示
    pagination = Pagination(bs_version=3, page=page, total=doc_count, prev_label=prev_label, next_label=next_label,
                            per_page=per_page)
    current_page = pagination.page
    global_page = current_page
    return render_template('contents_page.html', page=page, per_page=per_page, collection=collection,
                           pagination=pagination, wf=wf)


@app.route("/practice")
def practice():  # 练习页 查询显示经过数据分离的选项和答案
    global global_page
    collection = mgc.db.co_doc
    for item in collection.find({}).skip((global_page - 1)).limit(1):
        from_url = item.get('from_url')
        analysis_result = wf.doc_analysis(from_url)
        return render_template('content_practice.html', analysis_result=analysis_result)


@app.route("/write_url")
def write_url():
    tip_str_md = wf.write_urls_md()
    return '<center><h3><a href="/" style="text-decoration: none;">返回首页</h3></center>' \
           '<p align="center" >' + tip_str_md + '</p>' \
           '<script>alert("已存储！")</script>'


@app.route("/write_doc")
def write_doc():
    global global_page  # 路由contents传来的参 根据当前页找到文档链接
    collection = mgc.db.co_doc
    for item in collection.find({}).skip((global_page - 1)).limit(1):
        from_url = item.get('from_url')
        str_doc = wf.write_doc_md(from_url)
        print(from_url, str_doc)
        return '<center><h3><a href="/" style="text-decoration: none;">返回首页</h3></center>' \
               '<p align="center" >' + str_doc + '</p>' \
                                                 '<script>alert("已存储！")</script>'


@app.route("/write_ppt")
def write_ppt():
    global global_page  # 路由contents传来的参 根据当前页找到文档链接
    collection = mgc.db.co_doc
    for item in collection.find({}).skip((global_page - 1)).limit(1):
        from_url = item.get('from_url')
        str_ppt = wf.write_ppt_pic(from_url)
        print(from_url, str_ppt)
        return '<center><h3><a href="/" style="text-decoration: none;">返回首页</h3></center>' \
               '<p align="center" >' + str_ppt + '</p>' \
                                                 '<script>alert("已存储！")</script>'


if __name__ == "__main__":
    app.run()
