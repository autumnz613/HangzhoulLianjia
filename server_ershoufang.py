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


def one_record_spider(ershoufang):
    """
    爬取一个二手房所有信息，记录到dict中
    """
    info_dict = {}

    houseTitle = ershoufang.find("div", {"class": "title"})
    href = houseTitle.a.get("href")
    info_dict['链接'] =  href

    total_price = ershoufang.find("div", {"class": "totalPrice"}).text
    info_dict['价格'] =  total_price

    house_info = ershoufang.find("div", {"class": "houseInfo"}).get_text().strip()
    info = house_info.split("|")
    if info:
        info_dict['小区名称'] =  info[0]
        info_dict['户型'] =  info[1].strip()
        info_dict['面积'] =  info[2].strip()
        info_dict['朝向'] =  info[3].strip()
        info_dict['装修'] =  info[4].strip()
        info_dict['电梯'] =  info[-1].strip()

    position_info = ershoufang.find("div", {"class": "positionInfo"}).text
    info = position_info.strip().split(")")
    floor= info[0].strip()+")"
    buildtime = info[-1].split("-")[0].strip()
    info_dict['楼层'] =  floor
    info_dict['建造时间'] =  buildtime
    bankuai = info[-1].split("-")[-1]
    info_dict['板块'] =  bankuai

    follow_info = ershoufang.find("div", {"class": "followInfo"}).get_text().split("/")
    concerned = follow_info[0].strip()
    visit = follow_info[1].strip()
    date = follow_info[2].strip()
    info_dict['关注人数'] =  concerned
    info_dict['看房次数'] =  flovisitor
    info_dict['发布时间'] =  date

    unitPrice = ershoufang.find("div", {"class": "unitPrice"}).find("span").text
    info_dict['均价'] =  unitPrice

    detail = ershoufang.find("div", {"class": "tag"}).text
    if detail:
        info_dict['备注'] =  detail

    return info_dict


def ershoufang_spider(url_page):
    """
    爬取页面链接中的小区二手房信息
    """
    try:
        req = urllib2.Request(url_page, headers=hds[random.randint(0, len(hds) - 1)])
        source_code = urllib2.urlopen(req, timeout=10).read()
        plain_text = unicode(source_code)
        soup = BeautifulSoup(plain_text, "html.parser")
    except (urllib2.HTTPError, urllib2.URLError), e:
        print e
        return

    info_list = []
    ershoufang_list = soup.findAll("div", {"class": "info clear"})
    for ershoufang in ershoufang_list:
        info_dict = one_record_spider(ershoufang)
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


def region_ershoufang_spider(region):
    """
    爬取城区成交记录
    """
    url = u"http://hz.lianjia.com/ershoufang/" + region + "/"

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
        page_info = soup.find("div", {"class": "page-box house-lst-page-box"})
    except AttributeError as e:
        page_info = None
    if page_info == None:
        return None
    page_info_str = page_info.get("page-data").split(",")[0].split(":")[1]
    total_pages = int(page_info_str)

    #循环实现爬取所有页面
    for i in range(total_pages):
        url_page = u"http://hz.lianjia.com/ershoufang/%s/pg%d/" % (region,i + 1)
        ershoufang_spider(url_page)


def recent_ershoufang_spider(href):
    """
    爬取页面链接中的成交记录
    """
    total_pages = 100   #根据实际爬取频率确定，一般不大于10
    flag = 0
    #循环实现爬取所有页面
    for i in range(total_pages):
        url_page = u"http://hz.lianjia.com/ershoufang/pg%d/" % (i + 1)

        try:
            req = urllib2.Request(url_page, headers=hds[random.randint(0, len(hds) - 1)])
            source_code = urllib2.urlopen(req, timeout=10).read()
            plain_text = unicode(source_code)
            soup = BeautifulSoup(plain_text, "html.parser")
        except (urllib2.HTTPError, urllib2.URLError), e:
            print e
            return
        info_list = []
        ershoufang_list = soup.findAll("div", {"class": "info clear"})
        for ershoufang in ershoufang_list:
            info_dict = one_record_spider(ershoufang)
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


def regions_ershoufang_spider():
    """
    爬去所有城区成交记录
    """
    for region in regions:
        region_ershoufang_spider(region)
        print '已经爬取了%s区成交记录' % dict[region]
    print 'done'


if __name__ == "__main__":
    """
    传递参数为上次爬取记录最新一条的小区链接，或者为0。必填。
    """
    href = sys.argv[1]
    if href:
        #爬下最新成交记录
        recent_ershoufang_spider(href)
    else:
        # 爬下所有小区里的成交信息
        regions_ershoufang_spider()
