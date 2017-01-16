# -*- coding: utf-8 -*-
import threading
import sys
import time
import datetime
import requests
import httplib
import json
from bs4 import BeautifulSoup

reload(sys)
sys.setdefaultencoding("utf-8")

present_time = time.strftime('%Y-%m-%d %H:%M',time.localtime(time.time()))
now_date_time = datetime.datetime.strptime(present_time, "%Y-%m-%d %H:%M")
now_date = now_date_time.date()
now_time = now_date_time.time()
room_info_list = []
log_error = []


login_header = {'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8','Accept-Encoding':'gzip, deflate','Accept-Language':'zh-CN,zh;q=0.8,en;q=0.6','Host':'login.netease.com','Origin':'https://login.netease.com','User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
br_header = {'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8','Accept-Encoding':'gzip, deflate','Accept-Language':'zh-CN,zh;q=0.8,en;q=0.6','Host':'br.oa.netease.com','Origin':'https://br.oa.netease.com','User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

#所有可预定的会议室
A4_rooms = ['floor=104&room=1','floor=104&room=2','floor=104&room=5','floor=104&room=6','floor=104&room=9','floor=104&room=10','floor=104&room=13','floor=104&room=15']
B1_rooms = ['floor=1&room=1']
B3_rooms = ['floor=3&room=5','floor=3&room=7','floor=3&room=8']
B3W_rooms = ['floor=203w&room=10','floor=203w&room=13','floor=203w&room=20','floor=203w&room=21']
B4_rooms = ['floor=4&room=1','floor=4&room=4','floor=4&room=5','floor=4&room=8','floor=4&room=9','floor=4&room=13','floor=4&room=15']
B5_rooms = ['floor=5&room=1','floor=5&room=4','floor=5&room=5','floor=5&room=8','floor=5&room=9','floor=5&room=10', 'floor=5&room=11','floor=5&room=13','floor=5&room=15']
B6_rooms = ['floor=6&room=1','floor=6&room=5','floor=6&room=8','floor=6&room=9','floor=6&room=13']
B7_rooms = ['floor=7&room=15','floor=7&room=21']
B8_rooms = ['floor=8&room=3','floor=8&room=4','floor=8&room=7']
C2_rooms = ['floor=9&room=1','floor=9&room=2','floor=9&room=3','floor=9&room=4']
all_rooms = [A4_rooms,B1_rooms,B3_rooms,B3W_rooms,B4_rooms,B5_rooms,B6_rooms,B7_rooms,B8_rooms,C2_rooms]
floor_dict = {"104":"A4","1":"B1","203w":"B3西","3":"B3","4":"B4","5":"B5","6":"B6","7":"B7","8":"B8","9":"C2"}

#视频会议室，包括部分需要电话预定的会议室，下同
camera_rooms = ['floor=104&room=9','floor=4&room=5','floor=5&room=11','floor=6&room=9','floor=7&room=15','floor=8&room=3']
#投影仪会议室
projector_rooms = ['floor=203w&room=21','floor=3&room=5','floor=3&room=8','floor=4&room=15','floor=5&room=10','floor=5&room=11','floor=5&room=15','floor=7&room=21','floor=104&room=9','floor=104&room=15','floor=9&room=2','floor=9&room=3']
#电视会议室
TV_rooms = ['floor=203w&room=10','floor=203w&room=13','floor=203w&room=20','floor=3&room=7','floor=4&room=4','floor=4&room=5','floor=4&room=8','floor=4&room=9','floor=4&room=13','floor=5&room=1','floor=5&room=5','floor=5&room=8','floor=5&room=9','floor=5&room=11','floor=5&room=13','floor=5&room=15','floor=6&room=1','floor=6&room=5','floor=6&room=9','floor=6&room=13','floor=7&room=15','floor=8&room=3','floor=8&room=4','floor=8&room=7','floor=104&room=1','floor=104&room=2','floor=104&room=5','floor=104&room=6','floor=104&room=9','floor=104&room=10','floor=104&room=15','floor=9&room=1','floor=9&room=4']
#电话会议室
telephone_rooms = ['floor=203w&room=10','floor=203w&room=21','floor=3&room=5','floor=3&room=8','floor=5&room=1','floor=5&room=4','floor=5&room=5','floor=5&room=8','floor=5&room=9','floor=5&room=10','floor=5&room=11','floor=5&room=13','floor=6&room=1','floor=6&room=5','floor=6&room=8','floor=6&room=9','floor=6&room=13','floor=7&room=15','floor=8&room=3','floor=8&room=4', 'floor=8&room=7','floor=104&room=1','floor=104&room=2','floor=104&room=5','floor=104&room=6','floor=104&room=9','floor=104&room=10','floor=9&room=1','floor=9&room=2']


def login():
    url = "http://br.oa.netease.com/hzroom/"
    session = requests.Session()
    login_page = session.get(url, headers = login_header)
    post_data = {
        'authm':'corp',
        'trust_root':'http://br.oa.netease.com/hzroom/',
        'corpid':'hzsongjie1',
        'corppw':'xxx'
    }
    reponse_url = login_page.url
    try:
        content = session.post(reponse_url, data=post_data)
        cookies = session.cookies
        return cookies
    except Exception, e:
        log_error.append(e.message)


#处理单个会议室信息
def one_room_reserved(room_names, request_hour, date = now_date, TV = False, camera = False, projector = False, telephone = False ):
    session = requests.Session()
    for room_name in room_names:
        #判断是否含有满足条件的会议室
        has_TV = True
        has_camera = True
        has_projector = True
        has_telephone = True
        if (TV == True):
            has_TV = contains_meeting_room(room_name, TV_rooms)
        if (camera == True):
            has_camera = contains_meeting_room(room_name, camera_rooms)
        if (projector == True):
            has_projector = contains_meeting_room(room_name, projector_rooms)
        if (telephone == True):
            has_telephone = contains_meeting_room(room_name, telephone_rooms)

        if (has_TV and has_camera and has_projector and has_telephone):
            room_url = 'http://br.oa.netease.com/hzroom/action/bookroom/?' + room_name
            req = session.get(room_url, headers =br_header, cookies = cookies)
            soup = BeautifulSoup(req.text, 'lxml')
            checklists = soup.findAll('tr', {'class': 'checklist'})
            meeting_room_timetable(checklists, room_name, date, request_hour)


#找到所有预定时间，并将符合期望的加入到timelist中
def meeting_room_timetable(checklists,room_name, date, request_hour ):
    timelist = []
    flag = 0
    start_time = ""
    end_time = ""
    for checklist in checklists:
        try:
            start_time = checklist.find_all('td',{'width':'21%'})[0].string
            end_time = checklist.find_all('td',{'width':'21%'})[1].string
        except Exception, e:
            log_error.append(e.message)

        #过滤时间，保留与期望date符合的选项
        start_date_time = datetime.datetime.strptime(start_time,"%Y-%m-%d %H:%M")
        start_end_time = datetime.datetime.strptime(end_time,"%Y-%m-%d %H:%M")
        if (start_date_time.date() == date and start_date_time > now_date_time):
            timelist.append(start_date_time.time())
            timelist.append(start_end_time.time())
        try:
            if (start_date_time.date() > date):
                #若当天没有任何预定，则将整天时间都插入,定义一个flag,同样执行计算日期
                if(len(timelist) == 0):
                    flag = 1
                break
        except Exception, e:
            log_error.append(e.message)

    #根据timelist计算是否有满足条件的时间段
    if (len(timelist) > 1 or flag == 1):
        compute_time(room_name, timelist, date, request_hour)


#处理时间列表
def compute_time(room_name, timelist, date, request_hour):
    special_note = ""
    earlist_time = datetime.time(9, 30)
    latest_time = datetime.time(22, 00)
    if (date == now_date):
        if( now_time > earlist_time):
            earlist_time = now_time
    timelist.insert(0, earlist_time)
    timelist.append(latest_time)

    timelist_len = len(timelist)
    floor_number, room_number = get_room_name(room_name)
    i = 0
    while i < timelist_len:
        begin_time = timelist[i]
        end_time = timelist[i+1]
        begin_time_string = begin_time.strftime("%H:%M")
        end_time_string = end_time.strftime("%H:%M")
        i += 2
        beigin_minute = begin_time.minute/60.0
        beagin_hour = begin_time.hour + beigin_minute
        end_minute = end_time.minute/60.0
        end_hour = end_time.hour + end_minute
        time_difference = end_hour - beagin_hour

        if (time_difference >= request_hour):
            if(floor_number == "B5"):
                special_note = "(只接受在线游戏事业部(杭州)员工预订)"
            elif (floor_number == "B8"):
                special_note = "(只接受在线游戏事业部(杭州)及雷火工作室员工预订)"
            elif (floor_number == "B3西"):
                special_note = "(只接受运营中心员工预订)"
            elif (room_name == "floor=104&room=1" or room_name == "floor=1&room=1" or floor_number == "C2"):
                special_note = "(预订请联系前台，电话：20000)"
            room_message = floor_number + "楼" + room_number + "可预定时间：" + begin_time_string + "--" + end_time_string + " " + special_note
            room_info_list.append(room_message)


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
    elif (room_name == "floor=9&room=1"):
        room_number = "VIP会议室2"
    elif (room_name == "floor=9&room=2"):
        room_number = "VIP会议室"
    elif (room_name == "floor=9&room=3"):
        room_number = "大培训教室"
    elif (room_name == "floor=9&room=4"):
        room_number = "视频会议室"
    else:
        room_number += "号会议室"
    return floor_dict[floor_number], room_number


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

def do_reserved_meeting_room(job_id,request_hour,date,TV,camera,projector,telephone,pointed_floor):
    errors = ""
    room_message = ""
    hour = 0
    point_date = now_date
    TV_para = False
    camera_para = False
    projector_para = False
    telephone_para = False
    try:
        hour = int(request_hour)
        if (hour <= 0):
            log_error.append("时间太短")
        if ( hour > 12):
            log_error.append("时间太长")
    except Exception, e:
        log_error.append("输入的时长不是数字")
        log_error.append(e.message)

    if (date == "0"):
        point_date = now_date
    else:
        try:
            point_date = datetime.datetime.strptime(date,'%Y-%m-%d').date()
            if (point_date < now_date):
                log_error.append("输入日期不正确！")
        except Exception,e:
            log_error.append("输入日期格式不正确！")
            log_error.append(e.message)

    if( TV == "0"):
        TV_para = False
    elif (TV == "1"):
        TV_para = True
    else:
        log_error.append("电视参数不正确")

    if( camera == "0"):
        camera_para = False
    elif (camera == "1"):
        camera_para = True
    else:
        log_error.append("视频参数不正确")

    if( projector == "0"):
        projector_para = False
    elif (projector == "1"):
        projector_para = True
    else:
        log_error.append("投影仪参数不正确")

    if( telephone == "0"):
        telephone_para = False
    elif (telephone == "1"):
        telephone_para = True
    else:
        log_error.append("电话参数不正确")

    threads = []
    if (pointed_floor == "0"):
        for rooms in all_rooms:
            t = threading.Thread(target=one_room_reserved ,args = (rooms, hour, point_date, TV_para, camera_para, projector_para, telephone_para) )
            threads.append(t)
        for t in threads:
            t.setDaemon(True)
            t.start()
        for t in threads:
            t.join()
    else:
        floor_roooms_dict = {"A4":A4_rooms,"B1":B1_rooms,"B3":B3_rooms,"B3W":B3W_rooms,"B4":B4_rooms,"B5":B5_rooms,"B6":B6_rooms,"B7":B7_rooms,"B8":B8_rooms,"C2":C2_rooms}
        if (floor_roooms_dict.has_key(pointed_floor)):
            for rooms in floor_roooms_dict[pointed_floor]:
                t = threading.Thread(target=one_room_reserved ,args = (rooms, hour, point_date, TV_para, camera_para, projector_para, telephone_para) )
                threads.append(t)
            for t in threads:
                t.setDaemon(True)
                t.start()
            for t in threads:
                t.join()
        else:
            log_error.append("楼层参数不正确，请重新输入")

    room_info_list.sort()

    if(len(room_info_list) == 0):
        room_message = "没有找到合适的会议室"
    else:
        for message in room_info_list:
            room_message += message
            room_message += "\n"

    if(len(log_error) == 0):
        status = 1
    else:
        status = 2
        for err in log_error:
            errors += err
    is_over = 1

    result = {'user_job_id': job_id, 'message': room_message, 'status': status, 'is_over': is_over, 'error_log': errors}
    httpClient = None
    try:
        headers = {"Content-Type": "application/json; charset = UTF-8", "Accept": "application/json"}
        httpClient = httplib.HTTPConnection("10.242.109.29", 8183, timeout=30)
        httpClient.request("POST", "/ajax/open/result/record/meetingroom", json.dumps(result, encoding = "utf-8", ensure_ascii=False), headers)
        response = httpClient.getresponse()
        print response.status
        print response.getheaders()
    except Exception, e:
        print e
    finally:
        if httpClient:
            httpClient.close()

"""
job_id:系统参数，必填。
reques_hour:数字字符串，定义大于0小于12。必填。
date：日期，格式为"2017-01-06"。若不传参，默认为当天。选填
TV,camera,projeator,telephone:"0"表示不选择，"1"表示选择。默认为0.选填。
"""
if __name__ == "__main__":
    cookies = login()
    try:
        # job_id = sys.argv[1]
        # request_hour = sys.argv[2]
        # date = sys.argv[3]
        # TV = sys.argv[4]
        # camera = sys.argv[5]
        # projector = sys.argv[6]
        # telephone = sys.argv[7]
        job_id = 11212
        request_hour = "1"
        date = "2017-01-16"
        TV = "0"
        camera = "0"
        projector = "0"
        telephone = "0"
        pointed_floor = "0"

        do_reserved_meeting_room(job_id,request_hour,date,TV,camera,projector,telephone,pointed_floor)
    except Exception, e:
        print e
        print ("系统参数调用有误")


