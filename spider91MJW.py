import comunits
from re import X, findall, search
from urllib.parse import urljoin, unquote
from multiprocessing import Pool, freeze_support, Manager
from lxml import etree
from os import listdir, makedirs, system
from os.path import join, exists
from time import sleep


# 网站主页
url_home = "https://91mjw.com"
# 下载 M3U8 ts 时的请求头的origin
url_origin = "https://sp.lujiahb.com"

# 存储路径
path_default = r"E:\CodeStore\movie"
# 本地存储地址
path_download = ""
# url
url_info = ""


def get_info():
    """从美剧详情页获取
    :return
        name_section (str): 美剧名，带季度
        episode_dic（字典）: 第几集:url的关键部分
        info_section（列表）: 导演，演员，评分等信息
        introduce（字符串）: 剧情介绍
    """

    tree = comunits.send_requests(url_info, referer=url_home, need="xpath")

    # 美剧名
    name_section = tree.xpath('//h1[@class="article-title"]//text()')[0]
    name_section = findall("《(.*)》", name_section)[0]
    # print(name_section)

    # 每集url线索,第几集
    id_epis = tree.xpath('//a[@onclick="play(this)"]/@id')
    key_epis = ["/vplay/" + i + ".html" for i in id_epis]
    name_epis = tree.xpath('//a[@onclick="play(this)"]/text()')
    name_epis = [int(findall("第(.*)集", i)[0]) for i in name_epis]
    # print(id_epis, name_epis, sep="\n")
    episode_dic_main = dict(zip(name_epis, key_epis))

    # 影片信息
    div = tree.xpath("//div[@class='video_info']")[0]
    # 将lxml.etree._Element转化成字符串
    div = etree.tostring(div, encoding="utf8")
    div = div.decode("utf8")
    # print(div)

    # 预处理字符串，后正则
    div = div.replace("</strong>", '').replace("<br/>", '')
    info_section = findall("<strong>(.*)", div)
    # for i in info_section:
    #     print(i)

    # 剧情简介
    introduce = tree.xpath('//p[@class="jianjie"]/span/text()')[0]
    # print(introduce)

    return name_section, episode_dic_main, info_section, introduce


def get_m3u8(url_play):
    """从播放页面找出第一个M3U8的url: url_m3u8
    几个播放源几个，几个m3u8
    """
    # 主线下的vid
    obj = comunits.send_requests(url_play, referer=url_info, need="xpath")
    script = obj.xpath('//section[@class="container"]/script[@type="text/javascript"]/text()')[0]
    # 提取vid
    vid = findall("vid.*?=(.*);", script)
    vid = vid[0].strip()
    vid = eval(vid).strip()
    # url解码
    url_m3u8 = unquote(vid)

    # 找到备用源和独家源的每集播放页的url
    play_container = obj.xpath('//div[@id="playcontainer"]//section')
    episode_dic_list = []                  # 其元素是每个源下的集数的字典{name:key}
    for s in play_container[1:]:
        name_epis = s.xpath('./a/text()')
        name_epis = [int(findall("第(.*)集", i)[0]) for i in name_epis]
        key_epis = s.xpath('./a/@href')
        episode_dic = dict(zip(name_epis, key_epis))
        episode_dic_list.append(episode_dic)

    return url_m3u8, episode_dic_list


def get_ts(url_m3u8):
    """
    m3u8可能1个或2个；ts索引可能6位或3位，或任意位

    return: url_ts的模板 和 ts总数  用于构造ts生成器
    """

    m3u8 = comunits.send_requests(url_m3u8, origin=url_origin, need="response")
    m3u8 = m3u8.text
    print("第一个m3u8文件内容节选：", m3u8[:350], m3u8[-150:], sep='\n')
    if ".m3u8" in m3u8:  # 说明有两个m3u8
        part = findall("\n(.+)m3u8", m3u8)
        m3u8b = part[0] + "m3u8"
        url_m3u8b = urljoin(url_m3u8, m3u8b)
        ts = comunits.send_requests(url_m3u8b, origin=url_origin, need="response")
        ts = ts.text
        url_tspat = url_m3u8b
    elif ".ts" in m3u8:
        ts = m3u8
        url_tspat = url_m3u8
    else:
        return "", 0, 0
        # ts = ""                       # 放报错
        # url_tspat = ""
        # print("m3u8文件出现新特征，请修改代码")

    # 找头尾的两个ts
    ts_start = search("(.*).ts", ts, X).group(1)  # X 忽略空格和#后的东西
    ts_end = search("(.*).ts\n#EXT-X-ENDLIST", ts).group(1)

    # 找出ts是几位数的索引
    diff = 0
    length = len(ts_start)
    for i in range(length - 1):
        if ts_start[i] != ts_end[i]:
            diff = i
            break
    index_long = length - diff

    # 制作ts模板
    ts_pat = ts_end[:diff] + "{0}.ts"
    ts_pat = urljoin(url_tspat, ts_pat)
    # ts总数
    ts_total = ts_end[diff:]
    ts_total = int(ts_total)

    return ts_pat, ts_total, index_long


def download_ts(url_ts, path_ts, d):
    """ 下载ts"""
    # sleep(0.5)
    ts_stream = comunits.send_requests(url_ts, origin=url_origin, need="response")
    with open(path_ts, "wb") as f:
        f.write(ts_stream.content)
        f.close()
    d[0] += 1
    comunits.show_bar(d[0], d[1])


def get_download_console(ts_download, ts_pat, index_long, path_ts_dir):

    # 进程数
    pool = Pool(30)
    # 进程数据共享
    m = Manager()
    d = m.list()
    d.extend([0, len(ts_download)])
    try:
        # ts生成器
        for i in ts_download:  # ts_download列表 元素是 int
            # n为需要添加0的个数
            i = str(i)
            n = index_long - len(i)
            index = "0" * n + i
            url_ts = ts_pat.format(index)
            # ts文件路径
            path_ts = join(path_ts_dir, url_ts.rsplit('/', 1)[1])
            # 开启异步任务
            pool.apply_async(download_ts, (url_ts, path_ts, d))
    finally:
        pool.close()
        pool.join()


def merge_ts(path_ts_dir, path_episode, ts_total, name_episode):
    # 判断ts文件是否下全了
    if len(listdir(path_ts_dir)) == ts_total:
        print("{1}开始合并：{0}{1}".format(name_episode, "*" * 25))
        # 合并ts
        merge = r'copy /b "{0}\*.ts" "{1}"'.format(path_ts_dir, path_episode)
        system(merge)
        if exists(path_episode):
            # 删除ts
            delete = r'rd /S/Q "{0}"'.format(path_ts_dir)
            system(delete)
            sleep(0.5)  # 删除文件夹有一定时间
            if not exists(path_ts_dir):
                print("{1}合并成功：{0}{1}".format(name_episode, "*" * 25))
            else:
                print("删除失败")
        else:
            print("合并失败")
    else:
        print("ts文件未下载完全")


def get_ready():
    info_out = r"""                                Welcome my friend!
    
    爬取网站： 91美剧网   https://91mjw.com/
    网站简介： 好多好多的美剧。。
    使用指导： 进入91美剧网首页，点开你喜欢的美剧，会进入一个介绍该美剧的详情页面，将此页面的网址复制，
              在程序提醒你输入美剧网址的时候,输入此网址，然后，就会开始下载啦！
            
    选择集数： 默认是全部下载哦, 当程序提示时，直接回车就好啦
              当然你还可以指定下载哪几集, 比如我想下载第1集,第9集和第3集到第7集，输入格式为：1 9 3-7
    
    本地
    存储地址： 默认的存储地址为：{0}
              当提示输入存储地址时，直接回车则是选择默认地址；如果要自定义存储地址，自己输入就好啦 
                ！注意 要正确输入地址哦，输错了，我也无力更改呢*——* 
                ！不要担心 文件夹还没有创建，只要地址格式正确，我会帮你建的^^
                """
    print(info_out.format(path_default))

    url_start = input("请输入美剧网址（看上文使用指导，有提示哦）：")
    sets_download = input("亲，要下载哪几集呢：")
    path_store_user = input("下载的视频，亲要存储在哪嘞：")

    # 处理下载集数
    if sets_download is '':
        download_sets_list = []
    else:
        download_sets_list = comunits.deal_input_num(sets_download)
    # 加 0 "第" "集"
    # download_sets_list = ["第"+"0"+i+"集" if len(i) == 1 else "第"+i+"集" for i in download_sets_list]
    download_sets_list = [int(i) for i in download_sets_list]
    # 判断存储地址
    global path_download
    path_download = comunits.choice_path(path_store_user, path_default)
    # url
    global url_info
    url_info = url_start

    return download_sets_list


def main():
    # 交互界面,输出/输入必要信息
    download_sets_list = get_ready()
    # 从美剧详情页获取介绍和每集的url线索
    name_section, episode_dic_main, info_section, introduce = get_info()
    # 写美剧的介绍到txt文件
    path_info = join(path_download, name_section, "美剧详情.txt")
    # 美剧详情写入本地txt文件
    with open(path_info, "w") as f:
        f.write("{0}\n".format("*"*80))
        for i in info_section:
            f.write(i)
            f.write("\n")
        f.write("\n")
        f.write("{0}剧情简介{0}".format("*"*35))
        f.write("\n"*2)
        introduce = findall("(.{50})", introduce)
        for i in introduce:
            f.write(i)
            f.write("\n")

    if not download_sets_list:
        download_sets_list = [i for i in range(1, len(episode_dic_main) + 1)]

    # 每集循环下载
    for i in download_sets_list:  # i:第几集； 按用户输入的集数来下载
        name_episode = str(i) + "__" + name_section
        path_ts_dir = join(path_download, name_section, name_episode)
        file_episode = name_episode + ".mp4"
        path_episode = join(path_download, name_section, file_episode)
        if not (exists(path_episode) or exists(path_ts_dir)):
            makedirs(path_ts_dir)

        # 从详情页到播放页到第一个m3u8到..到ts
        print("{1}解析影片索引中：{0}{1}".format(name_episode, "*" * 25))
        url_play_key = episode_dic_main[i]
        flag_s = 0                                  # 换源头的标志位
        while 1:
            flag_s += 1
            url_play = urljoin(url_home, url_play_key)  # 播放页有详情页来，
            url_m3u8, episode_dic_list = get_m3u8(url_play)  # 返回第一个m3u8地址 和 每个源下的episode_dic
            ts_pat, ts_total, index_long = get_ts(url_m3u8)
            if ts_pat == "" and flag_s-1 < len(episode_dic_list):
                print("第{0}次换源".format(flag_s))
                url_play_key = episode_dic_list[flag_s-1][i]             # 备用源
                continue
            else:
                break
        if ts_pat == "":
            print("没有资源: 第{0}集--{1}".format(i, name_section))
            continue

        # 本地自检 ts_local列表 （int, 与ts_total比对）
        ts_local, ts_dis = comunits.check_local(path_ts_dir, mode="m3u8", path_episode=path_episode
                                                , index_long=index_long)
        if ts_local is False:  # 影片已经合成好，ts_local为FALSE
            print("{0}已经下载,可直接观看".format(name_episode))
            continue

        # 本地ts文件总数 = 服务器ts总数, 算下载完了
        # 本地ts文件总数 < 服务器ts总数,构造一个新的未下的ts列表，注意中间有不连续的也被查出
        ts_local_num = len(ts_local)
        while ts_local_num < ts_total:  # 本地ts不够时
            print("\r{1}开始下载ts流：{0}{1}".format(name_episode, "*" * 25))
            ts_download = [i for i in range(ts_local_num, ts_total)]
            for t in range(ts_local_num, ts_total):
                if t in ts_local:
                    ts_download.remove(t)  # 去除连续ts部分 重复下的部分
            ts_download = ts_download + ts_dis  # 需要下载的ts总列表
            print("ts总数:{0}; 需要下载数:{1}".format(ts_total, len(ts_download)))
            get_download_console(ts_download, ts_pat, index_long, path_ts_dir)
            # 再次本地自检
            print("再次本地自检")
            ts_local, ts_dis = comunits.check_local(path_ts_dir, mode="m3u8", path_episode=path_episode
                                                    , index_long=index_long)
            ts_local_num = len(ts_local)
        print("{1}ts流已经下载完成：{0}{1}".format(name_episode, "*" * 25))

        # 开始合并ts文件
        merge_ts(path_ts_dir, path_episode, ts_total, name_episode)
        input("回车以退出")


if __name__ == '__main__':

    freeze_support()      # 不然多进程打包出错
    main()
