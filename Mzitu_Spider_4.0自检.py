import requests
from bs4 import BeautifulSoup
from time import sleep
import os
import random
from collections import Counter
import lxml

# new_proxy = {'https': '121.237.149.209:3000'}  # 'https':'116.196.85.166:3128'
# proxy_list = []  # 返回高匿代理IP

#def change_ip():
    # if(flag_ip == 1):
    #     url = "https://www.xicidaili.com/wn/"
    #     referer = "https://www.xicidaili.com"
    #     soup = send_requests(url,referer)
    #     items = soup.select("table  tr")
    #     ip = []
    #     port = []
    #     state = []
    #     for item in items[1:]:
    #         tds = item.select("td")
    #         ip.append(tds[1].text)
    #         port.append(tds[2].text)
    #         state.append(tds[4].text)
    #     for i in range(len(ip)):
    #         if (state[i] == "高匿"):
    #             proxy = ip[i] + ":" + port[i]
    #             proxy_list.append(proxy)
    #
    # new_proxy["https"] = proxy_list[flag_ip]



# 本地图片自检
def check_local(path, isend=False):
    file_list = os.listdir(path)
    name = []  # 本地图集列表
    for file in file_list:
        try:
            fn = file.split('_')
        except:
            continue
        if fn[-1] == ".jpg":
            name.append(fn[0])
        else:
            continue
    if isend is False:
        name_pics_local = dict(Counter(name))
        return name_pics_local
    elif isend is True:
        return [len(set(name)), len(name)]


# 发送请求，返回对象： response or soup
def send_requests(url, referer, choice=True):  # 设置默认参数

    # global response
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0',

        'Referer': referer
    }

    ip_list = [ '175.155.24.28:19969', '116.196.85.166:3128',] #'116.196.85.166:3128', '116.196.85.150:3128',

    new_proxy = {'https':random.choice(ip_list)}
    # r = requests.get(url, proxies=new_proxy, headers=headers,timeout =13) #,timeout =(10,27)
    # #response.close()
    print(new_proxy)
    try:
        # s = requests.sessions
        response = requests.get(url, proxies=new_proxy, headers=headers,timeout=13)
        response.close()
        while(response.status_code !=200):
            print("再次尝试连接")
            response = requests.get(url, proxies=new_proxy, headers=headers)
            response.close()
        print(response.status_code)
        print("try末尾", type(response))

    except:
        print("{0}正在更换代理中{0}".format('*—_—*' * 3))
        sleep(0.7)
        send_requests(url, referer, choice)

    else:                                        # 只有try正常才会执行
        if choice is True:
            print("try后面",type(response))
            soup = BeautifulSoup(response.text,'html.parser')
            # if soup is None:
            #     send_requests(url, referer, choice)
            # else:
            print("这里是总部",type(soup))
            return soup

        elif choice is False:
            return response
        else:
            print("没有返回值")


# 下载进度条
def show_pbars(num, nums_img):
    max_tep = 50  # 进度条的长度
    a = int(num / nums_img * max_tep // 1)
    b = '[' + '>' * a + ' ' * (max_tep - a) + ']'
    c = str(int(100 / max_tep * a))
    print('\r{0}{1}%'.format(b, c), end='')


class MzituSpider(object):
    """  page:页面   pics:图集   img:图片 """

    url_home = 'https://www.mzitu.com'
    url_page = url_home

    # 类初始化
    def __init__(self, page_start, page_end, path_download, name_pics_local):
        # 将上面的参数保存为该类的成员属性
        self.page_start = int(page_start)
        self.page_end = int(page_end)
        self.path_download = path_download
        self.name_pics_local = name_pics_local

        self.down_pics_page = 0  # 一页新下载图集数目 判断页间休息
        self.down_pics_total = 0  # 新下载图集的总数
        self.down_img_total = 0  # 新下载图片的总数

    # 控制图片循环
    def start_download(self, url_pics, nums_img, nums_down, name_pics):
        """ 由显示图片的url导航，循环获取图片下载地址并下载"""

        for num in range(nums_down + 1, nums_img + 1):
            # 进度条
            show_pbars(num, nums_img)

            # 设置 访问图片显示页的 URL和 referer
            if num == 1:
                url_img_show = url_pics
                url_img_show_referer = self.url_page
            else:
                url_img_show = url_pics + '/' + str(num)
                url_img_show_referer = url_pics + '/' + str(num - 1)

            # 获取图片下载地址
            url_img_soup = send_requests(url_img_show, url_img_show_referer)
            print("准备下载图片",type(url_img_soup))
            url_img = url_img_soup.select('.main-image>p>a>img')


            if not url_img:  # 因为 下了一会 url_img==[]了 不知为何
                break
            url_img = url_img[0].attrs['src']

            img = send_requests(url_img, url_img_show,choice=False)  # 图片显示页为下载图片的referer
            print("我在下载图片",type(img))
            path_img = self.path_download + '\\' + name_pics + '_' + str(num) + '_.jpg'
            with open(path_img, 'wb') as f:
                f.write(img.content)
                f.close
            self.down_img_total += 1
            img.close()
            # rtime = random.choice([0.1,0.2,0.15])
            # sleep(rtime)

        if num < nums_img:
            nums_down = num - 1
            self.start_download(url_pics, nums_img, nums_down, name_pics)

        print('\n', end='')

    # 查询该图集的本地下载情况
    def is_download(self, name_pics, nums_img):

        nums_down = self.name_pics_local.get(name_pics, 0)  # 若本地没有该图集，返回默认值 0
        if nums_down == nums_img:
            print('已经下载：{}'.format(name_pics))

        elif nums_down == 0:
            print('正在下载：{}'.format(name_pics))
            self.down_pics_page += 1  # 用于判断页间是否休息 （上一页有下载则休息）
        else:
            print('继续下载：{}'.format(name_pics))
            self.down_pics_page += 1

        return nums_down

    # 控制图集循环
    def round_pics(self, dic_pics):
        name_list_pics = list(dic_pics)
        for name_pics in name_list_pics:
            url_pics = dic_pics.get(name_pics)  # 字典以键取值，未加默认值

            # 防止文件夹名字 尾有非法字符 ？
            name_pics = name_pics.replace('？', '')
            name_pics = name_pics.replace('?', '')

            # 查询图集的 图片数目
            print("图片数目处测试返回值",type(send_requests(url_pics, self.url_page)))
            nums_img_soup = send_requests(url_pics, self.url_page)  # referer == url_page 符合浏览行为
            print("我要图片数目",type(nums_img_soup))
            print(type())
            # print(nums_img_soup)
            nums_img = nums_img_soup.select('.pagenavi > a')[-2].text


            nums_img = int(nums_img)

            nums_down = self.is_download(name_pics, nums_img)

            # 只有图集未创建 和 图集未下完 才启动 下载图片的循环
            if nums_down != nums_img:
                self.start_download(url_pics, nums_img, nums_down, name_pics)
                # rtime = random.choice([1.5, 2, 2.5])
                # sleep(rtime)                         # 一个图集下完后休息

    # 获取页面下所有图集的 [入口,名字]
    def get_dic_pics(self, referer_page):
        print("图集入口处测试返回值",type(send_requests(self.url_page, referer_page)))
        pics_soup = send_requests(self.url_page, referer_page)
        print("我要图集入口",type(pics_soup))
        # print(pics_soup)
        items = pics_soup.select('.postlist  li')
        dic_pics = {}
        for item in items:
            href = item.select('a')[1]['href']
            name = item.select('a')[1].text
            dic_pics[name] = href
        return dic_pics

    # 控制页面循环
    def run(self):
        for page in range(self.page_start, self.page_end + 1):
            # 进入下一页的请求头中的referer是上一页
            if page == 1:
                url_page = self.url_home
                referer_page = url_page
            elif page == 2:
                url_page = self.url_home + '/' + 'page' + '/' + '2' + '/'
                referer_page = self.url_home
            else:
                url_page = self.url_home + '/' + 'page' + '/' + str(page) + '/'
                referer_page = self.url_home + '/' + str(page - 1) + '/'
            self.url_page = url_page

            # 返回 -某页所有图集的字典—— 名字：链接
            dic_pics = self.get_dic_pics(referer_page)

            print('{1}准备下载:第{0}页{1}'.format(str(page), '*' * 20))
            # 开始图集循环
            self.round_pics(dic_pics)  # 进入图集的referer == url_page 符合浏览行为
            print('{1}下载完成:第{0}页{1}'.format(str(page), '*' * 20))
            print('\n')

            # 统计新下载图集总数
            self.down_pics_total += self.down_pics_page
            # 最后一页 和 上一页没下载 不休息
            if (page != self.page_end) and (self.down_pics_page > 3):
                print('{0}休息一下再下载{0}'.format('=' * 20))
                print('\n')
                # 一个页面下完后休息
                # rtime = random.choice([3,4,5,6])
                # sleep(rtime)

            self.down_pics_page = 0  # 下一页前清 该统计变量


def main():
    print('\n' * 2)
    print("{0}所以你准备好纸巾了么{0}".format('__*_*__' * 5))
    print('\n' * 2)
    path_download = 'E:\\Mzitu\\imgs'
    # #自定义下载路径
    # print('{0}默认图片下载路径：{1},选择默认请回车{0}'.format('*'*25,path_download))
    # print('\n')
    # path_download_self = input('自定义请输入存储路径：')
    # if(path_download_self == ''):
    #     path_download = path_download
    # else:
    #     path_download = path_download_self
    # if not(os.path.exists(path_download)):
    #     os.mkdir(path_download)
    # #选择下载页面
    page_start = input('请输入起始页码：')
    page_end = input('请输入结束页码：')
    # page_start = 7
    # page_end = 7

    # 启动自检
    name_pics_local = check_local(path_download)
    # 创建对象，启动爬取程序
    spider = MzituSpider(page_start, page_end, path_download, name_pics_local)

    spider.run()
    # finally:
    #      #统计信息
    #     print('\n')
    #     print("下载图集：{0}个；下载图片：{1}张".format(spider.down_pics_total, spider.down_img_total))
    #     pics_total, img_total = check_local(path_download, True)
    #     print("共有图集：{0}个；共有图片：{1}张".format(pics_total, img_total))
    #
    #     end = input('这是用来停住命令行的！')


if __name__ == '__main__':
    main()
