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

# 杭州区域列表
regions = [u"xihu", u"xiacheng", u"jianggan", u"gongshu", u"shangcheng", u"binjiang", u"yuhang", u"xiaoshan"]
#regions = [u'binjiang']

dict = {"xihu": "西湖", "xiacheng": "下城", "jianggan": "江干", "gongshu": "拱墅", "shangcheng": "上城",
        "binjiang": "滨江", "yuhang": "余杭", "xiaoshan": "萧山"}

lock = threading.Lock()

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

def gen_xiaoqu_insert_command(info_dict):
    """
    生成小区数据库插入命令
    """
    info_list = [u'小区名称', u'城区', u'板块', u'小区均价', u'在售', u'链接',u'标识']
    t = []
    for il in info_list:
        if il in info_dict:
            t.append(info_dict[il])
        else:
            t.append('')
    t = tuple(t)
    command = (r"insert into xiaoqu values(?,?,?,?,?,?,?)", t)
    return command


def xiaoqu_spider(db_xiaoqu, url_page):
    """
    爬取一个页面链接中的小区信息
    """
    try:
        # 请求城区信息
        req = urllib2.Request(url_page, headers=hds[random.randint(0, len(hds) - 1)])
        # 获取响应源码
        source_code = urllib2.urlopen(req, timeout=10).read()
        plain_text = unicode(source_code)  # ,errors='ignore')
        # 使用beautifulsoup解析dom
        soup = BeautifulSoup(plain_text, "html.parser")
    except (urllib2.HTTPError, urllib2.URLError), e:
        print e
        exit(-1)
    except Exception, e:
        print e
        exit(-1)

    xiaoqu_list = soup.findAll("li", {"class": "clear xiaoquListItem"})
    for xiaoqu in xiaoqu_list:
        info_dict = {}

        #小区信息
        xiaoquinfo = xiaoqu.find("div", {"class", "info"})
        title = xiaoquinfo.find("div", {"class": "title"})

        info_dict.update({u'小区名称': title.text})

        href = title.a.get('href')
        info_dict.update({u'链接': href})

        district = xiaoquinfo.find("a", {"class": "district"})
        info_dict.update({u'城区': district.get_text().strip()})

        bizcircle = xiaoquinfo.find("a", {"class": "bizcircle"})
        info_dict.update({u'板块': bizcircle.get_text().strip()})

        #小区均价和在售
        itermright = xiaoqu.find("div", {"class": "xiaoquListItemRight"})

        averageprice = itermright.find("div", {"class": "totalPrice"}).get_text().strip()
        info_dict.update({u'小区均价': averageprice})

        onsale = itermright.find("a", {"class": "totalSellCount"}).get_text().strip()
        info_dict.update({u'在售': onsale})

        command = gen_xiaoqu_insert_command(info_dict)
        db_xiaoqu.execute(command, 1)


def do_xiaoqu_spider(db_xiaoqu, region):
    """
    爬取一个城区中的所有页面
    """
    url = u"http://hz.lianjia.com/xiaoqu/" + region + "/"
    try:
        req = urllib2.Request(url, headers=hds[random.randint(0, len(hds) - 1)])
        source_code = urllib2.urlopen(req, timeout=5).read()
        plain_text = unicode(source_code)  # ,errors='ignore')
        soup = BeautifulSoup(plain_text, "html.parser")
    except (urllib2.HTTPError, urllib2.URLError), e:
        print e
        return
    except Exception, e:
        print e
        return

    try:
        page_info= soup.find("div", {"class": "page-box house-lst-page-box"})
    except AttributeError as e:
        page_info = None
    if page_info == None:
        return None

    page_info_str = page_info.get("page-data").split(",")[0].split(":")[1]
    total_pages= int(page_info_str)

    threads = []
    for i in range(total_pages):
        url_page = u"http://hz.lianjia.com/xiaoqu/%s/pg%d" % (region, i + 1)
        t = threading.Thread(target=xiaoqu_spider, args=(db_xiaoqu, url_page))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print u"爬下了%s区全部的小区信息" % dict[region]


def exception_write(fun_name, url):
    """
    写入异常信息到日志
    """
    lock.acquire()
    f = open('log.txt', 'a')
    line = "%s %s\n" % (fun_name, url)
    f.write(line)
    f.close()
    lock.release()


if __name__ == "__main__":
    command = "create table if not exists xiaoqu (title TEXT primary key UNIQUE, regionb TEXT, regions TEXT, averageprice TEXT, onsale TEXT, href TEXT, flag TEXT)"
    db_xiaoqu = SQLiteWraper('lianjia-xiaoqu.db', command)

    # 爬下所有的小区信息
    for region in regions:
        do_xiaoqu_spider(db_xiaoqu, region)


