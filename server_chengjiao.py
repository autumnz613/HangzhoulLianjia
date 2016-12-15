# -*- coding: utf-8 -*-

import re
import urllib2
import httplib, urllib
import random
import json
import sys
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

dict = {"xihu": "西湖", "xiacheng": "下城", "jianggan": "江干", "gongshu": "拱墅", "shangcheng": "上城",
        "binjiang": "滨江", "yuhang": "余杭", "xiaoshan": "萧山"}


def one_record_spider(chengjiao):
    """
    爬取一个成交记录内所有信息，记录到dict中
    """
    info_dict = {}

    houseTitle = chengjiao.find("div", {"class": "title"})
    href = houseTitle.a.get("href")
    info_dict['链接'] =  href

    content = houseTitle.get_text().split(" ")
    if content:
        info_dict['小区名称'] =  content[0]
        info_dict['户型'] =  content[1]
        info_dict['面积'] =  content[2]

    houseInfo = chengjiao.find("div", {"class": "houseInfo"}).get_text()
    info = houseInfo.split("|")
    if info:
        info_dict['朝向'] = info[0].strip()
        info_dict['装修'] = info[1].strip()
        if len(info) > 2:
            info_dict['电梯'] = info[2].strip()

    positionInfo = chengjiao.find("div", {"class": "positionInfo"}).text
    info = positionInfo.strip().split(")")
    floor= info[0].strip()+")"
    buildtime = info[-1]
    info_dict['楼层'] = floor
    info_dict['建造时间'] = buildtime

    dealDate = chengjiao.find("div", {"class": "dealDate"}).get_text().strip()
    info_dict['签约时间'] =  dealDate

    #个别没有成交均价
    unitPrice = chengjiao.find("div", {"class": "unitPrice"}).find("span")
    if unitPrice:
        unitPrice= unitPrice.text+"元/平"
        info_dict['签约单价'] = unitPrice

    totalPrice = chengjiao.find("span", {"class": "number"}).text.strip()+"万"
    info_dict['签约总价']  = totalPrice

    traffic = chengjiao.find("div", {"class": "dealHouseInfo"}).text
    if traffic:
        info_dict[u'交通'] = traffic

    return info_dict


def chengjiao_spider(url_page):
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
        return

    info_list = []
    chengjiao_list = soup.findAll("div", {"class": "info"})
    for chengjiao in chengjiao_list:
        info_dict = one_record_spider(chengjiao)
        info_list.append(info_dict)

    #将info_list通过HTTP请求发送出去
    httpClient = None
    try:
        headers = {"Content-type": "application/json; charset = UTF-8", "Accept": "application/json"}
        httpClient = httplib.HTTPConnection("10.242.109.29", 80, timeout=30)
        httpClient.request("POST", "/ajax/open/result/record/housedeal", json.dumps(info_list, encoding = "utf-8", ensure_ascii=False), headers)
        response = httpClient.getresponse()
        print response.status
        print response.getheaders()
    except Exception, e:
        print e
    finally:
        if httpClient:
            httpClient.close()


def region_chengjiao_spider(region):
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
        return

    total_pages = 1
    try:
        page_info= soup.find("div", {"class": "page-box house-lst-page-box"})
    except AttributeError as e:
        page_info = None
    if page_info == None:
        return None
    page_info_str = page_info.get("page-data").split(",")[0].split(":")[1]
    total_pages = int(page_info_str)

    #循环实现爬去所有页面
    for i in range(total_pages):
        url_page = u"http://hz.lianjia.com/chengjiao/%s/pg%d/" % (region,i + 1)
        chengjiao_spider(url_page, region)


def recent_chengjiao_spider(href):
    """
    爬取页面链接中的成交记录
    """
    total_pages = 100

    #循环实现爬去所有页面
    for i in range(total_pages):
        url_page = u"http://hz.lianjia.com/chengjiao/pg%d/" % (i + 1)

        try:
            req = urllib2.Request(url_page, headers=hds[random.randint(0, len(hds) - 1)])
            source_code = urllib2.urlopen(req, timeout=10).read()
            plain_text = unicode(source_code)  # ,errors='ignore')
            soup = BeautifulSoup(plain_text, "html.parser")
        except (urllib2.HTTPError, urllib2.URLError), e:
            print e
            return
        info_list = []
        chengjiao_list = soup.findAll("div", {"class": "info"})
        for chengjiao in chengjiao_list:
            info_dict = one_record_spider(chengjiao)
            info_list.append(info_dict)

            #已爬取到上次位置
            if (info_dict["链接"]) == href:
                flag = 1

        #将info_list通过HTTP请求发送出去
        httpClient = None
        try:
            headers = {"Content-type": "application/json; charset = UTF-8", "Accept": "application/json"}
            httpClient = httplib.HTTPConnection("10.242.109.29", 80, timeout=30)
            httpClient.request("POST", "/ajax/open/result/record/housedeal", json.dumps(info_list, encoding = "utf-8", ensure_ascii=False), headers)
            response = httpClient.getresponse()
            print response.status
            print response.getheaders()
        except Exception, e:
            print e
        finally:
            if httpClient:
                httpClient.close()

        if flag == 1:
            break


def regions_chengjiao_spider():
    """
    爬去所有城区成交记录
    """
    for region in regions:
        region_chengjiao_spider(region)
        print '已经爬取了%s区成交记录' % dict[region]
    print 'done'


def exception_write(fun_name, url):
    """
    写入异常信息到日志
    """
    f = open('log.txt', 'a')
    line = "%s %s\n" % (fun_name, url)
    f.write(line)
    f.close()

if __name__ == "__main__":
    href = sys.arg[1]

    if href:
        #爬下最新成交记录
        recent_chengjiao_spider(href)
    else:
        # 爬下所有小区里的成交信息
        regions_chengjiao_spider()

    #recent_chengjiao_spider("www.baidu.com")
