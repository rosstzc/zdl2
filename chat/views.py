# -*- coding: utf-8 -*-
# from __future__ import unicode_literals


from datetime import datetime

from django.http import HttpResponse, HttpRequest, QueryDict
from django.http import HttpResponseRedirect
from django.http import HttpResponseServerError
from django.urls import reverse
from django.views import View

from django.shortcuts import render
from django.views.generic import View  #通用类
from models import *
from django.db.models import Q

from django.views.decorators.csrf import csrf_exempt


from view_func import *    #公共方法
# from apscheduler.schedulers.background import BackgroundScheduler
#
# from apscheduler.schedulers.blocking import BlockingScheduler

from django.template.context import RequestContext
# Create your views here.
# import leancloud
# leancloud.init("TpiAufPcAVp2cR1GRpJQIX5X-gzGzoHsz", "NSXmOEgBlq8Aghgh7LhQAUda")
# from leancloud import Object
# from leancloud import Query
# from leancloud.errors import LeanCloudError

import base64,os
import logging,random
import json
import  datetime, time

logging.basicConfig(level=logging.DEBUG)

from django.template.loader import get_template

import  platform

import sys
reload(sys)
sys.setdefaultencoding('utf-8')


#把两个字符时间修改日期，然后比较
def dayTimeCompare(time1, time2):
    if time1 == '' or time1 == None: #没有时间就表示最近没有提醒
        return '0'

    if GetTimeString(time1) == GetTimeString(time2):
        return '1'
    else:
        return '0'

def GetTimeString(time):
    #先把字符转为时间，然后转为某时间格式字符
    date_time = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
    time_string = datetime.datetime.strftime(date_time, '%Y-%m-%d')
    return time_string


# 首页
def index(req):
    #GET  从api/chat_state 获取数据，然后返回到chat.html
    # currentUser = leancloud.User.get_current()
    # todoo, 触发配对,日后也是要异步操作
    if req.method == 'POST':

        return

    #get方法
    else:
        #微信触发带登录特性的页面
        W_NAME = req.GET.get('W_NAME')
        if W_NAME:
            my = User.objects.get(W_NAME=W_NAME)
            url = GetSiteUrl(req)
            response = HttpResponseRedirect(url)
            response.set_cookie('UID', my.id, max_age=10000000000)
            response.set_cookie('W_NAME', W_NAME, max_age=10000000000)
            return response

        uid = req.COOKIES.get('UID')
        my = User.objects.get(id=uid)


        #查询time_login_today是否未今天，如果是就不给今天积分，如果不是就给积分，并且把时间改为今天时间
        # time = my.time_login_today
        # date_time = datetime.datetime.strptime(time,'%Y-%m-%d %H:%M:%S')
        # time_string = datetime.datetime.strftime(date_time,'%Y-%m-%d')
        # now = datetime.datetime.now()
        # DATETIME_FORMAT = '%Y-%m-%d'
        # today_string = now.strftime(DATETIME_FORMAT)

        today_string = GetTimeString(my.time_login_today)
        now_string = GetTimeString(GetTimeNow())
        scoreText = ''
        #赠送积分
        if  now_string != today_string:
            temp = get_score_today(my)
            my = temp[0]
            my.remind_key = '0'  #user表提醒状态，用户与48小时服务提醒
            scoreText = temp[1]  #第一次登录的积分提示文本

        #刷新登录数据
        my.time_login_today = GetTimeNow()
        my.save()

        #发出邀请
        action = req.GET.get('action')
        sex_match = req.COOKIES.get('sex_match')
        #下面应该执行随机聊天的，目前已不用了
        if action == 'gochat':
            if my.state == '3':   #在聊中
                response = HttpResponseRedirect(reverse('index'))
                return response
            else:
                my.state = '2'
                my.time_gochat = GetTimeNow()  #写入一个最近匹配时间，这样就不用一个自动脚本来刷新用户状态；
                my.save()
                start = OnlineTime(0.5)
                #到user表找状态"匹配中"的人；
                user = User.objects.filter(state='2',time_gochat__gt=start).exclude(id=uid)

                #选择匹配异性进入如下模式, 如果自己有性别匹配异性，如果没有就随便匹配
                if sex_match == '1' :
                    if my.sex == '0':
                        user = user.filter(sex='1')
                    if my.sex == '1':
                        user = user.filter(sex='0')


                if user.count() > 0:
                    #12小时内匹配过的不重复匹配
                    start = OnlineTime(8)
                    chatRecord = Chat.objects.select_related().filter(Q(rid=uid) | Q(sid=uid), close='1',time__gt=start)

                    #把user查询结果与聊天记录表校验：先找到所有""用户，然后逐个到最近对话列表里检查，取没有出现的第一个
                    key = 0 #是否有
                    x = 0
                    user_chat = user[0]
                    for i in user:
                        k = 0
                        for j in chatRecord:
                            if i.id == j.sid_id or i.id == j.rid_id:
                                k = k + 1
                        #如果最近没有聊过,就取这个
                        # if k == 0  or k == 1:   # 2次
                        if k == 0 :  # 1次
                            key = 1
                            user_chat = user[x]
                            break
                        x = x + 1

                    #匹配到
                    if key == 1:
                        # getMatchLogic(my,user_chat,req)
                        randomMatchLogic(my,user_chat)

                        # time = GetTimeNow()
                        # chat = Chat(sid_id=user_chat.id, rid_id=uid, mode='1', time=time, close='0')
                        # chat.save()
                        #
                        # my.state = '3'
                        # if int(my.score_today) > 0:
                        #     my.score_today = str(int(my.score_today) - 1)
                        # else:
                        #     my.score_forever = str(int(my.score_forever) - 1)
                        # my.score_sum = str(int(my.score_sum) + 1)
                        # my.save()
                        #
                        # user_chat.state = '3'
                        # if int(user_chat.score_today) == 0:
                        #     user_chat.score_forever = str(int(user_chat.score_forever) - 1)
                        # else:
                        #     user_chat.score_today = str(int(user_chat.score_today) - 1)
                        # user_chat.score_sum = str(int(user_chat.score_sum) + 1)
                        # user_chat.save()
                        #
                        # #线上环境
                        # if 'centos' in platform.platform():
                        #     #給双方发微信推送告诉配对成功
                        #     token = GetAccessToken()
                        #     resMsgA = '【系统消息】刚刚为你匹配到 '+ user_chat.name + '，回复消息打个招呼，聊天请注意文明用语哦！ '
                        #     # resMsgA = '已匹配到 '+ user_chat.name + '，你们可以开始对话 :> (' + link + '的主页)'
                        #     PostMessge(token, str(PostText(my.W_NAME, resMsgA)))
                        #
                        #     resMsgA = '[' + user_chat.name + ']：您好 :>'
                        #     PostMessge(token, str(PostText(my.W_NAME, resMsgA)))
                        #
                        #
                        #     link = getUserLink(req, my)
                        #     resMsgB = '【系统消息】已匹配到 '+ my.name + '，回复消息打个招呼吧 :>  '
                        #     # resMsgB = '已匹配到 '+ my.name + '，回复消息打个招呼吧 :> \n(' + link + '的主页)'
                        #     PostMessge(token, str(PostText(user_chat.W_NAME, resMsgB)))
                        #
                        #     resMsgB = '[' + my.name + ']：您好 :>'
                        #     PostMessge(token, str(PostText(user_chat.W_NAME, resMsgB)))

                        response = HttpResponseRedirect(reverse('index'))
                        return response


        #退出聊天
        if action == 'leave':
            if my.state == '3':
                chat = Chat.objects.select_related().filter(Q(rid=uid) | Q(sid=uid), close='0')
                #异常处理
                if chat.count() == 0:
                    my.state = '1'
                    my.save()
                    return HttpResponseRedirect(reverse('index'))

                user_chat = GetUserChat(chat[0],uid)
                my.state = '1'
                my.save()
                user_chat.state = '1'
                user_chat.save()
                chat.update(close='1') #一般只有1个，考虑到容错，就全部更新
                if 'centos' in platform.platform():
                    token = GetAccessToken()
                    #todoo 给双方发推送告诉已退出聊天
                    resMsgA = '【系统消息】你已退出聊天'
                    PostMessge(token, str(PostText(my.W_NAME, resMsgA)))

                    resMsgB = '【系统消息】' + my.name + ' 已退出聊天'
                    PostMessge(token, str(PostText(user_chat.W_NAME, resMsgB)))

            if my.state == '2':
                my.state = '1'
                my.save()
            response = HttpResponseRedirect(reverse('index'))
            return response


        #如果状态是2，并且time_gochat时间超过30分钟，让状态回复1
        my = updateState(my)
        # if my.state == '2':
        #     start = OnlineTime(0.5)
        #     if my.time_gochat != None and my.time_gochat != '':
        #         time_gochat = my.time_gochat
        #         if time_gochat < start:
        #             my.state = '1'
        #             my.save()
        if my.introduction == '':
            my.introduction = "这家伙很懒，什么都没写"
        my.save()


        # 如果状态1或2，可以看到最近活跃用户,最近48小时在线用户
        user_active = '0'


        # if my.state == '1' or my.state == '2':
        #展示活跃用户
        # user_active = activeUsers(my, 3)

        #处理推荐用户：女生随机推荐3个男生；男生随机推荐15个女生.. "再来一个"
        temp = GetUserRecommend(my,action)
        user_re = temp[1]
        key_re = temp[0]   #等于"0"时表示第一次更新, 用在前端做判断
        # 点『再来一个』
        if action == 'addMore':
            temp = recommendMore(my, 1)
            return HttpResponseRedirect(reverse('index'))



        #如果状态是"聊天中"，
        url_info = ''
        user_chat = ''
        if my.state == '3':
            chat = Chat.objects.select_related().filter(Q(rid=uid) | Q(sid=uid), close='0')
            user_chat = ''
            if chat.count() > 0:
                user_chat = GetUserChat(chat[0],uid)
                url_info = GetSiteUrl(req) +'user/' + str(user_chat.id)

            # content = {'my': my, 'user_chat':user_chat, 'state':'3'}
            # response = render(req, 'chat/chat.html', content)
            # return response
        nine = check21PM(req)
        score_aviable = int(my.score_today) + int(my.score_forever)
        url_site = GetSiteUrl(req)
        url_gochat = GetSiteUrl(req) + '?action=gochat'
        url_leave = GetSiteUrl(req) + '?action=leave'
        unreadSum = getUnreadSum(req)
        url_daqi = GetSiteUrl(req) + 'invite?action=daqi&uid=' + str(uid)
        content = {'my': my, 'user_chat':user_chat, 'state':my.state,
                   'url_gochat':url_gochat, 'url_leave':url_leave, 'url_info':url_info, 'url_site':url_site,
                   'score_available':score_aviable, 'unreadSum':unreadSum, 'user_active':user_active,
                    'url_daqi':url_daqi, 'nine':nine, 'user_re':user_re, 'key_re':key_re, 'scoreText':scoreText}
        response = render(req, 'chat/chat.html', content)
        # 非9点后就写cookie
        # if action == 'gochat' and nine == 0:
        #     response.set_cookie('nine', nine, max_age=3600)
        return response




    # #todoo，
    #  1） 用户发起配对时，修改state和记录触发时间（30s有效）。
    #  2）如果配对成功，修改state。
    # 3）如果退出，修改state。
    #  4）发起匹配时，到user表查询状态为"匹配中"的人
    #5）从查询数据中，除去那些今天已匹配过的人
    #6）选择1个，到ChatRecord表写入一条记录表示配对成功

        # todoo 退出聊天/匹配/离开


    #当前方案：本方法内调用获取登录后user数据，然后python渲染内容，包括写cookie
    #API方案: 前端js调用api获取数据，然后js渲染内容


def updateState(my):
    if my.state == '2':
        start = OnlineTime(0.5)
        #如果半小时未匹配上，就把状态修改空闲
        if my.time_gochat != None and my.time_gochat != '':
            time_gochat = my.time_gochat
            if time_gochat < start:
                my.state = '1'
                my.save()
    return my


def GetUserRecommend(my, action):
    # 先查询今天是否已经推荐，都是48小时内用户
    today = GetTimeNow()
    time = my.time_user_recommand

    key_re_today = '0'
    #避免数据错误
    if time == '' or time == None :
        key_re_today = '0'
    else:
        if GetTimeString(time) == GetTimeString(today):
            key_re_today = '1'

    if key_re_today == '0': #每天只会执行一次
        user = UserRecommend.objects.filter(uid=my)
        user.delete()
        my.time_user_recommand = GetTimeNow()
        my.save()

        # 首次推荐
        recomendFrist(my, 3)
    user = UserRecommend.objects.filter(uid=my).order_by('-id')
    return [key_re_today, user]



#首次推荐
def recomendFrist(my,count):
    if my.sex == '0':
        sex = '1'
    else:
        sex= '0' #女
    start = OnlineTime(48)
    user = User.objects.filter(time_login_today__gt=start, sex=sex, state='1').order_by('?')[:count]
    # 如果不够3个人，那么就到48小时前用户补充
    if user.count() < count:
        userArray = []
        temp = count - user.count()
        start = OnlineTime(720)  # 1个月内
        addUser = User.objects.filter(time_login_today__gt=start, sex=sex, state='1').order_by('?')[:temp]
        for i in user:
            userArray.append(i)
        for i in addUser:
            userArray.append(i)
        user = userArray  # 补全3个人

    # 写入recommend表
    for i in user:
        user_re = UserRecommend(uid=my, rid=i, time=GetTimeNow())
        user_re.save()


#再来几个逻辑
def recommendMore(my,count):
    user = UserRecommend.objects.filter(uid=my)
    queryList = Q()
    for i in user:
        queryList = queryList | Q(id=i.rid_id)

    #处理性别
    if my.sex == '0':
        sex = '1'
    else:
        sex= '0'
    # 先取48小时内，并且不在对话状态的
    start = OnlineTime(48)
    tempUser = User.objects.filter(sex=sex, time_login_today__gt=start, state='1').exclude(queryList).order_by('?')[:count]
    if tempUser.count() == 0:
        start = OnlineTime(720)  # 1个月内
        tempUser = User.objects.filter(sex=sex, time_login_today__gt=start, state='1').exclude(queryList).order_by(
            '?')[:count]
    if tempUser.count() > 0:
        for i in tempUser:
            user_re = UserRecommend(uid=my, rid_id=i.id, time=GetTimeNow())
            user_re.save()
            scoreSpend(my)  #扣减积分
    user = UserRecommend.objects.filter(uid=my).order_by('-id')
    return [tempUser.count(),user]






#消费积分
def scoreSpend(user):
    my = user
    if (int(my.score_today) + int(my.score_forever)) <= 0:
        return 0

    if int(my.score_today) > 0:
        my.score_today = str(int(my.score_today) - 1)
    else:
        my.score_forever = str(int(my.score_forever) - 1)
    my.score_sum = str(int(my.score_sum) + 1)
    my.save()
    return  my


def scoreValidCheck(user):
    if user.score_forever == '' or user.score_forever == None:
        user.score_forever = '10'
    if user.score_today == '' or  user.score_today == None:
        user.score_today = '10'
    if user.score_sum == '' or user.score_sum == None:
        user.score_sum = '10'
    return user

#获得积分
def scoreIncome(user):
    #异常处理，避免手工添加的数据出错
    user = scoreValidCheck(user)
    user.score_forever = str(int(user.score_forever) + 1)
    user.score_sum = str(int(user.score_sum) + 1)
    user.save()
    return user



#把配对逻辑提取岀来
# def getMatchLogic(my, user_chat):
#     uid = my.id
#     time = GetTimeNow()
#     chat = Chat(sid_id=user_chat.id, rid_id=uid, mode='1', time=time, close='0')
#     chat.save()
#
#     my.state = '3'
#     if int(my.score_today) > 0:
#         my.score_today = str(int(my.score_today) - 1)
#     else:
#         my.score_forever = str(int(my.score_forever) - 1)
#     my.score_sum = str(int(my.score_sum) + 1)
#     my.save()
#
#     user_chat.state = '3'
#     if int(user_chat.score_today) == 0:
#         user_chat.score_forever = str(int(user_chat.score_forever) - 1)
#     else:
#         user_chat.score_today = str(int(user_chat.score_today) - 1)
#     user_chat.score_sum = str(int(user_chat.score_sum) + 1)
#     user_chat.save()
#
#     # 线上环境
#     if 'centos' in platform.platform():
#         # 給双方发微信推送告诉配对成功
#         token = GetAccessToken()
#         resMsgA = '【系统消息】刚刚为你匹配到 ' + user_chat.name + '，回复消息打个招呼，聊天请注意文明用语哦！ '
#         # resMsgA = '已匹配到 '+ user_chat.name + '，你们可以开始对话 :> (' + link + '的主页)'
#         PostMessge(token, str(PostText(my.W_NAME, resMsgA)))
#
#         resMsgA = '[' + user_chat.name + ']：您好 :>'
#         PostMessge(token, str(PostText(my.W_NAME, resMsgA)))
#
#         resMsgB = '【系统消息】已匹配到 ' + my.name + '，回复消息打个招呼吧 :>  '
#         # resMsgB = '已匹配到 '+ my.name + '，回复消息打个招呼吧 :> \n(' + link + '的主页)'
#         PostMessge(token, str(PostText(user_chat.W_NAME, resMsgB)))
#
#         resMsgB = '[' + my.name + ']：您好 :>'
#         PostMessge(token, str(PostText(user_chat.W_NAME, resMsgB)))



def girlMatchLogic(my,user_chat):
    uid = my.id
    time = GetTimeNow()
    chat = Chat(sid_id=uid, rid_id=user_chat.id, mode='2', time=time, time_end=time, close='0')  #mode=2，女方邀请的配对
    # chat = Chat(sid_id=user_chat.id, rid_id=uid, mode='2', time=time, time_end=time, close='0')  #mode=2，女方邀请的配对
    chat.save()

    my.state = '3'
    my.save()
    # my = scoreSpend(my)   不扣减积分

    user_chat.state = '3'
    user_chat.save()

    # 线上环境
    if 'centos' in platform.platform():
        # 給双方发微信推送告诉配对成功
        token = GetAccessToken()
        resMsgA = '【系统消息】已配对 [' + user_chat.name + ']（已通知TA），请等待他回应。若对方5分钟内不回应，你可以离开再选其他人 '
        # resMsgA = '已匹配到 '+ user_chat.name + '，你们可以开始对话 :> (' + link + '的主页)'
        PostMessge(token, str(PostText(my.W_NAME, resMsgA)))

        # resMsgA = '[' + user_chat.name + ']：您好 :>'
        # PostMessge(token, str(PostText(my.W_NAME, resMsgA)))

        resMsgB = '[' + my.name + ']：本宫我今天"宠幸"你，快给我回应 ：》  1分钟内不回应就pass你  '
        # resMsgB = '已匹配到 '+ my.name + '，回复消息打个招呼吧 :> \n(' + link + '的主页)'
        PostMessge(token, str(PostText(user_chat.W_NAME, resMsgB)))

        #如果配对的广告机器人，要给我发一个提示
        if user_chat.id in adUser('1'):
            adminId = 817  #我目前手机微信绑定的账户id
            content = "宠幸from-" + str(my.id) + "-to-" + str(user_chat.id)
            admin = User.objects.get(id=adminId)
            PostMessge(token, str(PostText(admin.W_NAME, content)))




            # resMsgB = '[' + my.name + ']：您好 :>'
        # PostMessge(token, str(PostText(user_chat.W_NAME, resMsgB)))



def randomMatchLogic(my, user_chat):
    uid = my.id
    time = GetTimeNow()
    chat = Chat(sid_id=user_chat.id, rid_id=uid, mode='1', time=time, time_end=time, close='0')  #mode=1 随机的配对
    chat.save()

    my.state = '3'
    my = scoreSpend(my)

    user_chat.state = '3'
    user_chat = scoreSpend(user_chat)

    # 线上环境
    if 'centos' in platform.platform():
        # 給双方发微信推送告诉配对成功
        token = GetAccessToken()
        resMsgA = '【系统消息】刚刚为你匹配到 ' + user_chat.name + '，回复消息打个招呼，聊天请注意文明用语哦！ '
        # resMsgA = '已匹配到 '+ user_chat.name + '，你们可以开始对话 :> (' + link + '的主页)'
        PostMessge(token, str(PostText(my.W_NAME, resMsgA)))

        resMsgA = '[' + user_chat.name + ']：您好 :>'
        PostMessge(token, str(PostText(my.W_NAME, resMsgA)))

        resMsgB = '【系统消息】已匹配到 ' + my.name + '，回复消息打个招呼吧 :>  '
        # resMsgB = '已匹配到 '+ my.name + '，回复消息打个招呼吧 :> \n(' + link + '的主页)'
        PostMessge(token, str(PostText(user_chat.W_NAME, resMsgB)))

        resMsgB = '[' + my.name + ']：您好 :>'
        PostMessge(token, str(PostText(user_chat.W_NAME, resMsgB)))



#检查是否到晚上9点
def check21PM(req):
    hour = datetime.datetime.now().strftime("%H")
    true = 0
    if int(hour) == 21 or int(hour) == 22 or int(hour) == 23 or int(hour) == 24 or int(hour) == 0:
        true = 1
    elif req.COOKIES.get('nine') == '0':
        true = 1
    return true

#随机获取活跃用户
def activeUsers(my,count):
    # start = OnlineTime(24)
    if my.sex == '2':
        # user = User.objects.filter(time_login_today__gt=start).order_by('time_login_today').exclude(id=my.id)[:50]
        user = User.objects.filter(time_login_today__gt='2017-10-30 00:00:17').order_by('-time_login_today').exclude(id=my.id)[:50]
        print(user.count())
    else:
        if my.sex == '0':
            sex = '1'
        else:
            sex = '0'
        # user = User.objects.filter(time_login_today__gt=start).filter(sex=sex).order_by('time_login_today').exclude(id=my.id)[:50]
        user = User.objects.filter(time_login_today__gt='2017-10-30 00:00:17',sex=sex).order_by('-time_login_today').exclude(id=my.id)[:50]
        # print(user.count())
    if user.count() < count:
        user = random.sample(user, user.count())
    else:
        user = random.sample(user, count)
    return user


def activeList(req):
    uid = req.COOKIES.get('UID')
    my  = User.objects.get(id=uid)
    user = activeUsers(my, 50)
    site_url = GetSiteUrl(req)

    #女王选兵
    user_match = User.objects.filter(sex='1', state='2',time_login_today__gt='2017-10-30 00:00:17').order_by('-time_gochat')[:50]
    content = {'my': my, 'user':user, 'site_url':site_url, 'user_match':user_match}
    response = render(req, 'message/active_list.html', content)
    return response


def helpList(req):

    help = req.GET.get('help') #具体哪条帮助



    url = GetSiteUrl(req) + 'help-list/'
    content = {'url':url, 'help':help}



    response = render(req, 'user/help_list.html', content)
    return response



def getUserLink(req, user):
    url = GetSiteUrl(req) + 'user/' + str(user.id)
    link = '<a href="' + url + '">' + user.name + '</a>'
    return link


def CheckBrowser(req):
    meta = req.META['HTTP_USER_AGENT']
    BrowserType = 5

    if 'MicroMessenger' in meta:
        BrowserType = 0

    if 'MicroMessenger' in meta and 'Android' in meta:
        BrowserType = 1
    elif 'iPhone' in meta:
        BrowserType = 2  #表明是iphone 浏览器或 iphone微信
    elif 'Android' in meta:
        BrowserType = 3  #表明是androidl浏览器

    return BrowserType  #如果是5，表示不是手机浏览器


def invite(req):
    BrowserType = CheckBrowser(req)
    action = req.GET.get('action')
    uid = req.GET.get('uid')
    user = User.objects.get(id=uid)
    myId = req.COOKIES.get('UID')
    myself = 0
    if str(uid) == myId:
        myself = 1
    if req.method == 'POST':
        user.score_forever = str(int(user.score_forever) + 1)
        user.save()
    url_friend = GetSiteUrl(req) + 'invite?action=desc&uid=' + uid
    content = {'user': user, 'myself':myself, 'url_friend':url_friend, 'BrowserType':BrowserType}
    #打气 (所有判断在前端完成)
    if action == 'daqi':
        response = render(req, 'user/daqi.html', content)
        return response

    if action == 'desc':

        response = render(req, 'user/invite.html', content)
        return response

    response = render(req, 'user/invite.html', content)
    return response


def score_desc(req):
    uid = req.COOKIES.get('UID')
    site_url = GetSiteUrl(req)
    content = {'site_url':site_url, 'uid':uid}
    response = render(req, 'chat/score_desc.html', content)
    return response


# find the user chatting with me
def GetUserChat(chat, uid):
    if uid == str(chat.rid.id):
        user_chat = chat.sid
    else:
        user_chat = chat.rid
    return user_chat




#修改用户状态
def modifyState():
    return



#注册
class Register(View):
    def post(self, req):
        username = req.POST.get('username')
        password = req.POST.get('password')
        code = req.POST.get('code')
        name = req.POST.get('name')
        #不能有相同用户名
        test = User.objects.filter(username=username)
        if test.count() > 0:
            return HttpResponse('have the same username')

        if code == 'kidd888':
            user = User(username= username, password= password, name=username,time_login_today=GetTimeNow(),remind_time=GetTimeNow())
            user.save()
            user = get_score_today(user)[0]
            context = {'user': user}

            url = reverse('index')
            response = HttpResponseRedirect(url)
            # response.set_cookie('W_NAME', user, max_age=10000000000)
            response.set_cookie('UID', user.id, max_age=10000000000)
            # response.set_cookie('NAME', user.id, max_age=10000000000)
            return response
        return HttpResponse("要向管理员申请内部验证码")

    def get(self, req):
        context = {'': ''}
        response = render(req, 'chat/register.html', context)

        return response





#登录
class Login(View):
    def post(self,req):
        username = req.POST.get('username')
        password = req.POST.get('password')
        user = User.objects.filter(username=username, password=password)
        if user.count() > 0:
            user = user[0]
            user.time_login_today = GetTimeNow()
            user.state = '1'
            user.save()
            response = HttpResponseRedirect(reverse('index'))
            # response.set_cookie('wname', user.get('wname'), max_age=10000000000)
            response.set_cookie('UID', user.id, max_age=10000000000)
            response.set_cookie('name', user.name, max_age=10000000000)
            response.set_cookie('info', user.introduction, max_age=10000000000)
            response.set_cookie('image_url', user.image_url, max_age=10000000000)
            return response
        else:
            return  HttpResponse("用户名或密码错误")




    def get(self,req):
        context = {'user':''}
        response = render(req, 'chat/login.html', context)
        return response
    # response = render('chat/index.html',req, context)
    # response = render_to_response('chat/index.html',
    #                               RequestContext(req, {}))



def getUnreadSum(req):
    uid = req.COOKIES.get('UID')
    unread = Message.objects.filter(rid_id=uid, read_not='0').count()
    return unread


#类似与以前的showInbox，
def chatList(req):
    # 微信触发带登录特性的页面
    W_NAME = req.GET.get('W_NAME')
    if W_NAME:
        my = User.objects.get(W_NAME=W_NAME)
        url = GetSiteUrl(req) + 'chat-list/'
        response = HttpResponseRedirect(url)
        response.set_cookie('UID', my.id, max_age=10000000000)
        response.set_cookie('W_NAME', W_NAME, max_age=10000000000)
        return response

    uid = req.COOKIES.get('UID')
    #todoo 以前是每次发信都要刷新inbox表，比较浪费资源。。优化：访问该页时才刷新最近那一条对话信息 （还是不行，要循环50次）

    result = ChatList.objects.select_related().filter(rid_id=uid).order_by('-time')[:50]
    result2 = ChatList.objects.select_related().filter(sid_id=uid).order_by('-time')[:50] #自己是发送方的

    chats = []
    x = 0
    for i in result:
        a = GetSiteUrl(req) + 'message/' + str(i.sid_id)
        # urls.append(a)
        chats.append({'i':i, 'url':a, 'chat':result2[x]})
        x = x + 1

    url_site = GetSiteUrl(req)
    unreadSum = getUnreadSum(req)
    context = {'chatList': chats, 'url_site':url_site, 'unreadSum':unreadSum, 'uid':int(uid)}
    response = render(req, 'message/chat_list.html', context)
    return response


#与某人的消息记录列表
def showMessage(req,rid):
    uid = req.COOKIES.get('UID')

    if req.method == 'POST':
        if uid == rid:
            return HttpResponse('can not send message to useself')
        #todoo发送信息，日后采用异步实现

        msg = req.POST.get('msg')
        if msg != '':
            saveMessage(uid, rid, msg, '0','0',GetTimeNow())
        url_full = HttpRequest.build_absolute_uri(req)
        return HttpResponseRedirect(url_full)

    else:
        #delete unread count
        message = Message.objects.filter(sid_id=rid, rid_id=uid, read_not='0')
        message.update(read_not='1')
        chatList = ChatList.objects.filter(sid_id=rid, rid_id=uid)  #把别人发给我的未读信息，修改为已读
        chatList.update(unread=0)

        #对方名字
        user = User.objects.get(id=rid)
        userbName = user.name
        siteUrl = GetSiteUrl(req)
        userUrl = siteUrl + 'user/' + rid
        result = Message.objects.select_related().\
            filter(Q(sid_id=uid, rid_id=rid) | Q(sid_id=rid,rid_id=uid)).order_by('-s_time')[:100]
        temp = getUserInfo(user,req) #对方信息
        img_gift_template = temp[2]


    context = {'msgs': result,
               'name':userbName,
               'siteUrl':siteUrl,
               'userUrl':userUrl,
                'img_gift_template':img_gift_template,
               'uid':int(uid),
               }
    response = render(req, 'message/message.html', context)
    return response



def userProfile(req,uid):
    my_uid = req.COOKIES.get('UID')
    my = User.objects.get(id=my_uid)
    user = User.objects.get(id=uid)

    #特殊出处理一下user表的sex
    if user.age == '' or user.age == None:
        user.age = 11


    # 配对某用户,异步触发
    action = req.GET.get('action')
    if action == 'match':
        user = User.objects.get(id=uid)
        #双方state都不能时3,女方就能配对成功，其他都可以
        if my.state == '3':         #自己聊天中
            return HttpResponse('2')
        elif user.state == '3':
            return HttpResponse('0')  #对方与别人聊天中
        else:
            # 成功配对,处理配对相关推送
            girlMatchLogic(my, user)

            return HttpResponse('1')


    #如果时recommand过来，检查用户是否是否在48小时内；如果是，女生可以配对他...但要注意男生未未回应前，不能直接发信息(暂不实现)
    canMatch = '0'
    start = OnlineTime(47)
    if user.time_login_today > start:
        if action == 'recommend' and my.sex == '0' and user.state != '3':  #自己是女性，对方不是对话状态
            canMatch = '1'
        elif my.sex == '0' and user.state != '3':
            #如果曾经聊天，即使不是推荐过来也可以聊
            chat = ChatList.objects.filter(Q(sid_id=uid, rid_id=my.id)|Q(sid_id=my.id, rid_id=uid))
            if chat.count() > 0:
                canMatch = '1'


    #异步检查 资料完整性
    check = req.GET.get('check')
    if check == 'check':
        user_re = UserRecommend.objects.filter(uid_id=my_uid,rid_id=uid)
        user_re = user_re[0]
        #检查是否可以看这个用户资料
        if user_re.open == '0':
            #查看open数量
            count = UserRecommend.objects.filter(uid_id=my_uid, open='1').count()
            # count2 = UserRecommend.objects.filter(uid_id=my_uid,rid_id=uid).count()
            user_re.open = '1'  #更新该值，目的下载不会再弹窗
            user_re.save()
            if count != 0 and count % 3 == 0:  # 每点开三个用户检查一次，并且不是第一次
                #若刚好是3的整数倍，这里检查一下资料完整性
                temp = infoCheck(my)
                if temp == '1':
                    return HttpResponse('1')  # 表示完整
                else:
                    return HttpResponse(temp)
            else:
                return HttpResponse('1')  # 表示不检查

        else:
            return HttpResponse('1')  # 表示不检查


    #反正check之下，只要避免open值更新影响
    if action == 'recommend':
        user_re = UserRecommend.objects.filter(uid_id=my_uid,rid_id=uid)
        user_re = user_re[0]
        user_re.open = '1'
        user_re.save()


    myself = '0' #不是本人
    if my_uid == uid:
        myself = '1'

    # 给用户送花，仅异步使用
    my = scoreValidCheck(my)
    user = scoreValidCheck(user)

    score_aviable = int(my.score_today) + int(my.score_forever)  #查询自己可用积分
    if action ==  'sendFlower':
        msg = '#sendFlower'
        saveMessage(my.id,uid,msg,'0','0',GetTimeNow())
        info = addUserInfo(user) #判断之前是否有userInfo表
        info.giftFlower = info.giftFlower + 1
        info.save()

        if score_aviable == 0:
            return HttpResponse(score_aviable)
        scoreSpend(my) #消费积分
        if myself != '1': #自己就不获得积分
            scoreIncome(user)  #计算获得积分
        return HttpResponse(score_aviable)
    scoreArray = [score_aviable, my.score_today, my.score_forever]


    #检查用户礼物
    temp = getUserInfo(user,req)
    info = temp[0]
    img_gift = temp[1]
    img_gift_template = temp[2]

    #查询用户相册
    imgs = UserImg.objects.filter(uid_id=uid)
    for i in imgs:
        i.image.name = GetSiteUrl(req) + 'media/' + i.image.name
    count = imgs.count()

    # print (my.sex)
    # url_avatar = GetSiteUrl(req) + 'media/' + user.image1.name
    url_avatar = user.image_url
    url_modify_info = GetSiteUrl(req) + 'modify-info'


    url_sendFlower =  GetSiteUrl(req) + 'user/' + str(uid) + '?action=sendFlower'
    url_gochat = GetSiteUrl(req) + 'user/' + str(uid) + '?action=match'
    url_daqi =  GetSiteUrl(req) + 'invite?action=daqi&uid=' + str(my_uid)
    message_url = GetSiteUrl(req) + 'message/' + str(uid)

    #提醒用户可以送花
    cookieText = 'sendFlowerRemind'
    if req.COOKIES.get(cookieText):
        remind = '1'   #提醒用户送花的cookie
    else:
        remind = '0'
    context = {'user': user, 'myself':myself ,'url':url_modify_info,'imgs':imgs, 'url_avatar':url_avatar, 'my':my, 'message_url':message_url, 'url_gochat':url_gochat,
               'action':action, 'url_sendFlower':url_sendFlower, 'canMatch':canMatch, 'url_daqi':url_daqi,
               'img_gift': img_gift, 'info': info, 'img_gift_template':img_gift_template, 'scoreArray':scoreArray, 'remind':remind}
    response = render(req, 'user/info.html', context)

    if remind != '1':
        response.set_cookie(cookieText, '1', max_age=12*3600*2)  #12小时

    return response


#检查用户礼物
def getUserInfo(user,req):
    #检查用户收到的礼物
    img_url_gift = GetSiteUrl(req) + 'media/icon/gift-gift.png'
    img_url_flower = GetSiteUrl(req) + 'media/icon/gift-flower.png'
    img_url_bear = GetSiteUrl(req) + 'media/icon/gift-bear.png'
    img_url_heart = GetSiteUrl(req) + 'media/icon/gift-heart.png'
    img_url_diamond = GetSiteUrl(req) + 'media/icon/gift-diamond.png'

    img_gift_template = [img_url_flower, img_url_bear, img_url_heart, img_url_diamond] #基础图片
    info = addUserInfo(user) #判断是否有表
    if info.giftFlower == 0:
        img_url_flower = img_url_gift
    if info.giftBear == 0:
        img_url_bear = img_url_gift
    if info.giftHeart == 0:
        img_url_heart = img_url_gift
    if info.giftDiamond == 0:
        img_url_diamond = img_url_gift
    img_gift = [img_url_flower, img_url_bear, img_url_heart, img_url_diamond]
    return [info, img_gift, img_gift_template]


def addUserInfo(user):

    info = UserInfo.objects.filter(uid=user)
    if info.count() == 0:
        # 后加的表，所有要判断并添加，在送花、我的，这两个流程都要判断
        info = UserInfo(uid=user)
        info.save()
    else:
        info = info[0]
    return  info


def infoCheck(my):
    # my.age
    # my.xingzuo
    # my.city
    # my.industry
    # my.introduction

    infoNotValue = 0
    infoNotText = ''
    imgs = UserImg.objects.filter(uid_id=my.id)
    info = addUserInfo(my)  # 判断之前是否有userInfo表

    if my.age == '11':
        infoNotValue = infoNotValue + 1
        infoNotText = infoNotText + '年龄、'
    if my.xingzuo == '':
        infoNotValue = infoNotValue + 1
        infoNotText = infoNotText + '星座、'
    if my.city == '':
        infoNotValue = infoNotValue + 1
        infoNotText = infoNotText + '所在城市、'
    if my.industry == '':
        infoNotValue = infoNotValue + 1
        infoNotText = infoNotText + '所在行业、'
    if my.introduction == '' or my.introduction == '这家伙很懒，什么都没写':
        infoNotValue = infoNotValue + 1
        infoNotText = infoNotText + '个人介绍、'
    if imgs.count() <= 3 :
        infoNotText = infoNotText + '相册、'

    if info.job == '':
        infoNotValue = infoNotValue + 1
        infoNotText = infoNotText + '工作职责、'
    if info.company == '':
        infoNotValue = infoNotValue + 1
        infoNotText = infoNotText + '所在公司、'
    if info.hometown == '':
        infoNotValue = infoNotValue + 1
        infoNotText = infoNotText + '家乡、'
    if info.place == '':
        infoNotValue = infoNotValue + 1
        infoNotText = infoNotText + '经常出没、'
    if info.sport == '':
        infoNotValue = infoNotValue + 1
        infoNotText = infoNotText + '运动、'
    if info.music == '':
        infoNotValue = infoNotValue + 1
        infoNotText = infoNotText + '音乐、'
    if info.food == '':
        infoNotValue = infoNotValue + 1
        infoNotText = infoNotText + '食物、'
    if info.movie == '':
        infoNotValue = infoNotValue + 1
        infoNotText = infoNotText + '电影、'
    if info.book == '':
        infoNotValue = infoNotValue + 1
        infoNotText = infoNotText + '书或动漫、'
    if info.foot == '':
        infoNotValue = infoNotValue + 1
        infoNotText = infoNotText + '旅行足迹、'


    if my.sex == '0':
        infoNotText = '资料越完善，推荐用户越合适，也会收到更多的花。请你完善资料：' + infoNotText
    else:
        infoNotText = '对方设置了资料完善的用户才能查看她。请你完善资料：' + infoNotText

    infoNotText = SimpleCut(infoNotText,54)
    if infoNotValue > 1:
        return infoNotText
    else:
        return '1'


def my(req):

    #for test
    # pushFlowerRecord()
    # pushFlower()

    # 微信触发带登录特性的页面
    W_NAME = req.GET.get('W_NAME')
    if W_NAME:
        my = User.objects.get(W_NAME=W_NAME)

        url = GetSiteUrl(req) + 'my/'
        response = HttpResponseRedirect(url)
        response.set_cookie('UID', my.id, max_age=10000000000)
        response.set_cookie('W_NAME', W_NAME, max_age=10000000000)
        return response

    uid = req.COOKIES.get('UID')
    my = User.objects.get(id=uid)

    # temp = infoCheck(my)

    #关闭通知
    remind_day_close = req.GET.get('remind_day_close')
    remind_unread_close = req.GET.get('remind_unread_close')
    if remind_day_close or remind_unread_close:
        if remind_day_close == '1':
            my.remind_day_close = '1'
        elif remind_day_close == '0':
            my.remind_day_close = '0'

        if remind_unread_close == '1':
            my.remind_unread_close = '1'
        elif remind_unread_close == '0':
            my.remind_unread_close = '0'
        my.save()

    score_aviable = int(my.score_today) + int(my.score_forever)
    url_site = GetSiteUrl(req)
    url_info = GetSiteUrl(req) + 'user/' + uid
    url_daqi =  GetSiteUrl(req) + 'invite?action=daqi&uid=' + str(uid)
    unreadSum = getUnreadSum(req)
    context = {'my': my, 'url_info':url_info, 'url_daqi':url_daqi, 'url_site':url_site, 'unreadSum':unreadSum, 'score_aviable':score_aviable}
    response = render(req, 'user/my.html', context)
    return response


@csrf_exempt
def modifyInfo(req):
    if req.method == 'POST':
        uid = req.COOKIES.get('UID')
        my = User.objects.get(id=uid)


        #更新头像
        avatar_key = req.POST.get('avatar_key','')
        avatar = req.FILES.get('avatar')
        if avatar != None:
            my.image1.delete()  #先删除原来头像
            my.image1 = avatar
            my.image1.name = 'avatar-' + str(uid) + '.jpg'
            my.save()
            my.image_url = GetSiteUrl(req) + 'media/' + my.image1.name
            my.save()
            return HttpResponse('1')


        #删除图片
        delete_img = req.POST.get('delete_img','x')  #
        if delete_img != 'x' :
            result = UserImg.objects.filter(uid_id=uid)
            result[int(delete_img)].image.delete()
            result[int(delete_img)].delete()

        else:
            # 异步更新图片
            # imgData = req.POST.get('base64')
            image = req.FILES.get('fileVal')
            if image == None:
                print ('no photo save')
            else:
                img = UserImg(uid_id=uid, image=image, time=GetTimeNow())
                img.save()
                return HttpResponse('1')


        #todoo
        my.name = req.POST.get('name')
        my.sex = req.POST.get('sexInput')
        my.age = req.POST.get('ageInput')
        my.xingzuo = req.POST.get('xingzuo')
        my.city = req.POST.get('city')
        my.industry = req.POST.get('industry')
        my.introduction = req.POST.get('introduction')
        my.save()

        info = addUserInfo(my)
        info.job = req.POST.get('job')
        info.company = req.POST.get('company')
        info.hometown = req.POST.get('hometown')
        info.place = req.POST.get('place')
        info.sport = req.POST.get('sport')
        info.music = req.POST.get('music')
        info.food = req.POST.get('food')
        info.movie = req.POST.get('movie')
        info.book = req.POST.get('book')
        info.foot = req.POST.get('foot')
        info.save()


        url = GetSiteUrl(req) + 'user/' + uid
        response = HttpResponseRedirect(url)
        return response


    else:
        W_NAME = req.GET.get('W_NAME')
        #微信触发带登录特性的页面
        if W_NAME:
            my = User.objects.get(W_NAME=W_NAME)
            url = GetSiteUrl(req) + 'modify-info'
            response = HttpResponseRedirect(url)
            response.set_cookie('UID', my.id, max_age=10000000000)
            response.set_cookie('W_NAME', W_NAME, max_age=10000000000)
            return response
        uid = req.COOKIES.get('UID')
        my = User.objects.get(id=uid)
        # 特殊出处理一下user表的age
        if my.age == '' or my.age == None:
            my.age = 11

        imgs = UserImg.objects.filter(uid_id=uid)
        info = addUserInfo(my)
        for i in imgs:
            i.image.name = GetSiteUrl(req) + 'media/' + i.image.name
        content = {
            'my': my,
            'imgs':imgs,
            'info':info,
        }
        #前端更换图片，异步调用updatePhoto把图片保存到数据库
        response = render(req, 'user/modify_info.html',content)
        return response



# #每小时处理一下未读信息，把最近48小的未读信息总数同步到user表，user表的数据仅用作推送使用
# def updateUserUnread():
#     chat = ChatList.objects.select_related().filter(time__gt=OnlineTime(48)).exclude(unread=0)
#     if chat.count() > 0:
#         for i in chat:
#             user = i.rid
#             user.unread =



# #9：00、9：01触发未读提醒，只查询最近两天未读消息量。
# def unreadReminder():
#     token = GetAccessToken()
#     chat = ChatList.objects.select_related().filter(time__gt=OnlineTime(48)).exclude(unread=0)
#     #去掉重复
#     if chat.count() > 0:
#         temp = [chat[0].rid]
#         #循环所有chat记录，每个用户只保留1条记录
#         for i in chat:
#             k = 0
#             user = i.rid
#             for j in temp:
#                 if user.id == j.id:
#                     k = k + 1
#             if k == 0:
#                 temp.append(user)
#                 break
#
#         for i in temp:
#             text = '【温馨提醒】你有未读留言，请点底部菜单[留言]查看...关闭提醒请点[我的]设置。'
#             if i.remind_unread_close != '1':
#                 PostMessge(token, str(PostText(i.W_NAME, text)))
#                 i.remind_time = GetTimeNow()
#                 i.save()
#                 print('给用户id：'+ str(i.id) +'发送未读提醒')
#     return


#9：00、9：01触发未读提醒，只查询最近1天未读消息量。
def unreadReminder(sex):
    token = GetAccessToken()
    chat = ChatList.objects.select_related().filter(time__gt=OnlineTime(24)).exclude(unread=0)  #用24小时，就是保证下次触发那个没有未读的提醒

    #去掉重复
    if chat.count() > 0:
        temp = [chat[0].rid]
        #循环所有chat记录，每个用户只保留1条记录
        for i in chat:
            k = 0
            user = i.rid
            for j in temp:
                if user.id == j.id:
                    k = k + 1
            if k == 0:
                temp.append(user)


        for i in temp:
            #把今天已经提醒过的用户跳过; 日后在chatlist表就应该把已发通知的过滤掉
            if dayTimeCompare(i.remind_time, GetTimeNow()) == '1':
                continue
            text = ''
            flower = ''
            bear = ''
            heart = ''
            diamond = ''

            if i.sex == sex: #只处理目标性别的用户推送
                unread = getUnreadMsg(i.id)
                if unread[0] > 0:
                    text = '留言' + str(unread[0]) + '条'
                if unread[1] > 0:
                    flower = str(unread[1]) + '朵花，'
                if unread[2] > 0:
                    bear = str(unread[2]) + '个小熊，'
                if unread[3] > 0:
                    heart = str(unread[3]) + '个爱心，'
                if unread[4] > 0:
                    diamond = str(unread[4]) + '颗钻石，'

                if sex == '0':
                    text = '女皇好，\n1)今天你收到' + flower + bear + heart + diamond + text + '点【留言】查看。' + '\n2)今天帅哥已准备好，你想宠谁就点谁,点【配对】查看'
                    # text = '【温馨提醒】你有未读留言，请点底部菜单[留言]查看...关闭提醒请点[我的]设置。'
                else:
                    text = '帅哥好，\n1)今天你收到' + flower + bear + heart + diamond + text + '点【留言】查看。' + '\n2)今天女神推荐已为你准备好，请看看,合眼缘就给她送花，点【配对】查看'


                if i.remind_unread_close != '1':
                    PostMessge(token, str(PostText(i.W_NAME, text)))
                    i.remind_time = GetTimeNow()
                    i.save()
                    print('给用户id：'+ str(i.id) +'发送未读提醒')
    return


def getUnreadMsg(uid):
    start = OnlineTime(48)
    msg = Message.objects.filter(rid_id=uid,read_not='0',s_time__gt=start)
    flowerCount = 0
    textCount = 0
    bearCount = 0
    heartCount = 0
    diamondCount = 0
    for i in msg:
        if i.content == '#sendFlower':
            flowerCount = flowerCount + 1
        elif i.content == '#sendBear':
            bearCount = bearCount + 1
        elif i.content == '#sendHeart':
            heartCount = heartCount + 1
        elif i.content == '#sendDiamond':
            diamondCount = diamondCount + 1
        else:
            textCount = textCount + 1
    return [textCount, flowerCount, bearCount, heartCount, diamondCount]


#9：00、9：01触发聊天邀请提醒（没有未读的用户）
def chatReminder():
    # 如果remind_time是今天8:30点以前的，然后给他们推送
    # users = User.objects.filter(Q(remind_time__lt=OnlineTime(4))| Q(remind_time='')|Q(remind_time=None))
    # users = User.objects.filter(remind_time__lt=OnlineTime(2),remind_time__gt=OnlineTime(48)).exclude(user_type='ad')
    users = User.objects.filter(remind_time__lt=OnlineTime(2),time_login_today__gt=OnlineTime(48)).exclude(user_type='ad')
    token = GetAccessToken()
    text = ['朋友，可以把快乐加倍，把悲伤减半。',
            '真正的朋友应该说真话，不管话多么尖锐……',
            '财富不是真正的朋友,而朋友却是真正的财富',
            '相识是最珍贵的缘分，虽然我们不曾谋面，来也匆匆，去也匆匆，但彼此祝福来自我们的真心，愿我们在无声的世界写出有色温暖的文字，愿幸福围绕在您身边，愿微笑甜在您心间！',
            '我得到过的来自一个陌生人的爱，你呢',
            '分手后不可以做朋友，因为彼此伤害过；不可以做敌人，因为彼此深爱过。所以我们变成了最熟悉的陌生人。',
            '如果我不联系你，你不联系我， 是不是总有一天，我们就成了陌生人?',
            '我们和爱的人争吵 , 却要对陌生人倾诉。',
            '和爱的人吵架，和陌生人讲心里话。',
            '因为交浅所以言深，故而只爱陌生人。',
            '找到朋友的唯一办法是自己成为别人的朋友',
            '爱情正是一个将一对陌生人变成情侣，又将一对情侣变成陌生人的游戏',
            '在这个危险的世界也要勇敢地先对一个陌生人示好，如果不想陌生人敌对你的话。'
            ]
    text = random.sample(text, 1)
    text = '今天一句：' + text[0] + '\n 认识新朋友，请点【配对】'
    # text = '【温馨提醒】晚上好，我们在#九点聊天#等你，听听你的故事'
    if users.count() > 0:
        for i in users:
            if i.remind_day_close != '1':
                print('给用户id：' + str(i.id) + '发送来玩提醒')
                PostMessge(token, str(PostText(i.W_NAME, text)))
                i.remind_time = GetTimeNow()
                i.save()
            # break
    return




#每天执行一次，送花（广告）记录； #此呈现必在2：00执行，否则就不是10：00~23：00
def pushFlowerRecord():

    updateAdUser()

    start = OnlineTime(48)
    user = User.objects.filter(time_login_today__gt=start).exclude(user_type='ad')
    chat = ChatList.objects.select_related().filter(time__gt=start).exclude(unread=0)
    #去掉有未读信息的用户
    temp = []
    for i in user:
        x = 0
        for j in chat:
            tempUser = j.rid
            if i.id == tempUser.id: #找到相同的就直接去user
                x = 1
                break
        if x == 0:
            temp.append(i)
    user = temp

    #送花的时间范围
    now = datetime.datetime.now()
    start = now + datetime.timedelta(hours=8) #此呈现必在2：00执行，否则就不是10：00~23：00
    end = now + datetime.timedelta(hours=21)
    startTimeStamp = int(time.mktime(start.timetuple()))  # 把时间数组转timeStamp
    endTimeStamp = int(time.mktime(end.timetuple()))  #
    #写入广告花记录表
    for i in user:
        if i.sex == '0':
            count = random.sample([1,2,3],1)[0]
            userRamId = random.sample(adUser('1'),count) #1~3个用户
            flowerCount = random.sample([1,2,3],1)[0] #送1~4多花
        else:
            count = random.sample([1,2],1)[0]  #s随机取1
            userRamId = random.sample((adUser('0')),count) #1~3个女性用户
            flowerCount = random.sample([1,2],1)[0] #送1~3朵花

        #每个广告用户负责送几个花
        for x in userRamId:
            #循环几次写入花
            y = 0
            while y < flowerCount:
                # 生成随机时间，早10点~晚11点
                # import time,datetime,random
                timeStamp = random.randint(startTimeStamp, endTimeStamp)  #每次送花时间都不一样
                timeArray = time.localtime(timeStamp)
                timeString = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)

                msg = '#sendFlower'
                record = PushFlowerRecord(sid_id=x,rid_id=i.id,time=timeString, content=msg)
                record.save()
                y = y + 1
    return



def updateAdUser():
    #把机器人收到未读消息(含送花),标记为已读
    adUserAll = []
    for i in adUser('1'):
        adUserAll.append(i)
    for i in adUser('0'):
        adUserAll.append(i)

    #批量更新 所有机器人未读状态未已读
    chat = ChatList.objects.filter(rid_id__in=adUserAll).exclude(unread=0)
    chat.update(unread=0)
    message = Message.objects.filter(rid_id__in=adUserAll, read_not='0')
    message.update(read_not='1')


    #刷新机器人的登录状态
    user = User.objects.filter(user_type='ad')
    user.update(time_login_today=GetTimeNow())




#定时程序，每分钟触发的 送花逻辑
def pushFlower():
    #message type是10
    start = OnlineTimeMin(4)
    end = GetTimeNow()
    # push = PushFlowerRecord.objects.filter(sendNot='0',time__gt=start)
    # text = []
    # for i in push:
    #     text.append(i.time)
    # push = PushFlowerRecord.objects.filter(sendNot='0',time__lt=end)
    # text2 = []
    # for i in push:
    #     text2.append(i.time)
    # x = 0
    # for i in text:
    #     for j in text2:
    #         if i == j:
    #             x = x + 1

    push2 = PushFlowerRecord.objects.filter(sendNot='0',time__gt=start, time__lt=end)

    for i in push2:
        saveMessage(i.sid_id, i.rid_id, i.content, '0','10',GetTimeNow())
        i.sendNot = '1'
        i.save()
    return





def checkMin():

    #更新状态
    # start = OnlineTime(0.5)
    # user = User.objects.filter(time_gochat__lt=start)
    # for i in user:
    #     if i.state == '2':
    #         if i.time_gochat != None and i.time_gochat != '':
    #             time_gochat = i.time_gochat
    #             if time_gochat < start:
    #                 i.state = '1'
    #                 i.save()


    #检查30分钟没有动的对话
    start = OnlineTime(0.5)
    chat = Chat.objects.filter(close='0',time_end__lt=start)
    for i in chat:
        usera = i.sid
        userb = i.rid
        usera.state = '1'
        usera.save()
        userb.state = '1'
        userb.save()
        i.close = '1'
        i.time_end = GetTimeNow()
        i.save()
    return





#服务超时提醒,每小时检查一次
def serviceRemind():

    token = GetAccessToken()
    start1 = OnlineTime(48)
    start2 = OnlineTime(36)
    hour = datetime.datetime.now().strftime("%H")
    if int(hour) == 18  or  int(hour) == 19 or int(hour) == 20 or int(hour) == 21 or int(hour) == 22:
        result = User.objects.filter(time_login_today__gt=start1, time_login_today__lt=start2, remind_key="0")
        for i in result:
            msgContent = '【系统提醒】：由于微信48小时响应限制，你将在2小时后无法收到我们的通知。\n\n请点【配对】菜单一次，刷新状态'
            msgContent = PostFormat(msgContent)
            PostMessge(token, str(PostText(i.W_NAME, msgContent)))
            i.remind_key = "1"
            i.save()
    return HttpResponse('1')


#查询在线用户
def onlineUser(req):
    content = {}
    response = render(req, 'chat/online_user.html', content)
    return


#定时器
def timer(req):
    # unreadReminder()
    chatReminder()

    return HttpResponse('1')

def test(req):
    # chatReminder()
    # unreadReminder('0')
    # pushFlowerRecord()
    # pushFlower()
    # unreadReminder('1')
    response = render(req, 'MP_verify_U4Tmj9FOXTelfMyx.txt')
    return response


def test3(req):
    test2()
    return HttpResponse('1')

def test2():
    user = User(username='444')
    user.save()
    print ('123')
    return


def tick2():
    print('Tick! The time is: %s' % datetime.datetime.now())


# if __name__ == '__main__':
#     scheduler = BackgroundScheduler()
#     scheduler.add_job(timer, 'interval', seconds=3)
#     # scheduler.add_job(tick2, 'cron', second='*/3', hour='*')
#     scheduler.start()
#     print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
#
#     try:
#         # This is here to simulate application activity (which keeps the main thread alive).
#         while True:
#             time.sleep(2)
#             print('sleep!')
#     except (KeyboardInterrupt, SystemExit):
#         scheduler.shutdown()  # Not strictly necessary if daemonic mode is enabled but should be done if possible
#         print('Exit The Job!')


def tick():
    print('Tick! The time is: %s' % datetime.datetime.now())


# if __name__ == '__main__':
#     scheduler = BlockingScheduler()
#     scheduler.add_job(tick, 'cron', second='*/3', hour='*')
#     print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
#
#     try:
#         scheduler.start()
#     except (KeyboardInterrupt, SystemExit):
#         scheduler.shutdown()




#修改图片时，异步保存到数据库
def updatePhoto(img):
    return



####管理员模块
def manageLogin(req):
    return


def manageListActiveUser(req):
    return


def userActiveData(req):
    return


def manageMessage(req):
    return

def manageAddUser(req):
    return

def manageSendMessage(req):
    return







def api_register2(req):
#
#     username = req.GET.get('username')
#     password = req.GET.get('password')
#     name = req.GET.get('name')
#
#     user = leancloud.User()
#     user.set_username(username)
#     user.set_password(password)
#     user.name = name
#     user.sign_up()
    return

#api 获取用户资料、喜欢、屏蔽、投诉某人等操作
def apiUser(req,uid):
    return


# #api 退出聊天/匹配/离开， 通过前端异步触发，
# def apiLeaveChat(req):
#     state = currentUser.get('state')
#     if state == '2': #配对中
#         currentUser.set('state', '1')
#     elif state == '3': #聊天中
#         currentUser.set('state', '1')
#         #todoo, 从配对表删除关系，并且修改双方属性, 还涉及微信触发
#
#     currentUser.save()
#     return

#api 发起配对， 异步
def apiChat(req):
    uid = req.COOKIES.get('UID')

    return


#api 魔法配对
def apiChatMagic(req):
    return


#API 注册接口
# class API_Register(View):
#     def get(self, req):
#         username = req.GET.get('username')
#         password = req.GET.get('password')
#         name = req.GET.get('name')
#         try:
#             user = leancloud.User()
#             user.set_username(username)
#             user.set_password(password)
#             user.name = name
#             user.sign_up()
#             print (user._attributes)
#             info = user._attributes
#
#         except LeanCloudError as e:
#             return HttpResponseServerError(e)
#
#         print(leancloud.User.get_current())
#         # return HttpResponse(leancloud.User.get_current())
#         return HttpResponse(user._attributes)
#         # url = GetSiteUrl(req)
#         # return HttpResponseRedirect(url)
#
#     def post(self,req):
#         return



def apiChatState(req):
    return



def apiLogin(req):
    return






        # def index(request):
#     latest_question_list = Question.objects.order_by('-pub_date')[:5]
#     context = {'latest_question_list': latest_question_list}
#     return render(request, 'polls/index.html', context)