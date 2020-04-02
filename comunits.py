
import requests
import os
import re
from bs4 import BeautifulSoup
from collections import Counter
from time import sleep
from lxml import etree


def get_ip():
    pass


def check_local(path, *, mode=None, **kwargs):
    """检查本地的已下载情况
    :mode "m3u8":
                return: index_ts（列表）   ts文件索引号，int(去0),
    :mode
    ，返回 已下完列表name_done 和 未下完字典name_ing
    一个图集的最后一张照片名含有特殊标记，利用此标记统计已下载的图集名

    """

    if mode is "m3u8":
        path_video = kwargs["path_episode"]           # 已经合成的影片名
        b = []
        if os.path.isfile(path_video):                     # 返回布尔值
            index_ts = False

        else:
            ts_list = os.listdir(path)
            index_ts = []
            for ts in ts_list:
                index = re.findall(r"(\d{6}).ts", ts)        # 使用ts变量，因为file就是ts文件
                if index is not []:
                    index = index[0]    # 字符串：6个数字
                    # 去零
                    index_ts.append(int(index))
                else:
                    print("{0}提取失败".format(ts))
            # 整理index_ts 排序 递增
            index_ts.sort()
            for i in range(len(index_ts)-1):
                i1 = index_ts[i]+1
                i2 = index_ts[i+1]
                if i1 != i2:
                    lst = [a for a in range(i1, i2)]
                    b = b + lst
        return index_ts, b

    else:
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
    """判断某页本地下载情况
    两类参数：一是从网页来的pic_dic,代表要下的内容；而是本地的下载情况，name_done_list(已经下完的图集)，name_ing_dic()
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


def send_requests(url, *, method="get", need="soup", mode="loop",
                  referer=None, origin=None, proxy=None):

    """
    :param url:       目标url
    :param method:    请求的方式，默认是get
    :param proxy:     请求使用的代理，默认是本机IP
    :param need:      表明需要返回的内容，有 response,soup,xpath 可选，
                            response: 返回 response对象
                            soup: 生成BeautifulSoup对象，调用处之后的网页解析用BeautifulSoup
                            xpath: 生成etree对象，调用处之后的网页解析用xpath
    :param mode:       请求的模式，有 loop,empty 可选
                            loop: 当请求因为连接超时或读超时而没有成功，则一直请求，直至请求成功，期间没有更换 IP
                            empty: 无论成败，只请求一次
    :param referer:   用于构造headers
    :param origin:    用于构造headers
    """

    global response    # return 不能返回比他缩进的变量，故将此变量全局化
    if proxy is None:
        proxy = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0',
        'Referer': referer,
        'origin': origin
              }

    if mode is "loop":
        while 1:
            try:
                response = requests.request(method, url, headers=headers, proxies=proxy, timeout=(13, 30))
                response.close()
                while response.status_code != 200:
                    print("\r再次尝试连接", end='')
                    response = requests.request(method, url, headers=headers, proxies=proxy, timeout=(13, 30))
                break
            except requests.Timeout:
                print("\r重新请求", end='')

    elif mode is "empty":
        response = requests.request(method, url, headers=headers, proxies=proxy, timeout=(13, 30))
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


def deal_input_num(input_num):

    """ 数字处理from 控制台的用户输入
    从控制台输入数字如：3 91 5-9 8
    每个元素以空格间隔，元素形态有两种：单个数字（如 3 91）和连续范围（5-9）
    想要得到的处理结果：[3 5 6 7 8 9 91] 即所有输入的数字(字符串)，不重复，升序
    """

    input_list = input_num.split()  # 以空格分割
    lx = []               # 连续数字 如：[1-3,3-6]
    lst = []              # 连续数字展开后 如 [1,2,3,3,4,5,6]
    for i in input_list:
        if '-' in i:
            lx.append(i)  # 寻找 连续月份
    for i in lx:                 # 处理 连续月份
        input_list.remove(i)    # 去除源列表中连续的表达式的元素 如：1-3
        i = i.split('-')
        i = [n for n in range(int(i[0]), int(i[-1]) + 1)]
        lst = lst + i
    input_list = input_list + lst                  # 融合两列表
    input_list = list(set(input_list))             # 去重
    input_list.sort()                              # 排序：从小到大
    input_list = [str(i) for i in input_list]      # 元素转字符串格式

    return input_list


def choice_path(path, path_default):

    # 判断存储地址
    if path is '':
        path = path_default
    if not os.path.exists(path):
        os.makedirs(path)
    return path

