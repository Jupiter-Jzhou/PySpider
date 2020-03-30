import Comunit
import re

url_home = "https://91mjw.com"
# 剧情介绍等影片信息
url_section = "https://91mjw.com/video/895.htm"
# 独家高清播放页，可获取每集的播放地址
url_epi = "https://91mjw.com/vplay/ODk1LTEtMA==.html"
url_store = "https://sp.lujiahb.com"




def get_addr_epis(obj):
    """获取每集地址"""

    div = obj.xpath("//div[@class='mgplaylist']")[0]
    channel_list = div.xpath('.//li/a')

    # 索引 选择主线 备用 独家高清等通道  网站有问题
    # index = 0
    # for c in channel_list:
    #     channel = c.xpath('./text()')[0]
    #     print(channel)
    #     if channel is ("独家高清" or "独家超清"):
    #         index = channel_list.index(channel)
    #         break
    section = div.xpath('./div/section')[0]
    href_list = section.xpath('./a/@href')
    episode_list = section.xpath('./a/text()')

    url_epi_list = []
    for href in href_list:
        url = url_home + href
        url_epi_list.append(url)
    url_epi_dic = dict(zip(episode_list, url_epi_list))

    return url_epi_dic


def get_info(obj):

    script = obj.xpath('//section[@class="container"]/script[@type="text/javascript"]/text()')[0]
    # script = script.xpath('string(.)')   效果同text()
    # script类型 <class 'lxml.etree._ElementUnicodeResult'>

    string = script.replace('var','').split(";\n")

    ## 找出所有信息
    # key = []
    # value = []
    # for s in string[:-1]:
    #     n = s.find("=")
    #     key.append(s[:n].strip())
    #     value.append(s[n+1:].strip())
    # value = [eval(i) for i in value]
    # # print(key)
    # # print(value)
    # info_dic = dict(zip(key, value))
    # # print(info_dic)
    # vid = info_dic["vid"]

    # 仅vid
    for s in string[:-1]:
        if "vid" in s:
            n = s.find("=")
            vid = eval(s[n + 1:].strip())

    # url解码
    vid = vid.replace("%3A",":").replace("%2F","/")
    print(vid)
    return vid


def main():


    obj = Comunit.send_requests(url_epi, url_section, need="xpath")
    # 每集地址
    # url_epi_dic = get_addr_epis(obj)
    # 下一个请求网址
    vid = get_info(obj)
    # 拼接下载地址

    response = Comunit.send_requests(vid, url_store, need="response")
    txt = response.text
    index = txt.find('/')
    txt = txt[index:]
    print(txt)
    v = vid.split("//")
    l = v[0]
    r = v[-1]
    r = r.split('/')[0]
    url_last = l + "//" + r + txt
    print(url_last)
    response1 = Comunit.send_requests(url_last, url_store, need="response")
    txt1 = response1.text()
    print(txt1)


if __name__ == '__main__':
    main()