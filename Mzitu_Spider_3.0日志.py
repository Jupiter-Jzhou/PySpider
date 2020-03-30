import requests
from bs4 import BeautifulSoup
from time import sleep
import os
import random

def get_headers(referer):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0',

        'Referer': referer
    }
    return headers

def get_soup(url, headers):
    proxy = {'https':'116.196.85.166:3128'}
    response = requests.get(url, proxies=proxy, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    response.close()
    return soup

# class DisAntiSpider(object):
#     url_useragent = 'http://www.useragentstring.com/pages/useragentstring.php?name=All'
#     url_IPs = 'https://www.xicidaili.com/wn/'
#
#     def __init__(self,num):
#         self.num = num
#
#     def get_useragents(self):
#         referer = 'http://www.useragentstring.com/'
#         headers = get_headers(referer)
#         soup = get_soup(self.url_useragent,headers)
#         print(soup)
#         liste =soup.select(".liste>ul")
#         # liste = liste.select("")
#         print(liste)


# page:页面   pics:图集   img: 图片
class MzituSpider(object):
    url_home='https://www.mzitu.com'

    #类初始化
    def __init__(self, page_start, page_end,path_download,store_mode):
        #将上面的参数保存为该类的成员属性
        self.page_start = int(page_start)
        self.page_end = int(page_end)
        self.path_download = path_download
        self.store_mode = store_mode

        self.dir_done = 0      #已下载的图集数目
        self.dir_goon_page = 0
        self.dir_new_page = 0       #一页新下载图集数目
        self.dir_goon_pages = 0
        self.dir_new_pages = 0
        self.img_add = 0      #未下完图集新下载的图片数目
        self.img_download = 0  #新下载图片的总数
        self.img_exist = 0      #已下载图片的总数
        self.ctrl_num = 0      #用于进度条

        self.text_log = {}
        self.name_list_log = []
        self.num_list_log = []
        self.num_log = 0
        self.page_log = 0
        self.path_log = self.path_download + "\\" + "log.txt"


    #下载进度条
    def show_pbars(self,num,nums):
        max_tep = 50  # 进度条的长度
        a = int(num / nums * max_tep // 1)
        b='[' + '>'*a + ' '*(max_tep - a) + ']'
        c=str(int(100/(max_tep)*a))
        print('\r{0}{1}%'.format(b,c),end='')

     #由显示图片的url：导航，循环获取图片下载地址并下载
    def start_download(self,url_pics,nums,nums_down,path_pics):
        #图集中图片循环
        for num in range(nums_down+1,nums+1):
            # 进度条
            self.show_pbars(num, nums)

            # referer 是下载图片时和转到下一页图片时候的请求头中referer
            if (num==1):
                referer=url_pics
                url_before=self.url_home
            else:
                referer=url_pics + '/' + str(num)
                url_before = url_pics + '/' + str(num - 1)

            headers_navi = get_headers(url_before)
            soup = get_soup(referer,headers_navi)
        # 图片下载地址直接从显示页获取；不拼接，因为该url递进不好处理，也因此对网站的访问多了一倍（访问显示页
            url_imgs = soup.select('.main-image>p>a>img')

           #因为 下了一会 url_imgs==[]了 不知为何
            if(url_imgs==[]):
                break
            url_imgs = url_imgs[0].attrs['src']
            name_img = url_imgs.split('/')
            name_img = name_img[-1]

            headers_img = get_headers(referer)
            img = requests.get(url_imgs, headers=headers_img)
            path_img = path_pics + '/' + name_img
            with open(path_img, 'wb') as f:
                f.write(img.content)
                f.close
            self.img_download += 1
            img.close()
            rtime = random.choice([0.1,0.2,0.15])
            sleep(rtime)

        if(num<nums):
            nums_down = num -1
            self.start_download(url_pics,nums,nums_down,path_pics)

        print('\n', end='')


    def start_download_log(self,url_pics,nums,nums_down,name_pics):
        # 图集中图片循环
        for num in range(nums_down + 1, nums + 1):
            # 进度条
            self.show_pbars(num, nums)

            # referer 是下载图片时和转到下一页图片时候的请求头中referer
            if (num == 1):
                referer = url_pics
                url_before = self.url_home
            else:
                referer = url_pics + '/' + str(num)
                url_before = url_pics + '/' + str(num - 1)

            headers_navi = get_headers(url_before)
            try:
                soup = get_soup(referer, headers_navi)
            except:
                self.num_list_log.append(num-1)
                self.write_log(self.page_log)
                print(name_pics+" de"+"第{}张图片下载失败".format(str(num)))
            # 图片下载地址直接从显示页获取；不拼接，因为该url递进不好处理，也因此对网站的访问多了一倍（访问显示页
            url_imgs = soup.select('.main-image>p>a>img')
            # 因为 下了一会 url_imgs==[]了 不知为何
            if (url_imgs == []):
                break
            url_imgs = url_imgs[0].attrs['src']
            headers_img = get_headers(referer)
            try:
                img = requests.get(url_imgs, headers=headers_img)
            except:
                self.num_list_log.append(num-1)
                self.write_log(self.page_log)
                print(name_pics+" de"+"第{}张图片下载失败".format(str(num)))

            path_img = self.path_download + '\\' + name_pics + '_' + str(num) + '_.jpg'
            with open(path_img, 'wb') as f:
                f.write(img.content)
                f.close
            img.close()
            self.img_download = num
            self.num_log = num
            rtime = random.choice([0.1, 0.2, 0.15])
            sleep(rtime)

        if (num < nums):
            nums_down = num - 1
            self.start_download_log(url_pics, nums, nums_down, name_pics)

        print('\n', end='')


    # 查询图集中的 图片数目
    def get_nums_img(self,url_pics):
        headers_home = get_headers(self.url_home)
        soup = get_soup(url_pics,headers_home)

        nums = soup.select('.pagenavi > a')[-2].text
        return int(nums)

    # 查询本地下载情况
    def is_download(self,name_pics,nums):
        path_pics = self.path_download + '\\' + name_pics
        if(os.path.exists(path_pics)):
            if(len(os.listdir(path_pics))==nums):
                print('已经下载：{}'.format(name_pics))
                flag = 1                              #判断是否睡眠  及 是否调用 下载图片的循环
                nums_down=nums
                self.dir_done += 1
                self.img_exist += nums
            else:
                nums_down = len(os.listdir(path_pics))
                print('继续下载：{}'.format(name_pics))
                flag = 0
                self.dir_goon_page += 1
                self.img_add = nums - nums_down
                self.img_exist += nums_down
        else:
            os.mkdir(path_pics)
            print('正在下载：{}'.format(name_pics))
            nums_down=0
            flag = 0
            self.dir_new_page += 1

        return [path_pics,nums_down,flag]


    def is_download_log(self,name_pics,nums):

        try:
            with open(self.path_log,"r+") as f:    # + 不存在能抛出异常
                text_log = f.read()            #字符串类型
                f.close()
            text_log = eval(text_log)           #去一层引号
            text_log = text_log.get(self.page_log)   #因为是两层字典，页s和一页中的图集s
        except:
            text_log = {}
        self.text_log = text_log
        if name_pics in text_log:                      #判断键（图集名）是否存在
            nums_down = text_log.get(name_pics,0)    # 0 是当键不存在时，输出的内容,这里可不需要
            if(nums_down == nums):
                print('已经下载：{}'.format(name_pics))
                flag = 1      # 判断是否睡眠  及 是否调用 下载图片的循环
                nums_down = nums
                self.dir_done += 1
                self.img_exist += nums
            else:
                print('继续下载：{}'.format(name_pics))
                flag = 0
                self.dir_goon_page += 1
                self.img_add = nums - nums_down
                self.img_exist += nums_down
        else:
            print('正在下载：{}'.format(name_pics))
            nums_down = 0
            flag = 0
            self.dir_new_page += 1
        del text_log                             #释放变量

        return [nums_down, flag]

    #控制图集循环
    def get_pics(self,list_pics):
        for pics in list_pics:
            url_pics = self.url_home +'/' + str(pics[0])
            name_pics= pics[1]
            # 防止文件夹名字 尾有非法字符 ？
            name_pics = name_pics.replace('？','')
            name_pics = name_pics.replace('?','')

            # 查询图集的 图片数目 和 存储图片的url
            nums =self.get_nums_img(url_pics)

            if(self.store_mode is True):
                info=self.is_download(name_pics,nums)
                # 只有图集未创建 和 图集未下完 才启动 下载图片的循环
                if (info[-1] == 0):
                    self.start_download(url_pics, nums, info[1], info[0])
                    rtime = random.choice([1.5, 2, 2.5])
                    sleep(rtime)  # 一个图集下完后休息两秒
            else:
                self.name_list_log.append(name_pics)
                info = self.is_download_log(name_pics,nums)
                if (info[-1] == 0):
                    self.start_download_log(url_pics, nums, info[0],name_pics)
                    self.num_list_log.append(self.num_log)
                    rtime = random.choice([1.5, 2, 2.5])
                    sleep(rtime)  # 一个图集下完后休息两秒



    #获取图集的 [入口,名字]
    def get_pics_list(self,url_page,referer_page):
        headers_page=get_headers(referer_page)
        soup = get_soup(url_page,headers_page)

        items=soup.select('.postlist li')
        list_pics=[]
        for item in items :
            href=item.select('a')[1]['href']
            href=href.split('/')[-1]
            name=item.select('a')[1].text
            list_pics.append([href,name])
        return list_pics

    #控制页面循环
    def run(self):
        for page in range(self.page_start,self.page_end + 1):

            self.name_list_log = []
            self.page_log = page
            #进入下一页的请求头中的referer是上一页
            if(page==1):
                url_page=self.url_home
                referer_page =url_page
            elif(page == 2):
                url_page=self.url_home + '/' + 'page' + '/' + '2' + '/'
                referer_page = self.url_home
            else:
                url_page=self.url_home + '/' + 'page' + '/' + str(page) + '/'
                referer_page = self.url_home + '/' + str(page - 1) + '/'

            # 返回 -某一页页各图集的链接和名字- 字典的列表
            list_pics = self.get_pics_list(url_page,referer_page)

            print('{1}准备下载:第{0}页{1}'.format(str(page),'*'*20))
            self.get_pics(list_pics)
            print('{1}下载完成:第{0}页{1}'.format(str(page),'*'*20))
            print('\n')
            self.dir_new_pages += self.dir_new_page
            self.dir_goon_pages += self.dir_goon_page
            if((page != self.page_end) and ((self.dir_new_page + self.dir_goon_page) > 1 )):
                print('{0}休息一下再下载{0}'.format('=' * 20))
                print('\n')
                rtime = random.choice([3,4,5,6])
                sleep(rtime)  #一个页面下完后休息5秒

            self.dir_new_page = 0
            self.dir_goon_page = 0
            self.write_log(page)

    #统计信息
    def output_info_download(self):
        pics_ing = self.dir_new_pages + self.dir_goon_pages
        pics_down = self.dir_done
        pics_all = pics_down + pics_ing
        img_ing = self.img_download
        img_down = self.img_exist
        img_all = img_ing + img_down
        print("共{2}个图集：新下载图集：{0}个；已下载图集：{1}个；".format(pics_ing,pics_down,pics_all))
        print("共{2}张图片：新下载图片：{0}张；已下载图片：{1}张；".format(img_ing,img_down,img_all))

    #写日志
    def write_log(self,page):
        dict_page_log = dict(zip(self.name_list_log,self.num_list_log))   #从两个列表合成字典
        self.text_log.update(dict_page_log)                           # 更新内字典元素

        with open(self.path_log,"r+") as f:
            log = f.read()
            f.close()
            log = eval(log)
            log[page] = self.text_log
        with open(self.path_log, "w+") as f:
            f.write(str(log))
            f.close()
            del log

def main():
    # num = 3
    # disanti = DisAntiSpider(num)
    # disanti.get_useragents()

    print("{0}所以你准备好纸巾了么{0}".format('__*_*__'*5))
    print('\n'*2)
    path_download = 'E:\\Mzitu\\imgs'

    # print('{0}下载的图片默认路径："E:\\Mzitu",选择默认请回车{0}'.format('*'*2))
    # print('\n')
    # path_download_self = input('自定义请输入存储路径：')
    # if(path_download_self == ''):
    #     path_download = path_download
    # else:
    #     path_download = path_download_self
    # if not(os.path.exists(path_download)):
    #     os.mkdir(path_download)

    # store_mode = input("一个图集一个文件夹则请输入：y    ；所有图片一个文件夹则请输入：n   ")
    # if(store_mode == 'y' or 'Y'):
    #     store_mode = True
    # elif(store_mode == 'n' or 'N'):
    #     store_mode = False

    # page_start = input('请输入起始页码：')
    # page_end = input('请输入结束页码：')

    store_mode = False
    page_start = 7
    page_end = 8
    # 创建对象，启动爬取程序
    spider = MzituSpider(page_start,page_end,path_download,store_mode)
    spider.run()

    spider.output_info_download()
    end = input('这是用来停住命令行的！')

if __name__ == '__main__':
    main()