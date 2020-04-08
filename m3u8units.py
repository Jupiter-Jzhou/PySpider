import comunits
import re
from urllib import parse


class M3u8(object):
    def __init__(self, **kwargs):
        self.referer = kwargs.get("referer", "")
        self.origin = kwargs.get("origin", "")
        self.proxy = kwargs.get("proxy", "")

    def get_ts(self, url_m3u8, *, mode):
        """分流
        """
        if mode == "91MJW":
            url_ts_pat, ts_total = self.get_ts_91MJW(url_m3u8)
            return url_ts_pat, ts_total
        elif mode == "pb":
            url_ts_pat, ts_total = self.get_ts_pb(url_m3u8)
            return url_ts_pat, ts_total

    def get_ts_pb(self, url_m3u8):
        """
        """
        args_requests = {
                            "referer": self.referer,
                            "origin": self.origin,
                            "proxy": self.proxy,
                            "need": "response"
                        }

        m3u8 = comunits.send_requests(url_m3u8, **args_requests)
        m3u8 = m3u8.text
        # print("第一个m3u8文件内容节选：", m3u8[:350], m3u8[-150:], sep='\n')

        # 判断如何获得ts索引文件
        if ".m3u8" in m3u8:  # 说明有两个m3u8
            a = re.compile("(.*).m3u8(.*)").search(m3u8).group(1, 2)
            m3u8b = a[0] + ".m3u8" + a[1]
            url_m3u8b = parse.urljoin(url_m3u8, m3u8b)
            ts = comunits.send_requests(url_m3u8b, **args_requests)
            ts = ts.text
        elif ".ts" in m3u8:
            ts = m3u8
            url_m3u8b = url_m3u8
        else:
            print("第一个m3u8文件有问题")
            return "", 0

        print(url_m3u8b)
        # 制作ts模板
        if "seg-" in ts:
            ts_pat = url_m3u8b.rsplit("/", 1)[-1].replace("index", "seg-{0}").replace(".m3u8", ".ts")
            url_ts_pat = parse.urljoin(url_m3u8b, ts_pat)
            # ts总数
            ts_total = re.search("seg-(.*?)-.*\n#EXT-X-ENDLIST", ts).group(1)
            ts_total = int(ts_total)
            return url_ts_pat, ts_total
        else:
            print("ts索引规律已经变了")
            return "", 0

    def get_ts_91MJW(self, url_m3u8):
        """
        m3u8可能1个或2个；ts索引可能6位或3位，或任意位

        return: url_ts的模板 和 ts总数  用于构造ts生成器
        """

        m3u8 = comunits.send_requests(url_m3u8, origin=self.origin, need="response")
        m3u8 = m3u8.text
        print("第一个m3u8文件内容节选：", m3u8[:350], m3u8[-150:], sep='\n')

        # 判断如何获得ts索引文件
        if ".m3u8" in m3u8:  # 说明有两个m3u8
            part = re.findall("\n(.+)m3u8", m3u8)
            m3u8b = part[0] + "m3u8"
            url_m3u8b = parse.urljoin(url_m3u8, m3u8b)
            ts = comunits.send_requests(url_m3u8b, origin=self.origin, need="response")
            ts = ts.text
        elif ".ts" in m3u8:
            ts = m3u8
            url_m3u8b = url_m3u8
        else:
            return "", 0

        # 找到处理 ts
        # 找头尾的两个ts
        ts_start = re.search("(.*).ts", ts, re.X).group(1)  # X 忽略空格和#后的东西
        ts_end = re.search("(.*).ts\n#EXT-X-ENDLIST", ts).group(1)
        # 找出ts是几位数的索引
        diff = 0
        for i in range(len(ts_end) - 1):
            if ts_start[i] != ts_end[i]:
                diff = i
                break
        # 制作ts模板
        ts_pat = ts_end[:diff] + "{0}.ts"
        url_ts_pat = parse.urljoin(url_m3u8b, ts_pat)
        # ts总数
        ts_total = ts_end[diff:]
        ts_total = int(ts_total)+1

        return url_ts_pat, ts_total



