import comunits
import re
from urllib import parse
from multiprocessing import Pool
from lxml import etree
import os


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
    name_section = re.findall("《(.*)》", name_section)[0]
    # print(name_section)

    # 每集url线索,第几集
    id_epis = tree.xpath('//a[@onclick="play(this)"]/@id')
    name_epis = tree.xpath('//a[@onclick="play(this)"]/text()')
    name_epis = [int(re.findall("第(.*)集", i)[0]) for i in name_epis]
    # print(id_epis, name_epis, sep="\n")
    episode_dic = dict(zip(name_epis, id_epis))

    # 影片信息
    div = tree.xpath("//div[@class='video_info']")[0]
    # 将lxml.etree._Element转化成字符串
    div = etree.tostring(div, encoding="utf8")
    div = div.decode("utf8")
    # print(div)

    # 预处理字符串，后正则
    div = div.replace("</strong>", '').replace("<br/>", '')
    info_section = re.findall("<strong>(.*)", div)
    # for i in info_section:
    #     print(i)

    # 剧情简介
    introduce = tree.xpath('//p[@class="jianjie"]/span/text()')[0]
    # print(introduce)

    return name_section, episode_dic, info_section, introduce


def get_m3u8a(url_play):
    """从播放页面找出第一个M3U8的url: vid"""

    # script = script.xpath('string(.)')   效果同text()
    # script类型 <class 'lxml.etree._ElementUnicodeResult'>
    obj = comunits.send_requests(url_play, referer=url_info, need="xpath")
    script = obj.xpath('//section[@class="container"]/script[@type="text/javascript"]/text()')[0]
    # 提取vid
    vid = re.findall("vid.*?=(.*);", script)
    vid = vid[0].strip()
    vid = eval(vid).strip()
    # url解码
    vid = parse.unquote(vid)
    # print(vid)

    return vid


def get_ts(url_m3u8a):
    """
    return: 第一个ts 和 ts总数  用于构造ts生成器
    """

    # 找到第二个m3u8地址 url_m3u8b
    m3u8b = comunits.send_requests(url_m3u8a, origin=url_origin, need="response")
    m3u8b = m3u8b.text
    part = re.findall("\n(.+)m3u8", m3u8b)
    m3u8b = part[0] + "m3u8"
    url_m3u8b = parse.urljoin(url_m3u8a, m3u8b)
    # print(url_m3u8b)
    # 找到ts模板
    ts = comunits.send_requests(url_m3u8b, origin=url_origin, need="response")
    ts = ts.text
    ts_list = re.findall("#EXTINF.*\n(.*)\n", ts)
    # print(ts_list[:3], len(ts_list), sep="\n")
    # 制作ts模板
    ts = ts_list[-1]  # 用第一个[0]会有莫名其妙的错误
    ts_pat = ts.replace(ts[-9:-3], "{}")

    return ts_pat, len(ts_list), url_m3u8b


def download_ts(url_ts, ts, path_ts_dir):
    """ 下载ts"""

    path_ts = os.path.join(path_ts_dir, ts)
    ts_stream = comunits.send_requests(url_ts, origin=url_origin, need="response")
    with open(path_ts, "wb") as f:
        f.write(ts_stream.content)
        f.close()


def create_pool(ts_download, ts_reload, ts_pat, path_ts_dir, url_m3u8b):
    # 动态进程数
    ts_start = ts_download[0]
    ts_end = ts_download[-1]
    n = int((ts_end - ts_start) * 0.04) + 1
    pool = Pool(n)

    try:
        # ts生成器
        for i in range(ts_start, ts_end):
            # n为需要添加0的个数
            i = str(i)
            n = 6 - len(i)
            index = "0" * n + i
            ts = ts_pat.format(index)
            url_ts = parse.urljoin(url_m3u8b, ts)
            # 开启异步任务
            pool.apply_async(download_ts, (url_ts, ts, path_ts_dir))
    finally:
        pool.close()
        pool.join()
    if len(ts_reload) != 0:
        n = int((len(ts_reload)) * 0.04) + 1
        pool = Pool(n)
        try:
            # ts生成器
            print("补下ts")
            for i in ts_reload:
                # n为需要添加0的个数
                i = str(i)
                n = 6 - len(i)
                index = "0" * n + i
                ts = ts_pat.format(index)
                url_ts = parse.urljoin(url_m3u8b, ts)
                # 开启异步任务
                pool.apply_async(download_ts, (url_ts, ts, path_ts_dir))
        finally:
            pool.close()
            pool.join()


def merge_ts(path_ts_dir, path_episode, ts_total, name_episode):

    # 判断ts文件是否下全了
    if len(os.listdir(path_ts_dir)) == ts_total:
        # 合并ts
        merge = r'copy /b "{0}\*.ts" "{1}"'.format(path_ts_dir, path_episode)
        os.system(merge)
        if os.path.exists(path_episode):
            # 删除ts
            delete = r'rd /S/Q "{0}"'.format(path_ts_dir)
            os.system(delete)
            print("\r合并成功：{}".format(name_episode))
        else:
            print("\rts文件合并失败")
    else:
        print("\rts文件未下载完全")


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
    name_section, episode_dic, info_section, introduce = get_info()
    if not download_sets_list:
        # download_sets_list = ["第" + "0" + str(i) + "集" if len(str(i)) == 1 else "第" + str(i) + "集"
        #                       for i in range(1, len(episode_dic)+1)]
        download_sets_list = [i for i in range(1, len(episode_dic) + 1)]
    # 每集循环下载
    for i in download_sets_list:        # i:第几集； 按用户输入的集数来下载
        name_episode = str(i) + "__" + name_section
        path_ts_dir = os.path.join(path_download, name_section, name_episode)
        file_episode = name_episode + ".mp4"
        path_episode = os.path.join(path_download, name_section, file_episode)

        # 本地自检 ts_local列表 （int, 与ts_total比对）
        ts_local, ts_reload = comunits.check_local(path_ts_dir, mode="m3u8", path_episode=path_episode)

        # 影片已经合成好，ts_local为FALSE
        if ts_local is False:
            print("{}已经下载,可直接观看".format(name_episode))
            continue
        else:
            if not os.path.exists(path_ts_dir):
                os.makedirs(path_ts_dir)

        print("{1}正在下载：{0}{1}".format(name_episode, "*" * 25))
        url_play = url_home + "/vplay/" + episode_dic[i] + ".html"
        print(url_play)
        # 返回第一个m3u8地址
        url_m3u8a = get_m3u8a(url_play)
        # 返回ts下载地址的变化部分的模板 和 ts总数
        ts_pat, ts_total, url_m3u8b = get_ts(url_m3u8a)

        # 本地ts文件总数 = 服务器ts总数, 算下载完了
        # 本地ts文件总数 < 服务器ts总数,构造一个新的未下的ts列表，注意中间有不连续的也被查出
        ts_local_num = len(ts_local)
        if ts_local_num < ts_total:
            ts_download = [ts_local_num, ts_total]
            create_pool(ts_download, ts_reload, ts_pat, path_ts_dir, url_m3u8b)

        print("{1}完成下载：{0}{1}".format(name_episode, "*" * 25))
        print("{1}开始合并：{0}{1}".format(name_episode, "*" * 25))
        merge_ts(path_ts_dir, path_episode, ts_total, name_episode)



if __name__ == '__main__':
    main()
