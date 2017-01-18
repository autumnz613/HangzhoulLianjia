# -*- coding: utf-8 -*-
# author:hzsongjie1
# 1、根据会议室列表爬取选择日期内所有可用时间段，得到会议室相关信息，返回room_info_list
# 2、根据用户楼层、时间段等需求，筛选room_info_list，筛选出符合条件的会议室信息selected_room_info
# 3、根据selected_room_info，预定会议室

import threading
import sys
import time
import datetime
import requests
import httplib
import json
import re
from datetime import timedelta
from bs4 import BeautifulSoup

reload(sys)
sys.setdefaultencoding("utf-8")

present_time = time.strftime('%Y-%m-%d %H:%M',time.localtime(time.time()))
now_date_time = datetime.datetime.strptime(present_time, "%Y-%m-%d %H:%M")
now_date = now_date_time.date()
now_time = now_date_time.time()
room_info_list = []
log_error = []

login_header = {'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding':'gzip, deflate','Accept-Language':'zh-CN,zh;q=0.8,en;q=0.6',
                'Host':'login.netease.com','Origin':'https://login.netease.com',
                'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/50.0.2661.102 Safari/537.36'}
br_header = {'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
             'Accept-Encoding':'gzip, deflate','Accept-Language':'zh-CN,zh;q=0.8,en;q=0.6','Host':'br.oa.netease.com',
             'Origin':'https://br.oa.netease.com','User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 '
                                                               '(KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

#所有可预定的会议室
A4_rooms = ['floor=104&room=1','floor=104&room=2','floor=104&room=5','floor=104&room=6','floor=104&room=9',
            'floor=104&room=10','floor=104&room=13','floor=104&room=15']
B3_rooms = ['floor=3&room=5','floor=3&room=7','floor=3&room=8']
B4_rooms = ['floor=4&room=1','floor=4&room=4','floor=4&room=5','floor=4&room=8','floor=4&room=9','floor=4&room=13',
            'floor=4&room=15']
B6_rooms = ['floor=6&room=1','floor=6&room=5','floor=6&room=8','floor=6&room=9','floor=6&room=13']
B7_rooms = ['floor=7&room=15','floor=7&room=21']
all_rooms = [A4_rooms,B3_rooms,B4_rooms,B6_rooms,B7_rooms]
floor_dict = {"104":"A4","3":"B3","4":"B4","6":"B6","7":"B7",}
floor_dict_reverse = {"A4":"104", "B3":"3","B4":"4","B6":"6","B7":"7"}

neighbor = {"B7":["B7","B6","B4","B3","A4"],
            "B6":["B6","B7","B4","B3","A4"],
            "B4":["B4","B3","B6","B7","A4"],
            "B3":["B3","B4","B6","B7","A4"],
            "A4":["A4","B4","B6","B3","B7"]}

capity_dict = {"A4":{"1":12,"6":12,"2":12,"5":12,"9":26,"10":12,"13":12,"15":62},
          "B3":{"5":10,"7":10,"8":12},
          "B4":{"1":12,"4":12,"5":12,"8":12,"9":12,"13":12,"15":40},
          "B6":{"1":12,"5":12,"8":12,"9":12,"13":12},
          "B7":{"15":16,"21":40}
 }

#视频会议室，包括部分需要电话预定的会议室，下同
TV_projector_rooms = ['floor=3&room=5','floor=3&room=8','floor=4&room=15','floor=5&room=10','floor=7&room=21',
                      'floor=3&room=7','floor=4&room=4','floor=4&room=5','floor=4&room=8','floor=4&room=9',
                      'floor=4&room=13','floor=6&room=1','floor=6&room=5','floor=6&room=9','floor=6&room=13',
                      'floor=7&room=15','floor=104&room=2','floor=104&room=5','floor=104&room=6','floor=104&room=9',
                      'floor=104&room=10','floor=104&room=15']
telephone_rooms = ['floor=3&room=5','floor=3&room=8','floor=6&room=1','floor=6&room=5','floor=6&room=8',
                   'floor=6&room=9','floor=6&room=13','floor=7&room=15','floor=104&room=2','floor=104&room=5',
                   'floor=104&room=6','floor=104&room=9','floor=104&room=10']


def login():
    url = "http://br.oa.netease.com/hzroom/"
    session = requests.Session()
    login_page = session.get(url, headers = login_header)
    post_data = {
        'authm':'corp',
        'trust_root':'http://br.oa.netease.com/hzroom/',
        'corpid':'hzsongjie1',
        'corppw':'Qinling1989'
    }
    reponse_url = login_page.url
    try:
        content = session.post(reponse_url, data=post_data)
        cookies = session.cookies
        return cookies
    except Exception, e:
        log_error.append(e.message)


#检查所有用户参数是否正确
def check_params(pointed_floor,request_hour,request_date, period,TV_projector,telephone,person_num,user_note):
    point_date = now_date
    TV_projector_param = False
    telephone_param = False
    hour = 0
    nums = ""
    user_msg = ""

    if(pointed_floor != "A4" or pointed_floor != "B3" or pointed_floor != "B4"or pointed_floor != "B6" or
               pointed_floor != "B7" or pointed_floor != "C2"):
        log_error.append("请选择正确的楼层")

    try:
        hour = int(request_hour)
        if (hour <= 0):
            log_error.append("时间太短")
        if ( hour > 12):
            log_error.append("时间太长")
    except Exception, e:
        log_error.append("输入的时长不是数字")
        log_error.append(e.message)

    if (request_date == "0"):
        point_date = now_date
    else:
        try:
            point_date = datetime.datetime.strptime(request_date,'%Y-%m-%d').date()
            if (point_date < now_date):
                log_error.append("输入日期是过去的时间！")
            #日期为七天以内
            seven_day = timedelta(days=7)
            if(now_date + seven_day < point_date):
                log_error.append("只能预定七天以内的会议室！")
        except Exception,e:
            log_error.append("输入日期格式不正确！")
            log_error.append(e.message)

    if(period == "-1"):
        period == "3"
    if (period != "0" or period != "1" or period != "2" or period != "3"):
        log_error.append("请选择正确的时间段！")

    if( TV_projector == "0" or TV_projector == "-1"):
        TV_projector_param = False
    elif (TV_projector == "1"):
        TV_projector_param = True
    else:
        log_error.append("电视/投影仪参数不正确")

    if( telephone == "0" or telephone == "-1"):
        telephone_param = False
    elif (telephone == "1"):
        telephone_param = True
    else:
        log_error.append("电话参数不正确")

    if(person_num == "1" or person_num == "0"):
        nums = person_num
    else:
        log_error.append("人数不正确")

    if(user_note != "-1"):
        user_msg = user_note

    return hour, point_date, TV_projector_param, telephone_param, nums,user_msg,period


def inquire_meeting_rooms(room_names, request_hour,request_date, TV_projector, telephone):
    """
    一、获取room_info_list
    1、多线程爬取所有会议室列表
    2、按照日期筛选出时间列表timelist
    3、根据timelist得到可用会议室信息room_info_list
    """
    session = requests.Session()
    for room_name in room_names:
        #判断是否含有满足条件的会议室
        has_TV_project = True
        has_telephone = True
        if (TV_projector == True):
            has_TV_project = contains_meeting_room(room_name, TV_projector_rooms)
        if (telephone == True):
            has_telephone = contains_meeting_room(room_name, telephone_rooms)

        if (has_TV_project and has_telephone):
            room_url = 'http://br.oa.netease.com/hzroom/action/bookroom/?' + room_name
            req = session.get(room_url, headers =br_header, cookies = cookies)
            soup = BeautifulSoup(req.text, 'lxml')
            checklists = soup.findAll('tr', {'class': 'checklist'})

            time_list, time_flag = get_time_list(checklists, request_date)
            #根据timelist计算是否有满足条件的时间段
            if (len(time_list) > 1 or time_flag == 1):
                fill_room_info_list(room_name, time_list, request_date, request_hour)


#判断一个列表中是否含有指定会议室
def contains_meeting_room(meeting_room, room_list):
    if(len(room_list) == 0 ):
        return False
    for room in room_list:
        if( room == meeting_room):
            return True
        else:
            continue
    return False


#找到所有可预定时间，并将符合期望的加入到timelist中
def get_time_list(checklists, request_date):
    timelist = []
    time_flag = 0

    for checklist in checklists:
        try:
            start_time = checklist.find_all('td',{'width':'21%'})[0].string
            end_time = checklist.find_all('td',{'width':'21%'})[1].string
            #过滤时间，保留与期望date符合的选项
            start_date_time = datetime.datetime.strptime(start_time,"%Y-%m-%d %H:%M")
            end_date_time = datetime.datetime.strptime(end_time,"%Y-%m-%d %H:%M")
            if (start_date_time.date() == request_date and end_date_time.date() == request_date
                and start_date_time > now_date_time):
                timelist.append(start_date_time)
                timelist.append(end_date_time)
            #对于连续多天的预定处理,会从每天最早时间开始，不需要处理
            if(start_date_time.date() == request_date and end_date_time.date() > request_date):
                pass
            if (start_date_time.date() > request_date):
                #若当天没有任何预定，则标记
                if(len(timelist) == 0):
                    time_flag = 1
                break
        except Exception, e:
            log_error.append(e.message)
    return timelist, time_flag


#根据timelist，填充room_info_list
def fill_room_info_list(room_name, timelist, request_date, request_hour):
    earlist_time_string = request_date.strftime("%Y-%m-%d ") + "09:30"
    earlist_time = datetime.datetime.strptime(earlist_time_string,"%Y-%m-%d %H:%M")
    latest_time_string = request_date.strftime("%Y-%m-%d ") + "21:00"
    latest_time = datetime.datetime.strptime(latest_time_string,"%Y-%m-%d %H:%M")
    if (request_date == now_date):
        if( now_date_time > earlist_time):
            earlist_time = now_date_time
    timelist.insert(0, earlist_time)
    timelist.append(latest_time)

    floor_number, room_number = get_room_name(room_name)
    i = 0
    while i < len(timelist):
        begin_time = timelist[i]
        end_time = timelist[i+1]
        i += 2

        begin_minute = begin_time.minute/60.0
        begin_hour = begin_time.hour + begin_minute
        end_minute = end_time.minute/60.0
        end_hour = end_time.hour + end_minute
        time_difference = end_hour - begin_hour

        if (time_difference >= request_hour):
            room_info = []
            room_info.append(floor_number)
            room_info.append(room_number)
            room_info.append(begin_time)
            room_info.append(end_time)
            room_info_list.append(room_info)


#解析会议室具体地址
def get_room_name(room_name):
    floor_number = ""
    room_number = ""
    try:
        floor_and_room = room_name.split("&")
        floor = floor_and_room[0]
        room = floor_and_room[-1]
        floor_number = floor.split("=")[-1]
        room_number = room.split("=")[-1]
    except Exception, e:
        log_error.append(e.message)

    #对楼层进行处理
    if (room_number == "15" or room_number == "20"):
        room_number = "培训教室"
    elif (room_number == "21"):
        room_number = "新会议室"
    elif (room_name == "floor=3&room=8"):
        room_number = "培训教室"
    else:
        room_number += "号会议室"
    return floor_dict[floor_number], room_number


def select_room_to_reserve(room_info_list,pointed_floor,request_date,period,nums):
    """
    二、选择符合用户条件的会议室selected_room_info
    1、按照时段，查找room_info_list
    2、本层楼没找到，则查看相邻从层楼会议室
    """
    if( period =="0"):
        earlist_time_string = request_date + " 09:30"
        latest_time_string = request_date + " 12:30"
    elif(period == "1"):
        earlist_time_string = request_date + " 13:30"
        latest_time_string = request_date + " 18:00"
    elif(period == "2"):
        earlist_time_string = request_date + " 19:00"
        latest_time_string = request_date + " 21:00"
    else:
        earlist_time_string = request_date + " 09:30"
        latest_time_string = request_date + " 21:00"

    earlist_time = datetime.datetime.strptime(earlist_time_string, "%Y-%m-%d %H:%M")
    latest_time = datetime.datetime.strptime(latest_time_string, "%Y-%m-%d %H:%M")

    if(latest_time < now_date_time):
        log_error.append("时间段选择有误")

    selected_room_info, find_room_flag = search_room_info_list(room_info_list,earlist_time,latest_time,nums)
    if(len(selected_room_info) == 0):
        search_room_result = (pointed_floor + "没有合适的会议室")
    elif ( selected_room_info[0] == pointed_floor):
        search_room_result = "找到指定楼层会议室"
    else:
        search_room_result = "没有找到指定楼层会议室"
    return selected_room_info,search_room_result


def search_room_info_list(room_info_list,earlist_time,latest_time,nums):
    global neighbor
    find_room_flag = 0
    selected_room_info = []

    floors_to_search = neighbor[pointed_floor]
    #根据楼层优先级顺序，挨个比较选择
    for floor in floors_to_search:
        #单个楼层中查找会议室
        for room_info in room_info_list:
            floor_number = room_info[0]
            room_number = re.sub("\D","",room_info[1])
            if(floor_number == floor and room_info[2] >= earlist_time and room_info[3] <= latest_time ):
                #大会议室
                if(nums == "1" and capity_dict[floor_number][room_number] > 15):
                    selected_room_info = room_info
                    find_room_flag = 1
                #小会议室 15人以内
                elif(nums == "0" and capity_dict[floor_number][room_number] <13):
                    selected_room_info = room_info
                    find_room_flag = 1
                break
        if (find_room_flag != 0):
            break
    return selected_room_info, find_room_flag


"""
三、实现预定功能
"""
def reserve_meeting_room(selected_room_info, request_hour,contact, note,user_msg):
    reserve_session = requests.session()

    floor_number = selected_room_info[0]
    room_name = selected_room_info[1]
    room_number  = re.sub("\D","",room_name)
    #获取会议室地址链接
    room_address = "floor=" + floor_dict_reverse[floor_number] + "&room=" + room_number

    begin_time_string = selected_room_info[2].strftime("%Y-%m-%d %H:%M") + ":00"
    hours = timedelta(hours=request_hour)
    end_time = selected_room_info[2] + hours
    end_time_string =end_time.strftime("%Y-%m-%d %H:%M") + ":00"

    next_url = "/hzroom/action/bookroom/?" + room_address
    reserve_url = "http://br.oa.netease.com/hzroom/action/addroom/"

    form_data = {
        "floor":floor_dict_reverse[floor_number],
        "room":room_number,
        "bdt":begin_time_string,
        "edt":end_time_string,
        "ext":contact,
        "remark":note + user_msg,
        "next_url":next_url
    }

    response = reserve_session.post(reserve_url, headers = br_header, data = form_data, cookies = cookies)

    err = json.loads(response.content)['err']
    if (err == 0):
        reserve_result = "预定成功"
    else:
        reserve_result = "预定失败"

    return reserve_result


#取消会议室
def concel_meeting_room(start_time, floor, room_number):
    concel_session = requests.session()

    url = "http://br.oa.netease.com/hzroom/action/my_bookroom/"
    my_bookroom = concel_session.get(url, cookies = cookies)
    soup = BeautifulSoup(my_bookroom.text, "lxml")
    checklists = soup.find_all("tr", {"class": "checklist"})

    if(len(checklists) == 0):
        print "没有预定的会议室!"
    else:
        for checklist in checklists:
            tds = checklist.find_all("td")
            btime = tds[0].string
            building = tds[2].string
            reserved_floor = building.split("栋")[0] + building.split("栋")[-1].split("楼")[0]
            room = tds[3].string.split("号")[0]
            if (reserved_floor == floor and btime == start_time and room == room_number):

                onclick = tds[-1].find("a")["onclick"]
                link = onclick.split("\"")[1]
                concel_url = "http://br.oa.netease.com" + link
                response = concel_session.get(concel_url, cookies = cookies, headers = br_header)
                err = json.loads(response.content)['err']
                if( err == 0):
                    print "删除预定成功"
                else:
                    print "提交数据出错"
                break
            else:
                continue


def search_and_reserve_meeting_room(job_id,user_name,pointed_floor,request_hour,request_date,period,TV_projector,
                                    telephone,person_num):
    errors = ""
    #检查用户参数是否正确
    hour, point_date, TV_projector_param, telephone_param, nums,user_msg ,period= \
        check_params(pointed_floor,request_hour,request_date,period,TV_projector,telephone,person_num,user_note)
    #多线程获取所有会议室room_info_list
    threads = []
    for rooms in all_rooms:
        t = threading.Thread(target=inquire_meeting_rooms ,args =
        (rooms, hour, point_date, TV_projector_param, telephone_param) )
        threads.append(t)
    for t in threads:
        t.setDaemon(True)
        t.start()
    for t in threads:
        t.join()

    note = user_name + " " + present_time + " 预定"
    #筛选符合期望的会议室
    selected_room_info, search_room_result = \
        select_room_to_reserve(room_info_list,pointed_floor,request_date,period,nums)
    #预定会议室
    if (len(selected_room_info) != 0):
        reserve_result = reserve_meeting_room(selected_room_info,hour, contact, note,user_msg)
        message = search_room_result + " " + reserve_result
    else:
        message = search_room_result

    #发送预定结果给服务器
    if(len(log_error) == 0):
        status = 1
    else:
        status = 2
        for err in log_error:
            errors += err
    is_over = 1

    result = {'user_job_id': job_id, 'message': message, 'status': status, 'is_over': is_over, 'error_log': errors}
    httpClient = None
    try:
        headers = {"Content-Type": "application/json; charset = UTF-8", "Accept": "application/json"}
        httpClient = httplib.HTTPConnection("10.242.109.29", 8183, timeout=30)
        httpClient.request("POST", "/ajax/open/result/inquery",
                           json.dumps(result, encoding = "utf-8", ensure_ascii=False), headers)
        response = httpClient.getresponse()
        # session = requests.session()
        # response = session.post("10.242.109.29/ajax/open/result/inquery",
        # data = json.dumps(result, encoding = "utf-8", ensure_ascii=False), headers = headers)
        print response.status
        print response.getheaders()
    except Exception, e:
        print e
    finally:
        if httpClient:
            httpClient.close()


if __name__ == "__main__":
    cookies = login()
    try:

        job_id = 11212   #调用传参
        request_hour = "1"  #必填
        request_date = "2017-01-22"  #必填
        TV_projector = "0"  #选填
        telephone = "0"     #选填
        pointed_floor = "B6"    #必填
        user_name = "hzsongjie1"    #系统传参
        period = "3"    #选填。0：上午，1下午，2：晚上，3：全天。
        user_note = "test"  #选填
        person_num = "0"    #必填。0:15人以内，1:15人以上
        contact = "123456"    #用户备注，选填
        search_and_reserve_meeting_room(job_id,user_name,pointed_floor,request_hour,request_date,period,TV_projector,
                                    telephone,person_num)
    except Exception, e:
        print e


