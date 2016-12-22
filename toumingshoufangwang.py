# -*- coding: utf-8 -*-

import re
import urllib2
import sqlite3
import random
import threading
from bs4 import BeautifulSoup

import sys

reload(sys)
sys.setdefaultencoding("utf-8")

# Some User Agents
hds = [{'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'}, \
       {'User-Agent': 'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.12 Safari/535.11'}, \
       {'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Trident/6.0)'}, \
       {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:34.0) Gecko/20100101 Firefox/34.0'}, \
       {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/44.0.2403.89 Chrome/44.0.2403.89 Safari/537.36'}, \
       {'User-Agent': 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50'}, \
       {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50'}, \
       {'User-Agent': 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0'}, \
       {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1'}, \
       {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1'}, \
       {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11'}, \
       {'User-Agent': 'Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11'}, \
       {'User-Agent': 'Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11'}]


class SQLiteWraper(object):
    """
    数据库的一个小封装，更好的处理多线程写入
    """

    def __init__(self, path, command='', *args, **kwargs):
        self.lock = threading.RLock()  # 锁
        self.path = path  # 数据库连接参数

        if command != '':
            conn = self.get_conn()
            cu = conn.cursor()
            cu.execute(command)

    def get_conn(self):
        conn = sqlite3.connect(self.path)  # ,check_same_thread=False)
        conn.text_factory = str
        return conn

    def conn_close(self, conn=None):
        conn.close()

    def conn_trans(func):
        def connection(self, *args, **kwargs):
            self.lock.acquire()
            conn = self.get_conn()
            kwargs['conn'] = conn
            rs = func(self, *args, **kwargs)
            self.conn_close(conn)
            self.lock.release()
            return rs

        return connection

    @conn_trans
    def execute(self, command, method_flag=0, conn=None):
        cu = conn.cursor()
        try:
            if not method_flag:
                cu.execute(command)
            else:
                cu.execute(command[0], command[1])
            conn.commit()
        except sqlite3.IntegrityError, e:
            # print e
            return -1
        except Exception, e:
            print e
            return -2
        return 0


def gen_jilu_insert_command(info_dict):
    """
    生成小区数据库插入命令
    """
    info_list = [u"区域", u"楼盘名称", u"链接", u"城区", u"签约套数", u"预定套数", u"签约面积", u"签约均价"]
    t = []
    for il in info_list:
        if il in info_dict:
            t.append(info_dict[il])
        else:
            t.append('')
    t = tuple(t)
    insertcommand = (r"insert into jilu values(?,?,?,?,?,?,?,?)", t)
    return insertcommand

def transfer(string):
    """
    :param string:
    :return:
    """
    if(string == [u'numbone']):
        res = "1"
    elif (string == [u'numbtwo']):
        res = "2"
    elif (string == [u'numbthree']):
        res = "3"
    elif (string == [u'numbfour']):
        res = "4"
    elif (string == [u'numbfive']):
        res = "5"
    elif (string == [u'numbsix']):
        res = "6"
    elif (string == [u'numbseven']):
        res = "7"
    elif (string == [u'numbeight']):
        res = "8"
    elif (string == [u'numbnine']):
        res = "9"
    elif (string == [u'numbzero']):
        res = "0"
    elif (string == [u'numbdor']):
        res = "."
    else:
        res = " "
    return res


def do_jilu_spider(db_jilu, link):
    """
    爬取页面链接中的成交记录
    """
    try:
        req = urllib2.Request(link, headers=hds[random.randint(0, len(hds) - 1)])
        source_code = urllib2.urlopen(req, timeout=10).read()
        plain_text = unicode(source_code)
        soup = BeautifulSoup(plain_text, "html.parser")
    except (urllib2.HTTPError, urllib2.URLError), e:
        print e
        return
    except Exception, e:
        print e
        return

    data = soup.find("div", {"class": "datanowin"})
    """
    将每个区域作为一个子节点获取出来
    可以用.children  find_next_sibling
    """
    zhuchengqu = data.find("div", {"style": "display:block"})
    xiaoshan = zhuchengqu.find_next_sibling("div")
    yuhang = xiaoshan.find_next_sibling("div")
    fuyang = yuhang.find_next_sibling("div")
    dajiangdong = fuyang.find_next_sibling("div")

    regions = {zhuchengqu, xiaoshan, yuhang, fuyang, dajiangdong}
    url_header = "www.tmsf.com"

    for region in regions:
        info_dict = {}
        #获取每个城区的所有楼盘信息
        all_loupan_info = region.findAll("tr")
        #判断每个楼盘的信息
        for loupan in all_loupan_info:
            loupan_info = loupan.find("td", {"class": "tdborder blue2"})
            if loupan_info:
                name = loupan_info.get_text()
                href = url_header + loupan_info.a.get("href")
                info_dict.update({u"区域": region})
                info_dict.update({u"楼盘名称":name})
                info_dict.update({u"链接":href})

                #区域
                district = loupan_info.find_next_sibling("td")
                info_dict.update({u"城区": district.text.strip()})

                #签约套数
                sale = district.find_next_sibling("td")
                salenumbers = sale.findAll("span")
                #循环遍历所有数字，赋给num
                salenum = ""
                for number in salenumbers:
                    original = number["class"]
                    new = transfer(original)
                    salenum = salenum + new
                info_dict.update({u"签约套数": salenum})

                #预定套数，一般为个位数
                reserved = sale.find_next_sibling("td")
                reserverdnumber = reserved.find("span")
                reserverdnum = transfer(reserverdnumber["class"])
                info_dict.update({u"预定套数":reserverdnum})

                #签约面积
                area = reserved.find_next_sibling("td")
                areanumber = area.findAll("span")
                areanum = ""
                for number in areanumber:
                    original = number["class"]
                    new = transfer(original)
                    areanum = areanum + new
                areanum = areanum + "平"
                info_dict.update({u"签约面积": areanum})

                #签约均价
                averageprice = area.find_next_sibling("td")
                averageprice_number = averageprice.findAll("span")
                averagepricenum = ""
                for number in averageprice_number:
                    original = number["class"]
                    new = transfer(original)
                    averagepricenum = averagepricenum + new
                averagepricenum = averagepricenum + "元/平"
                info_dict.update({u"签约均价":averagepricenum})

                command = gen_jilu_insert_command(info_dict)
                db_jilu.execute(command, 1)


if __name__ == "__main__":
    command = "create table if not exists jilu (region TEXT primary key UNIQUE, name TEXT, href TEXT, district TEXT, " \
              "salecount TEXT, reservedcount TEXT, area TEXT, averageprice TEXT)"
    db_jilu = SQLiteWraper('tmsf-jilu.db', command)

    href = u"http://www.tmsf.com/daily.htm"
    # 爬下所有的售房信息

    do_jilu_spider(db_jilu, href)


