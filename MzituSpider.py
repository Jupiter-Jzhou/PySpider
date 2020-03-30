import os
import comunit
import time

path_default = 'E:\\Mzitu'
url_home = 'https://www.mzitu.com'
proxy = {}


def start_download(pics, url_pics, num_start, url_page, path_page):
    """
    获取图集的图片总数
    制作图片的 url 和 referer
    图片循环下载
    """

    # 从图集首页获取 图片总数
    soup = comunit.send_requests(url_pics, url_page, proxy)
    nums = soup.select('.pagenavi > a')[-2].text
    nums = int(nums)
    print("正在下载：{0}".format(pics))
    # 图片循环下载
    for num in range(num_start,nums+1):
        # 是否顺带第一张图片下载地址
        if num == 1:
            img = soup.select('.main-image>p>a>img')
            url_img = img[0].attrs['src']
            url_img_show = url_pics
        else:
            if num == 2:
                url_img_show = url_pics + '/' + "2"
                referer_show = url_pics
            else:
                url_img_show = url_pics + '/' + str(num)
                referer_show = url_pics + '/' + str(num-1)

            # 获取图片下载地址
            soup = comunit.send_requests(url_img_show, referer_show, proxy)
            img = soup.select('.main-image>p>a>img')
            url_img = img[0].attrs['src']

        response = comunit.send_requests(url_img, url_img_show, proxy, need="response")
        if num == nums:
            path_img = path_page + "\\" + pics + "_" + str(num) + "_L.jpg"
        else:
            path_img = path_page + '\\' + pics + '_' + str(num) + '_.jpg'

        with open(path_img, 'wb') as f:
            f.write(response.content)
        comunit.show_bar(num, nums)  # 进度条
        time.sleep(0.3)


def get_pics(page):
    """
    制作页面 url referer    进入下一页的请求头中的referer是上一页
    返回 页所有图集的字典 —— 名字：链接
    """
    # 制作页面 url referer
    if page == 1:
        url_page = url_home
        referer_page = url_page
    elif page == 2:
        url_page = url_home + '/' + 'page' + '/' + '2' + '/'
        referer_page = url_home
    else:
        url_page = url_home + '/' + 'page' + '/' + str(page)+ '/'
        referer_page = url_home + '/' + str(page - 1) + '/'

    # 返回 页所有图集的字典—— 名字：链接
    soup = comunit.send_requests(url_page, referer_page, proxy)
    items = soup.select('.postlist li')
    pics_dic = {}
    for item in items:
        href = item.select('a')[1]['href']
        name = item.select('a')[1].text
        pics_dic[name] = href

    return pics_dic, url_page


def main():
    print('\n')
    print("{0}所以你准备好纸巾了么{0}".format('__*_*__' * 5))
    print('\n' * 2)
    print('{0}默认图片下载路径：{1},选择默认请回车{0}'.format('*'*25,path_default))
    print('\n')
    page_list = input("请输入要下载的页码：")
    path = input('自定义请输入存储路径：')

    if path == '':
        path = path_default

    if not(os.path.exists(path)):
        os.mkdir(path)

    page_list = comunit.deal_input_num(page_list)         # 页码格式化处理 返回字符
    page_list = [int(i) for i in page_list]               #  页码处理成 int型
    for page in page_list:
        print("{1}准备下载第 {0} 页{1}".format(page,"*"*35))
        path_page = path + "\\" + "No.{}".format(page)                # 以页建文件夹
        if not (os.path.exists(path_page)):
            os.mkdir(path_page)

        name_done_list, name_ing_dic = comunit.check_local(path_page)
        # 页所有图集的字典 {名：url}
        pics_dic, url_page = get_pics(page)
        # 需要下载图集的字典{名：数}
        local_dic, pics_dic = comunit.is_download(pics_dic, name_done_list, name_ing_dic)

        pics_list = list(pics_dic)
        for pics in pics_list:
            url_pics = pics_dic[pics]
            num_start = local_dic[pics]
            start_download(pics, url_pics, num_start, url_page, path_page)
            time.sleep(1)
        print("{1}完成下载第 {0} 页{1}".format(page, "*" * 35))
    end = input('这是用来停住命令行的！')


if __name__ == '__main__':
    main()
                 


                 
                 
                 
                 
                 
                 
                 
                 
                 
      