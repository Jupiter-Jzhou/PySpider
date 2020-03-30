import requests
from bs4 import BeautifulSoup
from time import sleep
import os
import random


# url_pic和url_pics是显示图片的url；url_imgs和url_img是存储图片的url
# 带s的是用于拼接的url; 不带s的是每个单张图片的ur
# page:页面   pics:图集   img: 图片
class MzituSpider(object):
    url_home='https://www.mzitu.com'

    #类初始化
    def __init__(self, page_start, page_end,path_download):
        #将上面的参数保存为该类的成员属性
        self.page_start = int(page_start)
        self.page_end = int(page_end)
        self.path_download = path_download
        self.dir_done = 0      #已下载的图集数目
        self.dir_goon_page = 0
        self.dir_new_page = 0       #一页新下载图集数目
        self.dir_goon_pages = 0
        self.dir_new_pages = 0
        self.img_add = 0      #未下完图集新下载的图片数目
        self.img_download = 0  #新下载图片的总数
        self.img_exist = 0      #已下载图片的总数
        self.ctrl_num = 0      #用于进度条

    #下载进度条
    def show_pbars(self,num,nums):
        max_tep = 50  # 进度条的长度
        a = int(num / nums * max_tep // 1)
        b='[' + '>'*a + ' '*(max_tep - a) + ']'
        c=str(int(100/(max_tep)*a))
        print('\r{0}{1}%'.format(b,c),end='')

    def get_headers(self,referer):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0',
            'Connection': 'keep-alive',
            'Referer': referer
        }
        return headers

    def get_soup(self,url, headers):
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        response.close()
        return soup

     #由显示图片的url：导航，循环获取图片下载地址并下载
    def start_download(self,url_pics,nums,path_pics,nums_down):
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

            headers_navi = self.get_headers(url_before)
            soup = self.get_soup(referer,headers_navi)
        # 图片下载地址直接从显示页获取；不拼接，因为该url递进不好处理，也因此对网站的访问多了一倍（访问显示页
            url_imgs = soup.select('.main-image>p>a>img')

           #因为 下了一会 url_imgs==[]了 不知为何
            if(url_imgs==[]):
                break
            url_imgs = url_imgs[0].attrs['src']
            name_img = url_imgs.split('/')
            name_img = name_img[-1]

            headers_img = self.get_headers(referer)
            img = requests.get(url_imgs, headers=headers_img)
            path_img = path_pics + '/' + name_img
            with open(path_img, 'wb') as f:
                f.write(img.content)
                f.close
            self.img_download += 1
            rtime = random.choice([0.12,0.36,0.2,0.18,0.26,0.34])
            sleep(rtime)      #下完一张图片休息

        #一个异常的处理方法
        if(num<nums):
            nums_down = num -1
            self.start_download(url_pics,nums,path_pics,nums_down)
        # 进度条换行问题解决
        print('\n', end='')


    # 查询图集中的 图片数目
    def get_nums_img(self,url_pics):
        headers_home = self.get_headers(self.url_home)
        soup = self.get_soup(url_pics,headers_home)

        nums = soup.select('.pagenavi > a')[-2].text
        return int(nums)


    # 查询本地下载情况
    def is_download(self,url_pics,name_pics,nums):
        path_pics = self.path_download + '\\' + name_pics
        if(os.path.exists(path_pics)):
            if(len(os.listdir(path_pics))==nums):
                print('已经下载：{}'.format(name_pics))
                flag=1                              #判断是否睡眠 2秒 及 是否调用 下载图片的循环
                nums_down=nums
                self.dir_done += 1
                self.img_exist += nums
            else:
                nums_down = len(os.listdir(path_pics))
                print('继续下载：{}'.format(name_pics))
                flag=0
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


        #控制图集循环

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
            info=self.is_download(url_pics,name_pics,nums)

            # 只有图集未创建 和 图集未下完 才启动 下载图片的循环
            if(info[-1] == 0):
                path_pics = info[0]
                nums_down = info[1]
                self.start_download(url_pics, nums, path_pics, nums_down)
                rtime = random.choice([2,1.5,1.75,2.5,2.25])
                sleep(rtime)           #一个图集下完后休息


    #获取图集的入口和名字 : 列表的列表，一个内列表是一个图集的url拼接元素和名字
    def get_pics_list(self,url_page,referer_page):
        headers_page=self.get_headers(referer_page)
        soup = self.get_soup(url_page,headers_page)

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
                rtime = random.choice([4.5,5.3,3.8,4.1,5.8])
                sleep(rtime)  #一个页面下完后休息

            self.dir_new_page = 0
            self.dir_goon_page = 0
            
    def output_info_download(self):
        pics_ing = self.dir_new_pages + self.dir_goon_pages
        pics_down = self.dir_done
        pics_all = pics_down + pics_ing
        img_ing = self.img_download
        img_down = self.img_exist
        img_all = img_ing + img_down
        print("共{2}个图集：新下载图集：{0}个；已下载图集：{1}个；".format(pics_ing,pics_down,pics_all))
        print("共{2}张图片：新下载图片：{0}张；已下载图片：{1}张；".format(img_ing,img_down,img_all))

def main():


    print("{0}所以你准备好纸巾了么{0}".format('__*_*__'*5))
    print('\n'*2)
    print('{0}下载的图片默认路径："E:\\Mzitu",选择默认请回车{0}'.format('*'*2))
    print('\n')
    download_path_self = input('自定义请输入存储路径：')
    download_path = 'E:\\Mzitu'
    if(download_path_self == ''):
        download_path = download_path
    else:
        download_path = download_path_self
    if not(os.path.exists(download_path)):
        os.mkdir(download_path)

    page_start = input('请输入起始页码：')
    page_end = input('请输入结束页码：')
    # page_start = 1
    # page_end = 1

    # 创建对象，启动爬取程序
    spider = MzituSpider(page_start,page_end,download_path)
    spider.run()
    spider.output_info_download()
    end = input('这是用来停住命令行的！')

if __name__ == '__main__':
    main()