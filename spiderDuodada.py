# -*- coding: utf-8 -*-
import json
import os
import shutil

from urllib import parse
from lxml import etree
import requests
import re

from multiprocessing import Pool


def long_time_task(url, path):
    if not os.path.exists(path):
        try:
            res = requests.get(url, timeout=30)
            # 写入文件
            with open(path, 'ab') as f:
                f.write(res.content)
                f.flush()
        except:
            print('重试：{0}'.format(url))
            long_time_task(url, path)


class DownloadVideo:
    def __init__(self, start_url, title, download_all=False, base_dir=os.getcwd()):
        """

        :param start_url: 视频的观看链接
        :param title: 电视的名字(用于创建文件夹)
        :param download_all: 是否下载电视剧全集，(如：放入庆余年31集的播放地址，则下载电视剧所有的剧集，否则，只下载第31集)
        :param base_dir: 下载的文件的 保存目录
        """
        self.__start_url = start_url
        self.__header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'
        }
        self.__download_type = 'all' if download_all else 'part'
        self.__start_urls = []
        self.__title = title
        self.__save_dir = ''
        self.__file_name = ''
        self.__base_dir = base_dir

    def __download_html(self, url):
        """
        下载网页
        :param url:
        :return:
        """
        html = requests.get(url, headers=self.__header, timeout=30).text
        return html

    def __get_index_url(self, url):
        """
        m3u8文件预处理，生成文件名，后续的爬取地址
        :param url: 每一集播放地址的url
        :return:
        """
        html = self.__download_html(url)
        result = etree.HTML(html)
        # 获取视频加载的起始地址
        location = result.xpath('//*[@id="iFrame_play"]/script/@src')[0]
        file_name = result.xpath('/html/body/div[2]/div/div[1]/div[1]/h4/a[3]//text()')
        file_index = result.xpath('/html/body/div[2]/div/div[1]/div[1]/h4/small//text()')
        index = re.findall(re.compile(r'\d*?集'), str(file_index[0]))
        self.__file_name = file_name[0] + str(index[0])
        print("当前处理的电视名：", file_name[0], file_index[0])
        #  提取m3u8起始文件地址
        html = self.__download_html(location)
        pat = re.compile(r'﻿var cms_player = (.*?);document.write')
        find_result = re.findall(pattern=pat, string=html)
        assert len(find_result) == 1, '未找到资源的起始播放链接'
        info_dict = json.loads(find_result[0])
        # 此url为m3u8文件地址
        url = info_dict['url']
        self.__get_redirect_url(url)

    def __get_redirect_url(self, url):
        """
        获取重定向后的m3u8下载地址
        即从第一个m3u8文件中找到第二个m3u8文件的url
        :return:
        """
        # 内容有三行，做成列表以取最后一行内容
        all_content = requests.get(url).text
        file_data = all_content.split("\n")
        new_url = parse.urljoin(url, file_data[-1])

        self.__download_ts(new_url)

    def __download_ts(self, url):
        """
        下载ts片段，合并文件
        :param url: 有ts文件名的m3u8文件的url
        :return:
        """
        # 合并文件后的保存文件夹,也是ts流的保存文件夹；合并后会删除ts流文件，仅留下最后合成文件
        self.__save_dir = self.__base_dir + os.sep + r"download" + os.sep + self.__title
        download_path = self.__save_dir + os.sep + self.__file_name
        if not os.path.exists(download_path):
            os.makedirs(download_path)
        # 最终保存的文件名
        end_file_name = os.path.join(self.__save_dir, self.__file_name) + '.ts'
        # 判断文件是否已经下载过了
        if os.path.exists(end_file_name):
            print('{0} 该文件已下载'.format(end_file_name))
            return

        # 读取m3u8文件里的每一行，迭代下载，并生成新文件
        all_content = requests.get(url).text
        file_line = all_content.split("\n")
        # 通过判断文件头来确定是否是M3U8文件
        if file_line[0] != "#EXTM3U":
            raise BaseException(u"非M3U8的链接")
        else:
            unknow = True  # 用来判断是否找到了下载的地址
            # 多进程爬取

            p = Pool(30)
            try:
                print(len(file_line))
                for index, line in enumerate(file_line):
                    line = line.strip()
                    if "EXTINF" in line:
                        unknow = False
                        # 拼出ts片段的URL
                        part_url = parse.urljoin(url, file_line[index+1])
                        c_file_name = str(file_line[index + 1])
                        tmp_ts_save_path = os.path.join(download_path, c_file_name)

                        # 开启异步任务
                        p.apply_async(long_time_task, (part_url, tmp_ts_save_path))
            except:
                pass
            finally:
                p.close()
                p.join()

            if unknow:
                raise BaseException(u"未找到对应的下载链接")
            else:
                print(u"{0} 下载完成".format(self.__file_name))

        print('开始合并文件：{0}'.format(self.__file_name))
        try:
            s = r"copy /b  {0}{1}*.ts  {2}".format(download_path, os.sep, end_file_name)
            os.system(s)
            #  删除小文件
            shutil.rmtree(download_path)
        except BaseException as e:
            print(e.args)

    def __get_start_urls(self):
        if self.__download_type == 'all':
            html = self.__download_html(self.__start_url)
            result = etree.HTML(html)
            all_href = result.xpath('//*[@id="M3U8"]/ul/li/a/@href')
            #  href格式如："/dianshiju/48615/player-2-1.html"
            #   每一集播放地址的完整url："http://www.duodada.com/dianshiju/48615/player-2-1.html"
            for href in all_href:
                self.__start_urls.append(parse.urljoin(self.__start_url, href))
        else:
            self.__start_urls.append(self.__start_url)

        # 需要加修正 要爬取的集数因该从起始url往后！！
        # self.__start_urls = self.__start_urls[40:]
        print('本次任务共爬取电视 {0} 集'.format(len(self.__start_urls)))
        for tmp_url in self.__start_urls:
            self.__get_index_url(tmp_url)

    def start_wodnload(self):
        self.__get_start_urls()


if __name__ == '__main__':
    video_url = "http://www.duodada.com/dianshiju/48615/player-2-32.html"
    video_title = '庆余年'
    qyn = DownloadVideo(start_url=video_url, title=video_title, download_all=False, base_dir=r'E:\BaiduNetdiskDownload')
    qyn.start_wodnload()
