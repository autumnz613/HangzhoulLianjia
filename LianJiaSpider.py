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

    @conn_trans
    def fetchall(self, command="select name from xiaoqu", conn=None):
        cu = conn.cursor()
        lists = []
        try:
            cu.execute(command)
            lists = cu.fetchall()
        except Exception, e:
            print e
            pass
        return lists


def gen_chengjiao_insert_command(info_dict):
    """
    生成成交记录数据库插入命令
    """
    info_list = [u'房源链接',u'城区', u'小区名称', u'户型', u'面积', u'朝向', u'装修', u'电梯', u'楼层', u'建造时间',
                 u'签约时间', u'签约单价', u'签约总价', u'交通',u'标识']
    t = []
    for il in info_list:
        if il in info_dict:
            t.append(info_dict[il])
        else:
            t.append('')
    t = tuple(t)
    # 生成每一个小区对应的成交记录命令
    command = (r"insert into chengjiao values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", t)
    return command


def chengjiao_spider(db_chengjiao, url_page, region):
    """
    爬取页面链接中的成交记录
    """
    try:
        req = urllib2.Request(url_page, headers=hds[random.randint(0, len(hds) - 1)])
        source_code = urllib2.urlopen(req, timeout=10).read()
        plain_text = unicode(source_code)  # ,errors='ignore')
        soup = BeautifulSoup(plain_text, "html.parser")
    except (urllib2.HTTPError, urllib2.URLError), e:
        print e
        exception_write('chengjiao_spider', url_page)
        return
    except Exception, e:
        print e
        exception_write('chengjiao_spider', url_page)
        return

    chengjiao_list = soup.findAll("div", {"class": "info"})
    for chengjiao in chengjiao_list:
        info_dict = {}

        houseTitle = chengjiao.find("div", {"class": "title"})
        href = houseTitle.a.get("href")
        info_dict.update({u'房源链接': href})
        info_dict.update({u'城区': dict[region]})

        content = houseTitle.get_text().split(" ")
        if content:
            info_dict.update({u'小区名称': content[0]})
            info_dict.update({u'户型': content[1]})
            info_dict.update({u'面积': content[2]})

        houseInfo = chengjiao.find("div", {"class": "houseInfo"}).get_text()
        info = houseInfo.split("|")
        if info:
            info_dict.update({u'朝向': info[0].strip()})
            info_dict.update({u'装修': info[1].strip()})
            if len(info) > 2:
                info_dict.update({u'电梯': info[2].strip()})
            else:
                continue

        positionInfo = chengjiao.find("div", {"class": "positionInfo"}).text

        info = positionInfo.strip().split(")")
        floor= info[0].strip()+")"
        buildtime = info[-1]
        info_dict.update({u'楼层': floor})
        info_dict.update({u'建造时间': buildtime})

        dealDate = chengjiao.find("div", {"class": "dealDate"}).get_text().strip()
        info_dict.update({u'签约时间': dealDate})

        #个别没有成交均价
        unitPrice = chengjiao.find("div", {"class": "unitPrice"}).find("span")
        if unitPrice:
            unitPrice= unitPrice.text+"元/平"
            info_dict.update({u'签约单价': unitPrice})

        totalPrice = chengjiao.find("span", {"class": "number"}).text.strip()+"万"
        info_dict.update({u'签约总价': totalPrice})

        traffic = chengjiao.find("div", {"class": "dealHouseInfo"}).text
        if traffic:
            info_dict.update({u'交通': traffic})

        command = gen_chengjiao_insert_command(info_dict)
        db_chengjiao.execute(command, 1)


def region_chengjiao_spider(db_chengjiao, region ):
    """
    爬取城区成交记录
    """
    url = u"http://hz.lianjia.com/chengjiao/" + region + "/"

    try:
        req = urllib2.Request(url, headers=hds[random.randint(0, len(hds) - 1)])
        source_code = urllib2.urlopen(req, timeout=10).read()
        plain_text = unicode(source_code)
        soup = BeautifulSoup(plain_text, "html.parser")
    except (urllib2.HTTPError, urllib2.URLError), e:
        print e
        exception_write("xiaoqu_chengjiao_spider", region)
        return
    except Exception, e:
        print e
        exception_write("xiaoqu_chengjiao_spider", region)
        return

    total_pages = 1
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
        url_page = u"http://hz.lianjia.com/chengjiao/%s/pg%d/" % (region,i + 1)
        t = threading.Thread(target=chengjiao_spider, args=(db_chengjiao, url_page, region))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def regions_chengjiao_spider( db_chengjiao):
    """
    爬去所有城区成交记录
    """
    for region in regions:
        region_chengjiao_spider(db_chengjiao, region)

        print '已经爬取了%s区成交记录' % dict[region]
    print 'done'


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

    command = "create table if not exists chengjiao (href TEXT primary key UNIQUE, region TEXT, name TEXT," \
              " style TEXT, area TEXT, orientation TEXT, decoration TEXT, elevator TEXT, floor TEXT, year TEXT, " \
              "sign_time TEXT, unit_price TEXT, total_price TEXT, traffic TEXT, flag TEXT)"
    db_chengjiao = SQLiteWraper('lianjia-chengjiao.db', command)


    # 爬下所有小区里的成交信息
    regions_chengjiao_spider(db_chengjiao)

