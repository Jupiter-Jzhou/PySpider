import comunits
import m3u8units
from re import X, S, findall, search
from urllib.parse import urljoin, unquote
from multiprocessing import freeze_support
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


def get_ready():
    """
    交互界面,输出/输入必要信息
    """
    info_out = r"""                                Welcome my friend!

    爬取网站： 91美剧网   https://91mjw.com
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

    url = input("请输入美剧网址（看上文使用指导，有提示哦）：")
    sets = input("亲，要下载哪几集呢：")
    path = input("下载的视频，亲要存储在哪嘞：")

    # 处理下载集数, int的列表
    download_sets_list = comunits.deal_input_num(sets)
    # 判断存储地址
    global path_download
    path_download = comunits.choice_download_path(path, path_default)
    # url
    global url_info
    url_info = url

    return download_sets_list


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
    intro = tree.xpath('//p[@class="jianjie"]//text()')
    introduce = ""
    for i in intro:
        introduce = introduce + i
    # print(introduce)

    return name_section, episode_dic_main, info_section, introduce


def define_path(i, name_section):
    """定义合成后影片名，相关路径
    :return name_episode: 合成后的影片名
    :return path_ts_dir: 存放ts的文件夹的路径
    :return path_episode: 合成后影片的存储路径
    :return path_info: 美剧的介绍信息存放路径
    """
    name_episode = str(i) + "__" + name_section
    path_ts_dir = join(path_download, name_section, name_episode)
    path_episode = join(path_download, name_section, "{0}.mp4".format(name_episode))
    path_info = join(path_download, name_section, "美剧详情.txt")
    if not (exists(path_episode) or exists(path_ts_dir)):
        makedirs(path_ts_dir)
    return name_episode, path_ts_dir, path_episode, path_info


def write_info(path_info, info_section, introduce):
    # 美剧详情写入本地txt文件
    with open(path_info, "w+") as f:
        f.write("{0}\n".format("*" * 80))
        for i in info_section:
            f.write(i)
            f.write("\n")
        f.write("\n")
        f.write("{0}剧情简介{0}".format("*" * 35))
        f.write("\n" * 2)
        f.write(introduce)


def get_source(url_play):
    # 找到备用源和独家源的每集播放页的url
    obj = comunits.send_requests(url_play, referer=url_info, need="xpath")
    play_container = obj.xpath('//div[@id="playcontainer"]//section')
    episode_dic_list = []  # 其元素是每个源下的集数的字典{name:key}
    for s in play_container[1:]:
        name_epis = s.xpath('./a/text()')
        name_epis = [int(findall("第(.*)集", i)[0]) for i in name_epis]
        key_epis = s.xpath('./a/@href')
        url_epis = [urljoin(url_play, i) for i in key_epis]
        episode_dic = dict(zip(name_epis, url_epis))
        episode_dic_list.append(episode_dic)

    return episode_dic_list


def get_url_m3u8(i, url_play):
    """从播放页面找出第一个M3U8的url: url_m3u8
    几个播放源几个，几个m3u8
    """

    episode_dic_list = get_source(url_play)
    for episode_dic in episode_dic_list:
        url_play_epis = episode_dic.get(i)
        # 提取vid
        obj = comunits.send_requests(url_play_epis, referer=url_info, need="xpath")
        script = obj.xpath('//section[@class="container"]/script[@type="text/javascript"]/text()')[0]
        vid = findall("vid.*?=(.*);", script)
        vid = vid[0].strip()
        vid = eval(vid).strip()
        # url解码
        url_m3u8 = unquote(vid)
        # 测试有效性
        r = comunits.send_requests(url_m3u8, origin=url_origin, need="response")
        if r.status_code == 200:
            return url_m3u8
    # 如果所有链接都无效
    return ""


def main():

    download_sets_list = get_ready()
    name_section, episode_dic_main, info_section, introduce = get_info()
    if not download_sets_list:              # 列表不为空
        download_sets_list = [i for i in range(1, len(episode_dic_main) + 1)]

    # 每集循环下载
    for i in download_sets_list:                                   # i:第几集； 按用户输入的集数来下载
        name_episode, path_ts_dir, path_episode, path_info = define_path(i, name_section)
        write_info(path_info, info_section, introduce)              # 写美剧的介绍到txt文件

        print("{1}解析影片索引中：{0}{1}".format(name_episode, "*" * 25))
        url_play = urljoin(url_home, episode_dic_main[i])  # 播放页有详情页来
        # print(url_play)
        url_m3u8 = get_url_m3u8(i, url_play)                       # 返回第一个m3u8地址 和 每个源下的episode_dic
        # print(url_m3u8)
        if url_m3u8 == "":
            print("第{0}集：m3u8所有链接无效".format(i))
            continue

        m3u8obj = m3u8units.M3u8(origin=url_origin)
        ts_pat, ts_total = m3u8obj.get_ts(url_m3u8, mode="91MJW")
        if ts_pat == "" and ts_total == 0 :
            print("第{0}集：m3u8文件出现新特征，请修改代码".format(i))
            continue

        ts_local, ts_dis = comunits.check_local(path_ts_dir, mode="m3u8", path_file_merged=path_episode)
        if ts_local is False:                                               # 影片已经合成好，ts_local为FALSE
            print("{0}已经下载,可直接观看".format(name_episode))
            continue

        print("\r{1}开始下载ts流：{0}{1}".format(name_episode, "*" * 25))
        ts_local_num = len(ts_local)
        while ts_local_num < ts_total:  # 本地ts不够时
            ts_download = [i for i in range(ts_local_num, ts_total)]
            for t in range(ts_local_num, ts_total):
                if t in ts_local:
                    ts_download.remove(t)  # 去除连续ts部分 重复下的部分
            download_list = ts_download + ts_dis  # 需要下载的ts总列表
            print("ts总数:{0}; 需要下载数:{1}".format(ts_total, len(download_list)))
            # 启动多进程下载
            process = comunits.Multiprocess(origin=url_origin, referer=url_play)
            length = len(str(ts_total))           # ts文件存储名要补齐0
            process.process_console(path_ts_dir, download_list, length, url_pat=ts_pat, pat_mode="zero")
            # 再次本地自检, 控制是否退出循环
            print("再次本地自检")
            ts_local, ts_dis = comunits.check_local(path_ts_dir, mode="m3u8", path_file_merged=path_episode)
            ts_local_num = len(ts_local)
        print("{1}ts流已经下载完成：{0}{1}".format(name_episode, "*" * 25))

        # 开始合并ts文件
        comunits.merge_files(path_ts_dir, path_episode, ts_total)


if __name__ == '__main__':
    freeze_support()  # 不然多进程打包出错
    main()
    system("pause")
