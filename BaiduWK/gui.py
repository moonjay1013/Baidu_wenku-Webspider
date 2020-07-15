"""
如何让PIL读取jpg文件生成的内存对象被tkinter处理？
利用PIL提供了一个PhotoImage类--与tkinter包里的同名类接口兼容，
所以可以直接将PIL生成的PhotoImage对象赋给tkinter中能接收PhotoImage入参的所有控件（比如Label、Canvas等）
"""

from tkinter import *
import tkinter as tk
from tkinter import ttk  # 下拉菜单
import tkinter.messagebox as mb  # 对话框
from PIL import Image, ImageTk
import re
from Question_bank.BaiduWK.crawl_urls import DocURLS
from Question_bank.BaiduWK.crawl_doc import DocContent
from Question_bank.BaiduWK.verify import VerifyRobots
from Question_bank.BaiduWK.write_mongo import MongoDBClient  # MySQL数据库类
import Question_bank.BaiduWK.baidu_api as bq
from Question_bank.BaiduWK.setting import WIDTH, HEIGHT

# 新建窗体对象
window = tk.Tk()
# 窗体在屏幕上的显示位置以及大小
screenwidth = window.winfo_screenwidth()
screenheight = window.winfo_screenheight()
size = '%dx%d+%d+%d' % (WIDTH, HEIGHT, (screenwidth - WIDTH) / 2, (screenheight - HEIGHT) / 2)
window.geometry(size)  # width乘height+x+y--窗体的尺寸
window.title('BaiduWK Crawler')
window.configure({'background': 'gray'})  # 窗体背景颜色
window.resizable(False, False)  # 窗口大小(width，height)是否可调
# 定义区域，把全局分为一、page_tip层、index_tip层、二、三、四层
frame_top = tk.Frame(width=350, height=120)
frame_page = tk.Frame(width=350, height=50)
frame_index = tk.Frame(width=350, height=30)
frame_second = tk.Frame(width=350, height=50)
frame_third = tk.Frame(width=350, height=50)
frame_bottom = tk.Frame(width=350, height=60)
# 图片（top）
pilImage = Image.open("./image/BaiduWK.png")
tkImage = ImageTk.PhotoImage(image=pilImage)
canvas = tk.Canvas(frame_top)
canvas.create_image(175, 60, image=tkImage)  # position--175,60
canvas.grid()


# page_tip层===提示信息 测试按钮 选页下拉
def get_page():  # 对下拉菜单进行填充
    str_kw = find_name.get()
    if str_kw == "":
        mb.showwarning('', '请先输入关键字！')
    elif str_kw != "":
        vr = VerifyRobots(str_kw)
        str_index_page = vr.run()
        index_tip = tk.Label(frame_index, text=str_index_page)
        index_tip.grid(row=0, column=0, padx=30, pady=10)
        max_page = int(re.search('-.*?(\d+).*?', str_index_page).group(1))
        page_list = []
        page = 1
        while page <= max_page:
            str_page = str(page)
            page_list.append(str_page)
            page += 1
        cmb["values"] = page_list
        cmb.current(max_page - 1)  # 选择第最后一个(类似数组下标从0开始所有选择最后一个要减1)


def show_msg(*args):  # 返回选中的页码
    return_val = cmb.get()
    return return_val


test_btn = tk.Button(frame_page, text="测试连接", command=get_page)
page_tip = tk.Label(frame_page, text="页数：")
comvalue = tk.StringVar()  # 窗体自带的文本，新建一个值
cmb = ttk.Combobox(frame_page, textvariable=comvalue)  # 初始化
cmb.bind("<<ComboboxSelected>>", show_msg)
test_btn.grid(row=0, column=0, padx=30, pady=20)
page_tip.grid(row=0, column=1, padx=10, pady=10)
cmb.grid(row=0, column=2, padx=0, pady=10)
# 第二层区
find_tip = tk.Label(frame_second, text="请输入关键字：")
string = tk.StringVar()
string.set('')
find_name = tk.Entry(frame_second, textvariable=string)
find_tip.grid(row=0, column=0, padx=15, pady=30)
find_name.grid(row=0, column=1, padx=0, pady=30)

size_urls = '%dx%d+%d+%d' % (WIDTH, HEIGHT, 0, (screenheight - HEIGHT) / 2)
size_content = '%dx%d+%d+%d' % (WIDTH, HEIGHT, 2 * WIDTH, (screenheight - HEIGHT) / 2)


def dialog(size):
    """
    # 定义长在窗口上的窗口
    :return:
    """
    detail_win = tk.Toplevel(window)
    detail_win.geometry(size)
    detail_win.title('detail')
    detail_win.resizable(False, False)  # 窗口大小(width，height)是否可调
    s1 = tk.Scrollbar(detail_win)
    s1.pack(side=RIGHT, fill=Y)
    # HORIZONTAL 设置水平方向的滚动条，默认是竖直
    s2 = tk.Scrollbar(detail_win, orient=HORIZONTAL)
    s2.pack(side=BOTTOM, fill=X)
    # width 单行可见的字符 ; height 显示的行数
    text = tk.Text(detail_win, width=100, font='幼圆', spacing1=3, spacing3=3, wrap=None, height=100,
                   yscrollcommand=s1.set, xscrollcommand=s2.set)
    text.pack()
    detail_win.grid_propagate(0)
    s1.config(command=text.yview)
    s2.config(command=text.xview)
    return text


# 从文本输入框获取关键字  通过关键字爬取文档链接  存入数据库
def get_url():
    str_kw = find_name.get()  # 获取关键字
    str_page = show_msg()  # 下拉菜单获取页数
    str_url = ''  # 显示链接的窗体显示的字符串
    page_tip = '关键字:' + str_kw + '爬取页数:' + str_page + '\n'
    str_url += page_tip
    bd_wk = DocURLS(str_kw)  # 新建crawl_urls.py的类
    mgc = MongoDBClient()  # 新建write_mongo.py的类
    print('已连接到MongoDB数据库')
    # print(bd_wk.get_pure_urls()) # 纯url链接的list
    if str_kw.strip() != "" and str_page.strip() != "":
        text = dialog(size_urls)
        for i in bd_wk.get_all_urls(str_page):
            # print(i)  # dict类型
            mgc.write_doc_urls(i)
            str_url = i.get('title') + ' : ' + i.get('url') + '\n'
            text.insert(INSERT, str_url)
        print('已存入，断开连接...')
    elif str_kw.strip() == "" and str_page.strip() != "":
        mb.showwarning('', '关键字为空！')
    elif str_page.strip() == "" and str_kw.strip() != "":
        mb.showwarning('', '请选择页数！')
    else:
        mb.showwarning('', '请输入关键字！点击"测试"，选择页数，最后点击"确认"按钮')


submit_btn = tk.Button(frame_second, text="确认", command=get_url)  # command绑定事件get_url()
submit_btn.grid(row=0, column=2, padx=25, pady=0)
# 第三层区
get_link_tip = tk.Label(frame_third, text=" 请输入链接  ：")
string = tk.StringVar()
string.set('')
link_name = tk.Entry(frame_third, textvariable=string)
get_link_tip.grid(row=0, column=0, padx=15, pady=25)
link_name.grid(row=0, column=1, padx=0, pady=25)


# 从文本输入框文档链接  通过关键字解析文档页  存入数据库
def get_content():
    str_link = link_name.get()  # 获取输入的链接
    if str_link.strip() != "":
        if re.match('^https.*?search', str_link):
            dc = DocContent(str_link)
            text = dialog(size_content)
            text.insert(INSERT, dc.run())  # 数据库写入封装到了run_selenium()方法中
        elif re.match('^https.*?view.*?html', str_link):
            dc = DocContent(str_link)
            text = dialog(size_content)
            text.insert(INSERT, dc.run())
        else:
            mb.showwarning('', '链接格式错误！')
    else:
        mb.showwarning('', '链接为空！')


link_btn = tk.Button(frame_third, text="爬取", command=get_content)  # command绑定事件get_content()
link_btn.grid(row=0, column=2, padx=25, pady=0)
# 底部区
help_tip = tk.Label(frame_bottom, text="*数据存入数据库，WEB页面查看爬取结果", fg='red')
help_tip.configure({'font': '隶书, 10'})
help_tip.grid(row=0, column=0, padx=15, pady=15)


# 打开web按钮执行的方法 主要功能是运行baidu_api.py 打开本地5000端口的flask--WebUI
def run_web():
    bq.app.run()


web_btn = tk.Button(frame_bottom, text="打开WEB", command=run_web)
web_btn.grid(row=0, column=1, padx=0, pady=0)
# 容器布局 固定容器大小
frame_top.grid(row=0, column=2, padx=60)
frame_page.grid(row=1, column=2, padx=50)
frame_index.grid(row=2, column=2, padx=30)
frame_second.grid(row=3, column=2, padx=50, ipady=1)
frame_third.grid(row=4, column=2, padx=50, ipady=1)
frame_bottom.grid(row=5, column=2, padx=60)
frame_top.grid_propagate(0)
frame_page.grid_propagate(0)
frame_index.grid_propagate(0)
frame_second.grid_propagate(0)
frame_third.grid_propagate(0)
frame_bottom.grid_propagate(0)

window.mainloop()  # 运行显示GUI
