import comunits
import m3u8units
from lxml import etree
from execjs import compile as js_compile
from execjs import eval  as js_eval
import os.path

path_default = r"E:\CodeStore\movie\pb"
path_download = ""

url_home = "https://cn.pornhub.com"
proxy = {'https': 'https://127.0.0.1:25378'}


def get_ready():
    info_out = r"""                                       Welcome my friend!

    使用指导： 进入视频播放页：
              若要批量下载视频，复制该网页的url，当程序提醒输入视频地址时，输入复制的url；
              若要批量下载视频，可将视频地址复制到txt文件（一行一条！），当程序提醒输入视频地址时，输入该txt文件的绝对路径      
                ！绝对路径格式如： E:\\video_url.txt
    本地
    存储地址： 默认的存储地址为：{0}
              当提示输入存储地址时，直接回车则是选择默认地址；如果要自定义存储地址，自己输入就好啦 
                ！注意 要正确输入地址哦，输错了，我也无力更改呢*——* 
                ！不要担心 文件夹还没有创建，只要地址格式正确，我会帮你建的^^
                """
    print(info_out.format(path_default))
    url = input("请输入视频地址：")
    path = input("请输入存储地址：")

    # 判断存储地址
    global path_download
    path_download = comunits.choice_download_path(path, path_default)
    # 获取视频地址
    url_video_list = []
    if "https" in url:
        url_video_list.append(url.strip())
    elif ".txt" in url:
        with open(url, "r") as f:
            s = f.read()
        s.strip().split("\n")
        url_video_list = [i.strip() for i in s]
    else:
        print("输入的视频地址格式不正确：{0}".format(url))

    return url_video_list


def define_path(url_video):
    name_video = url_video.rsplit("viewkey=")[-1]
    path_ts_dir = path_download + '/' + name_video
    path_video = path_download + '/' + "{0}.mp4".format(name_video)
    if not (os.path.exists(path_video) or os.path.exists(path_ts_dir)):
        os.makedirs(path_ts_dir)

    return path_ts_dir, path_video, name_video


def get_url_m3u8(url_video):
    """
    从播放页获得url_m3u8
    """
    args = {

        "referer": url_home,
        "proxy": proxy,
        "need": "xpath"
    }
    obj = comunits.send_requests(url_video, **args)
    script = obj.xpath("//div[@class='original mainPlayerDiv']/script/text()")[0]
    video_id = obj.xpath("//div[@class='original mainPlayerDiv']/@data-video-id")[0]
    # print(script, ID, sep='\n')
    js = "var playerObjList = {};" + script
    js_obj = js_compile(js)
    dic_list = js_obj.eval("flashvars_{0}['mediaDefinitions']".format(video_id))
    dic = dic_list[-1]
    quality = dic["quality"]
    url_m3u8 = dic["videoUrl"]
    # print(quality, url_m3u8, sep="\n")
    # 验证有效性
    r = comunits.send_requests(url_m3u8, referer=url_video, origin=url_home, proxy=proxy, need="response")
    if "#EXTM3U" in r.text:
        return url_m3u8, quality
    else:
        print("播放页代码有改动，找不到m3u8地址")
        return "", ""


def main():
    url_video_list = get_ready()
    for url_video in url_video_list:
        path_ts_dir, path_video, name_video = define_path(url_video)

        url_m3u8, quality = get_url_m3u8(url_video)
        # print(quality, url_m3u8, sep="\n")
        if url_m3u8 == "":
            # print("第{0}集：m3u8所有链接无效".format(i))
            continue

        # 创建对象
        m3u8obj = m3u8units.M3u8(referer=url_video, origin=url_home, proxy=proxy)
        url_ts_pat, ts_total = m3u8obj.get_ts(url_m3u8, mode="pb")
        if url_ts_pat == "" and ts_total == 0:
            # print("第{0}集：m3u8文件出现新特征，请修改代码".format(i))
            continue

        ts_local, ts_dis = comunits.check_local(path_ts_dir, mode="m3u8", path_file_merged=path_video)
        if ts_local is False:  # 影片已经合成好，ts_local为FALSE
            # print("{0}已经下载,可直接观看".format(path_video))
            continue

        print("\r{1}开始下载ts流：{0}{1}".format(name_video, "*" * 25))
        ts_local_num = len(ts_local)
        while ts_local_num < ts_total:  # 本地ts不够时
            ts_download = [i for i in range(ts_local_num+1, ts_total+1)]
            for t in range(ts_local_num+1, ts_total+1):
                if t in ts_local:
                    ts_download.remove(t)  # 去除连续ts部分 重复下的部分
            download_list = ts_download + ts_dis  # 需要下载的ts总列表
            print("ts总数:{0}; 需要下载数:{1}".format(ts_total, len(download_list)))
            # 启动多进程下载
            process = comunits.Multiprocess(origin=url_home, referer=url_video, proxy=proxy)
            length = len(str(ts_total))  # ts文件存储名要补齐0
            process.process_console(path_ts_dir, download_list, length, url_pat=url_ts_pat, pat_mode="naked")
            # 再次本地自检, 控制是否退出循环
            print("再次本地自检")
            ts_local, ts_dis = comunits.check_local(path_ts_dir, mode="m3u8", path_file_merged=path_video)
            ts_local_num = len(ts_local)
        print("{1}ts流已经下载完成：{0}{1}".format(name_video, "*" * 25))

        # 开始合并ts文件
        comunits.merge_files(path_ts_dir, path_video, ts_total)


if __name__ == '__main__':
    main()

