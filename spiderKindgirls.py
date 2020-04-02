# 自定义模块
import comunits
import os

proxy = {'https': 'https://127.0.0.1:10809'}
url_ck = 'https://www.kindgirls.com/photo-archive'
url_home = 'https://www.kindgirls.com/'
path_default = "E:\\kindgirls"



def get_pics(year, month):
    """
    返回 pics_dic {图集名字:图集url}
    制作每月图集显示页的  url 和 referer
    获取每月图集显示页的  图集的 url 和 名字
    """
    url_month = url_ck + "/" + "?s={0}-{1}".format(month, year)
    href = []
    name = []
    soup = comunits.send_requests(url_month, referer=url_ck, proxy=proxy)
    soup = soup.select(".gal_list a")
    for tag in soup:
        t = tag['href']
        n = t.split('/')[-3]
        a = "https://www.kindgirls.com" + t
        href.append(a)
        name.append(n)
    pics_dic = dict(zip(name, href))
    return pics_dic


def start_download(local_dic, pics_dic, path_month):
    """
    判断是否已下载
    下载 未下或未下完的图集
    """
    pics_list = list(pics_dic)
    for pics in pics_list:
        print("正在下载：{0}".format(pics))
        url_pics = pics_dic[pics]           # 准备下载图片的url
        num_start = local_dic[pics]

        soup = comunits.send_requests(url_pics, referer=url_ck, proxy=proxy)
        soup = soup.select(".gal_list a[target]")
        url_img_list = []
        for img in soup:
            url_img_list.append(img['href'])

        n = num_start - 1           # 准备下载的控制参数
        nn = num_start - 1
        ns = len(url_img_list)
        for url in url_img_list[nn:]:          # 下载
            n += 1
            if n == ns:
                path_img = path_month + "\\" + pics + "_" + str(n) + "_" + "L.jpg"
            else:
                path_img = path_month + "\\" + pics + "_" + str(n) + "_" + ".jpg"
            response = comunits.send_requests(url, referer=url_pics, proxy=proxy, need="response")
            with open(path_img, "wb") as f:
                f.write(response.content)
                f.close()
            comunits.show_bar(n, ns)              # 进度条


def main():
    """
    Kindgirls 网站图片
    """
    print('\n')
    print("{0}welcome to kindgirls{0}".format('*'*45))
    print('\n'*2)
    print("说明：一个月有300张左右图片； 年份输入格式如：2019；月份输入格式如：3-4 5 7-9；\
    选择默认下载路径{0},请直接回车*-*".format(path_default))
    print('\n')
    year = input("亲^_^，想要哪年的：")
    month_list = input("亲^_^，哪几个月呢：")
    path = input("请输入下载路径：")

    if path is '':                        # 下载路径选择
        path = path_default
    if not os.path.exists(path):
        os.mkdir(path)

    month_list = comunits.deal_input_num(month_list)    # 月份格式化处理

    for month in month_list:    # 以月循环
        print("{2} 准备下载:{0}--{1} {2}".format(month, year, "*" * 35))
        if len(month) == 1:
            month = "0" + month
        path_month = path + "\\" + "{0}--{1}".format(month, year)  # 以月为单位 建文件夹
        if not os.path.exists(path_month):
            os.mkdir(path_month)

        name_done_list, name_ing_dic = comunits.check_local(path_month)  # 本地自检
        pics_dic = get_pics(year, month)      # 返回每月图集字典
        local_dic, pics_dic = comunits.is_download(pics_dic, name_done_list, name_ing_dic)
        start_download(local_dic, pics_dic, path_month)

        print("{2} 完成下载:{0}--{1} {2}".format(month, year, "*" * 35))


if __name__ == '__main__':
    main()
