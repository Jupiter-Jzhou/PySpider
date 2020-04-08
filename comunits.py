from requests import request, Timeout
from requests.exceptions import SSLError
from urllib3 import disable_warnings, exceptions
from os import listdir, makedirs, system
from os.path import exists, isfile, basename
from time import sleep
from re import findall
from bs4 import BeautifulSoup
from collections import Counter
from lxml import etree
from urllib.request import build_opener, install_opener, ProxyHandler
from multiprocessing import Pool, Manager



def get_ip():
    pass


def check_local_merge(path, path_file_merged):
    b = []
    if isfile(path_file_merged):  # 返回布尔值
        ts_local = False
    else:
        ts_list = listdir(path)
        if ts_list:  # 不为空列表
            ts_local = []
            for ts in ts_list:
                index = findall("(.*).ts", ts)[0]
                ts_local.append(int(index))
        else:
            ts_local = ts_list

        # 整理index_ts 排序 递增          ts_local: 本地所有ts列表 数字
        ts_local.sort()  # 空列表不影响
        # 寻找离散的未下ts
        for i in range(1, len(ts_local)-1):
            i1 = ts_local[i]
            i2 = ts_local[i + 1]
            if i == 0 and i1 != 0:  # 比如只有第一个文件0未下的情况
                lst = [a for a in range(i1)]
                b = b + lst
            elif i1 + 1 != i2:
                lst = [a for a in range(i1 + 1, i2)]
                b = b + lst
    ts_dis = b
    return ts_local, ts_dis


def check_local(path, *, mode=None, path_file_merged=None):
    """检查本地的已下载情况
    :mode "m3u8":
                return: ts_local（列表）   ts文件索引号，int(去0),
    :mode
    ，返回 已下完列表name_done 和 未下完字典name_ing
    一个图集的最后一张照片名含有特殊标记，利用此标记统计已下载的图集名

    """

    if mode is "m3u8":
        ts_local, ts_dis = check_local_merge(path, path_file_merged)
        return ts_local, ts_dis

    else:
        file_list = listdir(path)
        name_done = []  # 本地图集列表
        name_all = []
        pat = "L.jpg"
        for file in file_list:
            fn = file.split('_')
            name_all.append(fn[0])
            if pat in file:  # 判断文件名中含 pat的
                name_done.append(fn[0])
        name_ing = Counter(name_all)  # 统计列表元素，返回字典
        for name in name_done:
            name_ing.pop(name)  # 循环结束 name_dic 就是未下完图集的统计

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


def send_requests(url, *, method="get", need="response",
                  referer=None, origin=None, proxy=None):
    """
    :param url:       目标url
    :param method:    请求的方式，默认是get
    :param proxy:     请求使用的代理，默认是本机IP
    :param need:      表明需要返回的内容，有 response,soup,xpath 可选，
                            response: 返回 response对象
                            soup: 生成BeautifulSoup对象，调用处之后的网页解析用BeautifulSoup
                            xpath: 生成etree对象，调用处之后的网页解析用xpath
    :param referer:   用于构造headers
    :param origin:    用于构造headers
    """

    global response  # return 不能返回比他缩进的变量，故将此变量全局化
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0'}
    if referer is not None:
        headers["referer"] = referer
    if origin is not None:
        headers["origin"] = origin
    if proxy is None:
        proxy = {}
    # request增加代理设置 翻墙时候
    if "127.0.0.1" in proxy.get("https", "") or proxy.get("http", ""):
        opener = build_opener(ProxyHandler(proxy))
        install_opener(opener)

    # 循环控制变量
    verify = True
    timeout = (13, 30)
    while 1:
        try:
            response = request(method, url, headers=headers, proxies=proxy, timeout=timeout, verify=verify)
            response.close()
            if response.status_code != 200:
                print(response.status_code)
                print("\r再次尝试连接", end='')
                continue
            break
        except Timeout:
            print("\r请求超时", end='')
            timeout = (13, 60)
            continue
        except SSLError:
            print("\r关闭verify", end='')
            verify = False
            disable_warnings(exceptions.InsecureRequestWarning)
            continue

    # 选择返回值
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
    想要得到的处理结果：[3 5 6 7 8 9 91] 即所有输入数字（int）的列表，不重复，升序
    """
    if input_num is '':
        input_list = []
    else:
        input_list = input_num.split()  # 以空格分割
        lx = []  # 连续数字 如：[1-3,3-6]
        lst = []  # 连续数字展开后 如 [1,2,3,3,4,5,6]
        for i in input_list:
            if '-' in i:
                lx.append(i)  # 寻找 连续数字
        for i in lx:  # 处理 连续数字
            input_list.remove(i)  # 去除源列表中连续的表达式的元素 如：1-3
            i = i.split('-')
            i = [n for n in range(int(i[0]), int(i[-1]) + 1)]
            lst = lst + i
        input_list = [int(i) for i in input_list]   # int型
        input_list = input_list + lst  # 融合两列表
        input_list = list(set(input_list))  # 去重
        input_list.sort()  # 排序：从小到大

    return input_list


def choice_download_path(path, path_default):
    """
    用户输入地址则使用输入地址，否则使用默认地址
    无法判断输入地址格式是否正确
    """
    if path is '':
        path = path_default
    if not exists(path):
        makedirs(path)
    return path


def merge_files(path_dir, path_file, total):
    """
    :param path_dir: 需合并文件所在文件夹的路径
    :param path_file: 合成文件的存储路径
    :param total: 需合并文件的理想总数
    """

    name_file = basename(path_file)
    # 判断ts文件是否下全了
    if len(listdir(path_dir)) == total:
        print("{1}开始合并：{0}{1}".format(name_file, "*" * 25))
        # 合并ts
        merge = r'copy /b "{0}\*.ts" "{1}"'.format(path_dir, path_file)
        system(merge)
        if exists(path_file):
            # 删除ts
            delete = r'rd /S/Q "{0}"'.format(path_dir)
            system(delete)
            sleep(0.5)  # 删除文件夹有一定时间
            if not exists(path_dir):
                print("{1}合并成功：{0}{1}".format(name_file, "*" * 25))
            else:
                print("删除失败")
        else:
            print("合并失败")
    else:
        print("ts文件未下载完全")


class Multiprocess(object):
    def __init__(self, **kwargs):
        self.referer = kwargs.get("referer", None)
        self.origin = kwargs.get("origin", None)
        self.proxy = kwargs.get("proxy", None)

    def process_console(self, path_dir, download_list, length, *, url_pat, pat_mode="naked"):
        """
        :param path_dir: 下载文件的存储文件夹
        :param download_list: 需要下载文件的索引列表，int型数字
        :param length: 补0用的，为了ts文件名齐整，方可正确合并
        :param url_pat: 需要下载文件的url模板，与download_list中的数字组合，即可构成完整的url
        :param pat_mode: url模板的索引要不要补0 : "zero":要补零; "naked": 不补零
        """

        # 进程数
        pool = Pool(30)
        # 进程数据共享
        m = Manager()
        d = m.list()
        d.extend([0, len(download_list)])
        try:
            # ts生成器
            for i in download_list:
                i = str(i)
                # n为需要添加0的个数
                n = length - len(i)
                zero = "0" * n + i          # 文件名要补齐，不然合并出错
                if pat_mode == "zero":
                    index = zero
                else:
                    index = i
                url_file = url_pat.format(index)
                # 需下载文件的路径
                path_file = path_dir + r'\\' + "{0}.ts".format(zero)
                # 开启异步任务
                pool.apply_async(self.download, (url_file, path_file, d))
        finally:
            pool.close()
            pool.join()

    def download(self, url, path, d):
        """
        :param d: 多进程用的计数器
        """
        args = {
                "referer": self.referer,
                "origin": self.origin,
                "proxy": self.proxy,
                "need": "response"
                }
        ts_stream = send_requests(url, **args)
        with open(path, "wb") as f:
            f.write(ts_stream.content)
            f.close()
        d[0] += 1
        show_bar(d[0], d[1])
