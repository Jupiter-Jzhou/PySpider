import re
import Comunit

url = "https://mp.weixin.qq.com/s/s5ow4FoOKDS_DA6sPY1ysA"

# r = ComUnit.send_requests(url, url, need="response")
tree = Comunit.send_requests(url, url, need="xpath")
ret = tree.xpath("//div[@id='js_content']/p/text()")
ret.pop(0)
ret.pop(-1)

a = []
b = []
pat = "http.*com|http.*cn|http.*net|http.*me"

for i in ret:
    if "http" in i:
        n = re.compile(pat).findall(i)
        a = a + n
        # a.append(i.strip())        # 去首尾的空格

for i in a:
    try:
        r = Comunit.send_requests(i, i, need="response", mode="empty")
    except:
        continue
    if r.status_code is 200:
        b.append(i)
for i in b:
    print(i)

