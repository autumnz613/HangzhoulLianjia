# -*- coding: utf-8 -*-
import threading
import sys
import time
import datetime
import requests
from bs4 import BeautifulSoup

reload(sys)
sys.setdefaultencoding("utf-8")

present_time = time.strftime('%Y-%m-%d %H:%M',time.localtime(time.time()))
now_date_time = datetime.datetime.strptime(present_time, "%Y-%m-%d %H:%M")
now_date = now_date_time.date()
now_time = now_date_time.time()
floor_dict = {"104":"A4","1":"B1","203w":"B3西","3":"B3","4":"B4","5":"B5","6":"B6","7":"B7","8":"B8","9":"C2"}
floor_dict_reverse = {"A4":"104", "B1":"1", "B3W":"203w", "B3":"3","B4":"4","B5":"5","B6":"6","B7":"7","B8":"8","C2":"9"}
room_info_list = []

login_header = {'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding':'gzip, deflate','Accept-Language':'zh-CN,zh;q=0.8,en;q=0.6','Host':'login.netease.com',
                'Origin':'https://login.netease.com','User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 '
                                                                  '(KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

br_header = {'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
             'Accept-Encoding':'gzip, deflate','Accept-Language':'zh-CN,zh;q=0.8,en;q=0.6','Host':'br.oa.netease.com',
             'cookie':'hzroomssionid=0e36dc8fc5bc216e6d66b71b5afc8a25','Origin':'https://br.oa.netease.com',
             'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

#所有可预定的会议室
a4_rooms = ['floor=104&room=1','floor=104&room=2','floor=104&room=5','floor=104&room=6','floor=104&room=9',
            'floor=104&room=10','floor=104&room=13','floor=104&room=15']
b1_room = ['floor=1&room=1']
b3_rooms = ['floor=3&room=5','floor=3&room=7','floor=3&room=8']
b3w_rooms = ['floor=203w&room=10','floor=203w&room=13','floor=203w&room=20','floor=203w&room=21']
b4_rooms = ['floor=4&room=1','floor=4&room=4','floor=4&room=5','floor=4&room=8','floor=4&room=9','floor=4&room=13',
            'floor=4&room=15']
b5_rooms = ['floor=5&room=1','floor=5&room=4','floor=5&room=5','floor=5&room=8','floor=5&room=9','floor=5&room=10',
            'floor=5&room=11','floor=5&room=13','floor=5&room=15']
b6_rooms = ['floor=6&room=1','floor=6&room=5','floor=6&room=8','floor=6&room=9','floor=6&room=13']
b7_rooms = ['floor=7&room=15','floor=7&room=21']
b8_rooms = ['floor=8&room=3','floor=8&room=4','floor=8&room=7']
c2_rooms = ['floor=9&room=1','floor=9&room=2','floor=9&room=3','floor=9&room=4']

all_rooms = [a4_rooms,b1_room,b3w_rooms,b3_rooms,b4_rooms,b5_rooms,b6_rooms,b7_rooms,b8_rooms,c2_rooms]

#视频会议室，包括部分需要电话预定的会议室，下同
camera_rooms = ['floor=104&room=9','floor=4&room=5','floor=5&room=11','floor=6&room=9','floor=7&room=15','floor=8&room=3']
#投影仪会议室
projector_rooms = ['floor=203w&room=21','floor=3&room=5','floor=3&room=8','floor=4&room=15','floor=5&room=10',
                   'floor=5&room=11','floor=5&room=15','floor=7&room=21','floor=104&room=9','floor=104&room=15',
                   'floor=9&room=2','floor=9&room=3']
#电视会议室
TV_rooms = ['floor=203w&room=10','floor=203w&room=13','floor=203w&room=20','floor=3&room=7','floor=4&room=4',
            'floor=4&room=5','floor=4&room=8','floor=4&room=9','floor=4&room=13','floor=5&room=1','floor=5&room=5',
            'floor=5&room=8','floor=5&room=9','floor=5&room=11','floor=5&room=13','floor=5&room=15','floor=6&room=1',
            'floor=6&room=5','floor=6&room=9','floor=6&room=13','floor=7&room=15','floor=8&room=3','floor=8&room=4',
            'floor=8&room=7','floor=104&room=1','floor=104&room=2','floor=104&room=5','floor=104&room=6',
            'floor=104&room=9','floor=104&room=10','floor=104&room=15','floor=9&room=1','floor=9&room=4']
#电话会议室
telephone_rooms = ['floor=203w&room=10','floor=203w&room=21','floor=3&room=5','floor=3&room=8','floor=5&room=1',
                   'floor=5&room=4','floor=5&room=5','floor=5&room=8','floor=5&room=9','floor=5&room=10',
                   'floor=5&room=11','floor=5&room=13','floor=6&room=1','floor=6&room=5','floor=6&room=8',
                   'floor=6&room=9','floor=6&room=13','floor=7&room=15','floor=8&room=3','floor=8&room=4',
                   'floor=8&room=7','floor=104&room=1','floor=104&room=2','floor=104&room=5','floor=104&room=6',
                   'floor=104&room=9','floor=104&room=10','floor=9&room=1','floor=9&room=2']

def login(name, password):
    url1 = "http://br.oa.netease.com/hzroom/"
    session = requests.Session()
    login_page = session.get(url1, headers = login_header)
    post_data = {
        'authm':'corp',
        'trust_root':'http://br.oa.netease.com/hzroom/',
        'corpid':name,
        'corppw':password
    }
    reponse_url = login_page.url
    content = session.post(reponse_url, data=post_data)
    cookies = session.cookies
    return cookies

"""
爬取单个会议室的所有预定情况
输入预定日期，要求时长，默认日期为当天
"""
def one_room_reserved(room_names, request_hour, date = now_date, TV = False, camera = False,
                      projector = False, telephone = False ):
    session = requests.Session()
    # print content.text
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
            meeting_room_timetable(checklists,room_name, date, request_hour)


def meeting_room_timetable(checklists,room_name, date, request_hour ):
    timelist = []
    flag = 0
    for checklist in checklists:
        start_time = checklist.find_all('td',{'width':'21%'})[0].string
        end_time = checklist.find_all('td',{'width':'21%'})[1].string
        #过滤时间，保留与期望date符合的选项
        start_date_time = datetime.datetime.strptime(start_time,"%Y-%m-%d %H:%M")
        start_end_time = datetime.datetime.strptime(end_time,"%Y-%m-%d %H:%M")
        if (start_date_time.date() == date and start_date_time > now_date_time):
            timelist.append(start_date_time.time())
            timelist.append(start_end_time.time())
        if (start_date_time.date() > date):
            #若当天没有任何预定，则将整天时间都插入,定义一个flag,同样执行计算日期
            if(len(timelist) == 0):
                flag = 1
            break
            #根据timelist计算是否有满足条件的时间段
    if (len(timelist) > 1 or flag == 1):
        compute_time(room_name, timelist, date, request_hour)

"""
计算两个会议之间是时间差
时间列表中都是期望的日期
时间列表中所有元素均为datetime.time
设定一天最早时间为9点半，最晚时间为22点,插入头尾
"""
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
        time_difference = compute_time_difference(begin_time,end_time)
        if (time_difference >= request_hour):
            if(floor_number == "B5"):
                special_note = "(只接受在线游戏事业部(杭州)员工预订)"
            elif (floor_number == "B8"):
                special_note = "(只接受在线游戏事业部(杭州)及雷火工作室员工预订)"
            elif (floor_number == "B3西"):
                special_note = "(只接受运营中心员工预订)"
            elif (room_name == "floor=104&room=1" or floor_number == "C2"):
                special_note = "(预订请联系前台，电话：20000)"
            print "%s楼%s 可用时间段：%s -- %s     %s" % (floor_number, room_number, begin_time_string,
                                                   end_time_string, special_note)
            room_info = []
            room_info.append(floor_number)
            room_info.append(room_number)
            room_info.append(begin_time_string)
            room_info.append(end_time_string)
            room_info.append(special_note)
            room_info_list.append(room_info)

        i += 2

def compute_time_difference(begin_time,end_time):

    beigin_minute = begin_time.minute/60.0
    beagin_hour = begin_time.hour + beigin_minute
    end_minute = end_time.minute/60.0
    end_hour = end_time.hour + end_minute
    time_difference = end_hour - beagin_hour
    return time_difference

#解析会议室具体地址
def get_room_name(room_name):
    floor_and_room = room_name.split("&")
    floor = floor_and_room[0]
    room = floor_and_room[-1]
    floor_number = floor.split("=")[-1]
    room_number = room.split("=")[-1]

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

"""
实现预定功能
根据给定的时间以及房间号进行预定
暂不包括会议室以及培训教室等
"""
def booking_meeting_room(floor_number, room_number, book_date, book_btime, book_etime, telephone, note):

    book_session = requests.session()

    floor, room_address = get_room_address(floor_number, room_number)
    book_begin = book_date + " " + book_btime + ":00"
    book_end = book_date + " " + book_etime + ":00"
    next_url = "/hzroom/action/bookroom/?" + room_address
    book_url = "http://br.oa.netease.com/hzroom/action/addroom/"

    form_date = {
        "floor":floor,
        "room":room_number,
        "bdt":book_begin,
        "edt":book_end,
        "ext":telephone,
        "remark":note,
        "next_url":next_url
    }
    response = book_session.post(book_url, headers = br_header, data = form_date, cookies = cookies)

    if (response.status_code == 200):
        print "预订成功"
    else:
        print "Error"

def get_room_address(floor_number, room_number):

    floor = floor_dict_reverse[floor_number]
    room_address = "floor=" + floor + "&room=" + room_number
    return floor, room_address

"""
取消会议室
"""
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
                result = concel_session.get(concel_url, cookies = cookies, headers = br_header)
                if( result.status_code == 200):
                    print "删除预定成功"
                else:
                    print "提交数据出错"
                break
            else:
                continue


def do_reserved_meeting_room():
    request_hour = 1
    date = "2017-01-13"
    point_date = datetime.datetime.strptime(date,'%Y-%m-%d').date()
    TV = False
    camera = False
    projector = False
    telephone = False
    threads = []
    for room in all_rooms:
        t = threading.Thread(target=one_room_reserved ,args = (room, request_hour, point_date, TV, camera, projector, telephone) )
        threads.append(t)
    for t in threads:
        t.setDaemon(True)
        t.start()
    for t in threads:
        t.join()

def do_booking_meeting_room():
    floor_number = "B7"
    room_number = "15"
    booking_date = "2017-01-14"
    booking_btime = "12:00"
    booking_etime = "14:00"
    telephone = "12345"
    note = "test test"
    booking_meeting_room(floor_number, room_number, booking_date, booking_btime, booking_etime, telephone, note)

def do_concel_meeting_room():
    start_time = "2017-01-14 20:00"
    floor = "B6"
    room_number = "5"
    concel_meeting_room(start_time, floor, room_number)

if __name__ == "__main__":
    start = time.clock()
    name = "hzsongjie1"
    password = "xxx"
    cookies = login(name, password)
    do_reserved_meeting_room()
    for room_info in room_info_list:
        print  room_info
    # do_booking_meeting_room()
    # do_concel_meeting_room()
    end = time.clock()
    print "总共用时: %f s" % (end - start)

