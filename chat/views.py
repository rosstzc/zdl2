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
import logging
import json
import  datetime

logging.basicConfig(level=logging.DEBUG)

from django.template.loader import get_template

import  platform

import sys
reload(sys)
sys.setdefaultencoding('utf-8')


# 首页
def index(req):
    #GET  从api/chat_state 获取数据，然后返回到chat.html
    # currentUser = leancloud.User.get_current()
    # todoo, 触发配对,日后也是要异步操作
    if req.method == 'POST':

        #先找到所符合匹配条件的人
        # sex = req.POST.get('sex') #配对性别要求
        # user = leancloud.Object.extend('_User')
        # query = user.query
        # query.equal_to('state', '2')
        # query.equal_to('sex', sex)
        # queryResult = query.find()
        #
        # #todoo 今天匹配过的不重复匹配
        # startTime = OnlineTime(8)
        # chatRecord = leancloud.Object.extend('ChatRecord')
        # query2 = chatRecord.query
        # query3 = chatRecord.query
        # query2.equal_to('sid',currentUser.uid)
        # query2.greater_than_or_equal_to('startTime',startTime)
        # query3.equal_to('rid',currentUser.uid)
        # query3.greater_than_or_equal_to('startTime',startTime)
        # result = leancloud.Query.or_(query2,query3)
        # # result = query2.find()
        # #todoo 把user查询结果与聊天记录表校验，
        # rid = 0
        # for i in queryResult:
        #     k = 0
        #     for j in result:
        #         if i.uid == j.get('sid') or i.uid == j.get('rid'):
        #             k = k + 1
        #     if k == 0:
        #         rid = i.uid
        #         break
        #
        # #没匹配到,提示没找到
        # if rid == 0:
        #     print ('random_not_match')
        #
        #     return
        # else:
        #     print ('random_match')
        #     record = chatRecord()
        #     record.set('sid',currentUser.uid)
        #     record.set('rid',rid)
        #     record.set('close','0')
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
        time = my.time_login_today
        date_time = datetime.datetime.strptime(time,'%Y-%m-%d %H:%M:%S')
        time_string = datetime.datetime.strftime(date_time,'%Y-%m-%d')
        now = datetime.datetime.now()
        DATETIME_FORMAT = '%Y-%m-%d'
        today_string = now.strftime(DATETIME_FORMAT)
        if  time_string != today_string :
            my = score_today(my)
            my.remind_key = '0'  #user表提醒状态，用户与48小时服务提醒


        #发出邀请
        action = req.GET.get('action')
        sex_match = req.COOKIES.get('sex_match')
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
                        if k == 0  or k == 1:
                            key = 1
                            user_chat = user[x]
                            break
                        x = x + 1

                    #匹配到
                    if key == 1:
                        time = GetTimeNow()
                        chat = Chat(sid_id=user_chat.id, rid_id=uid, mode='1', time=time, close='0')
                        chat.save()

                        my.state = '3'
                        my.score_today = str(int(my.score_today) - 1)
                        my.score_sum = str(int(my.score_sum) + 1)
                        my.save()
                        user_chat.state = '3'
                        user_chat.score_today = str(int(user_chat.score_today) - 1)
                        user_chat.score_sum = str(int(user_chat.score_sum) + 1)
                        user_chat.save()

                        #线上环境
                        if 'centos' in platform.platform():
                            #給双方发微信推送告诉配对成功
                            token = GetAccessToken()
                            link = getUserLink(req, user_chat)
                            resMsgA = '【系统消息】：刚刚为你匹配到 '+ user_chat.name + '，回复消息打个招呼，聊天请注意文明用语哦！ '
                            # resMsgA = '已匹配到 '+ user_chat.name + '，你们可以开始对话 :> (' + link + '的主页)'
                            PostMessge(token, str(PostText(my.W_NAME, resMsgA)))
                            resMsgA = '[' + user_chat.name + ']：您好 :>'
                            PostMessge(token, str(PostText(my.W_NAME, resMsgA)))


                            link = getUserLink(req, my)
                            resMsgB = '【系统消息】：已匹配到 '+ my.name + '，回复消息打个招呼吧 :>  '
                            # resMsgB = '已匹配到 '+ my.name + '，回复消息打个招呼吧 :> \n(' + link + '的主页)'
                            PostMessge(token, str(PostText(user_chat.W_NAME, resMsgB)))
                            resMsgB = '[' + my.name + ']：您好 :>'
                            PostMessge(token, str(PostText(user_chat.W_NAME, resMsgB)))

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
                    resMsgA = '【系统消息】：你已退出聊天'
                    PostMessge(token, str(PostText(my.W_NAME, resMsgA)))

                    resMsgB = '【系统消息】：对方已退出聊天'
                    PostMessge(token, str(PostText(user_chat.W_NAME, resMsgB)))

            if my.state == '2':
                my.state = '1'
                my.save()
            response = HttpResponseRedirect(reverse('index'))
            return response


        #如果状态是2，并且time_gochat时间超过30分钟，让状态回复1
        if my.state == '2':
            start = OnlineTime(0.5)
            if my.time_gochat != None and my.time_gochat != '':
                time_gochat = my.time_gochat
                if time_gochat < start:
                    my.state = '1'
                    my.save()
        if my.introduction == '':
            my.introduction = "这家伙很懒，什么都没写"
        my.save()


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
        score_aviable = int(my.score_today) + int(my.score_forever)
        url_site = GetSiteUrl(req)
        url_gochat = GetSiteUrl(req) + '?action=gochat'
        url_leave = GetSiteUrl(req) + '?action=leave'
        unreadSum = getUnreadSum(req)
        content = {'my': my, 'user_chat':user_chat, 'state':my.state,
                   'url_gochat':url_gochat, 'url_leave':url_leave, 'url_info':url_info, 'url_site':url_site,
                   'score_available':score_aviable, 'unreadSum':unreadSum}
        response = render(req, 'chat/chat.html', content)
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





def getUserLink(req, user):
    url = GetSiteUrl(req) + 'user/' + str(user.id)
    link = '<a href="' + url + '">' + user.name + '</a>'
    return link

def invite(req):
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
    content = {'user': user, 'myself':myself, 'url_friend':url_friend}
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
    site_url = GetSiteUrl(req)
    content = {'site_url':site_url}
    response = render(req, 'chat/score_desc.html', content)
    return response


# find the user chatting with me
def GetUserChat(chat, uid):
    if uid == str(chat.rid.id):
        user_chat = chat.sid
    else:
        user_chat = chat.rid
    return user_chat


#查询某用户信息
# def getUserInfo(uid):
#     user = leancloud.Object.extend('_User')
#     query = user.query
#     my = query.get(uid)
#     return my


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
            user = User(username= username, password= password, name=username)
            user.save()
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

    result = ChatList.objects.select_related().filter(rid=uid).order_by('-time')[:50]

    chats = []
    for i in result:
        a = GetSiteUrl(req) + 'message/' + str(i.sid_id)
        # urls.append(a)
        chats.append({'i':i, 'url':a})

    url_site = GetSiteUrl(req)
    unreadSum = getUnreadSum(req)
    context = {'chatList': chats, 'url_site':url_site, 'unreadSum':unreadSum}
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
            saveMessage(req, uid, rid, msg, '0')
        url_full = HttpRequest.build_absolute_uri(req)
        return HttpResponseRedirect(url_full)

    else:
        #delete unread count
        message = Message.objects.filter(sid_id=rid, rid_id=uid, read_not='0')
        message.update(read_not='1')
        chatList = ChatList.objects.filter(sid_id=rid, rid_id=uid)
        chatList.update(unread=0)

        #对方名字
        userbName = User.objects.get(id=rid).name
        siteUrl = GetSiteUrl(req)
        result = Message.objects.select_related().\
            filter(Q(sid_id=uid, rid_id=rid) | Q(sid_id=rid,rid_id=uid)).order_by('-s_time')[:100]

    context = {'msgs': result,
               'name':userbName,
               'siteUrl':siteUrl

               }
    response = render(req, 'message/message.html', context)
    return response






def userProfile(req,uid):
    user = User.objects.get(id=uid)
    imgs = UserImg.objects.filter(uid_id=uid)
    for i in imgs:
        i.image.name = GetSiteUrl(req) + 'media/' + i.image.name
    count = imgs.count()
    my_uid = req.COOKIES.get('UID')
    # url_avatar = GetSiteUrl(req) + 'media/' + user.image1.name
    url_avatar = user.image_url
    myself = '0' #不是本人
    if my_uid == uid:
        myself = '1'
        url_modify_info = GetSiteUrl(req) + 'modify-info'
        context = {'user': user,'myself':myself, 'url':url_modify_info, 'imgs':imgs, 'url_avatar':url_avatar}
        response = render(req, 'user/info.html', context)
        return response

    context = {'user': user, 'imgs':imgs, 'url_avatar':url_avatar}
    response = render(req, 'user/info.html', context)
    return response


def my(req):
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
        imgs = UserImg.objects.filter(uid_id=uid)
        for i in imgs:
            i.image.name = GetSiteUrl(req) + 'media/' + i.image.name
        content = {
            'my': my,
            'imgs':imgs,
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



#9：00、9：01触发未读提醒，只查询最近两天未读消息量。 （先触发这个10次，再触发下一个方法10次）
def unreadReminder():
    token = GetAccessToken()
    chat = ChatList.objects.select_related().filter(time__gt=OnlineTime(48)).exclude(unread=0)
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
                break

        for i in temp:
            text = '你有未读留言，请点底部菜单[留言]查看'
            PostMessge(token, str(PostText(i.W_NAME, text)))
            i.remind_time = GetTimeNow()
            i.save()
            print('给用户id：'+ str(i.id) +'发送未读提醒')
    return



#9：00、9：01触发聊天邀请提醒（没有未读的用户）
def chatReminder():
    # 如果remind_time是今天9点以前的，然后给他们推送
    users = User.objects.filter(remind_time__lt=OnlineTime(4))
    token = GetAccessToken()
    if users.count() > 0:
        for i in users:
            text = '晚上好，我们在#九点聊天#等你，听听你的故事'
            PostMessge(token, str(PostText(i.W_NAME, text)))
            i.remind_time = GetTimeNow()
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
            msgContent = '【系统提醒】：由于微信48小时响应限制，你将在2小时后无法收到我们的通知。\n请点【快聊】菜单一次，以刷新状态。'
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
    response = render(req, 'MP_verify_U4Tmj9FOXTelfMyx.txt')
    return response




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