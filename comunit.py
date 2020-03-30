
import requests
from bs4 import BeautifulSoup
import os
from collections import Counter
from time import sleep
from lxml import etree


def get_ip():
    pass


def check_local(path):
    """
    检查本地的已下载情况，返回 已下完列表name_done 和 未下完字典name_ing
    一个图集的最后一张照片名含有特殊标记，利用此标记统计已下载的图集名
    """
    file_list = os.listdir(path)
    name_done = []                # 本地图集列表
    name_all = []
    pat = "L.jpg"
    for file in file_list:
        fn = file.split('_')
        name_all.append(fn[0])
        if pat in file:                 #判断文件名中含 pat的
            name_done.append(fn[0])
    name_ing = Counter(name_all)       #统计列表元素，返回字典
    for name in name_done:
        name_ing.pop(name)           #循环结束 name_dic 就是未下完图集的统计

    return name_done, name_ing


def is_download(pics_dic, name_done_list, name_ing_dic):
    """
    判断某页本地下载情况
    返回 需要下载图集的2个字典 ： {名：local数}  &  {名：url}
    """
    name_pics_list = list(pics_dic)
    name_ing_list = list(name_ing_dic)
    done = []
    doing = {}
    undo = {}

    for name_pics in name_pics_list:
        if name_pics in name_done_list:
            done.append(name_pics)
        elif name_pics in name_ing_list:
            doing[name_pics] = name_ing_dic[name_pics] + 1
        else:
            undo[name_pics] = 1

    local_dic = undo.copy()
    local_dic.update(doing)  # 融合两字典
    for name in done:
        pics_dic.pop(name)
        print("已经下载：", name)

    return local_dic, pics_dic


def send_requests(url, referer, proxy={}, need="soup",mode="loop"):   # 设置默认参数

    """发送请求，返回对象： response or soup"""

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0',
        'Referer': referer
              }
    if mode is "loop":
        while 1:
            try:
                response = requests.get(url, proxies=proxy, headers=headers, timeout=(13,16)) #, timeout=13
                response.close()
                while response.status_code != 200:
                    print("\r再次尝试连接", end='')
                    response = requests.get(url, proxies=proxy, headers=headers)
                    response.close()
                break
            except:
                print("\r重新请求", end='')
    elif mode is "empty":
        response = requests.get(url, proxies=proxy, headers=headers, timeout=(13, 16))  # , timeout=13
        response.close()

    if need is "response":
        return response
    elif need is "soup":
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    elif need is "xpath":
        # tree = etree.parse('xpath.html')  # 本地文件打开方式
        tree = etree.HTML(response.text)
        return tree


def show_bar(num, nums):

    """下载进度条"""

    max_tep = 50  # 进度条的长度
    a = int(num / nums * max_tep // 1)
    b = '[' + '>' * a + ' ' * (max_tep - a) + ']'
    c = str(int(100 / max_tep * a))
    print('\r{0}{1}%'.format(b, c), end='')
    if num == nums:
        print('')


def deal_input_num(input_list):

    """ 返回的数字 是字符串类型"""

    input_list = input_list.split()  # 以空格分割
    lst = []
    rm = []
    for i in input_list:
        if '-' in i:
            rm.append(i)  # 寻找 连续月份
    for i in rm:  # 处理 连续月份
        input_list.remove(i)
        i = i.split('-')
        i = [str(n) for n in range(int(i[0]), int(i[-1]) + 1)]  # 创建字符列表
        lst = lst + i
    input_list = input_list + lst  # 融合两列表
    input_list = list(set(input_list))  # 去重

    return input_list

