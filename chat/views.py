# -*- coding: utf-8 -*-
from __future__ import unicode_literals


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
logging.basicConfig(level=logging.DEBUG)

from django.template.loader import get_template

import  platform

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
        now = datetime.datetime.now()
        DATETIME_FORMAT = '%Y-%m-%d'
        today_string = now.strftime(DATETIME_FORMAT)
        if  time != today_string :
            my.time_login_today = today_string
            my.score_today = '30'
            if my.sex == '0':
                my.score_today = '50'
            my.save()


        #发出邀请
        action = req.GET.get('action')
        sex_match = req.COOKIES.get('sex_match')
        if action == 'gochat':
            if my.state == '3':   #在聊中
                response = HttpResponseRedirect(reverse('index'))
                return response
            else:
                my.state = '2'
                my.save()

                #到user表找状态"匹配中"的人； todoo 写入一个最近匹配时间，这样就不用一个自动脚本来刷新用户状态；
                user = User.objects.filter(state='2').exclude(id=uid)

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
                        if k == 0:
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

                        #給双方发微信推送告诉配对成功
                        token = GetAccessToken()
                        link = getUserLink(req, user_chat)
                        resMsgA = '已匹配到 '+ user_chat.name + '，你们可以开始对话 :> \n(' + link + '的主页)'
                        PostMessge(token, str(PostText(my.W_NAME, resMsgA)))

                        link = getUserLink(req, my)
                        resMsgB = '已匹配到 '+ my.name + '，你们可以开始对话 :> \n(' + link + '的主页)'
                        PostMessge(token, str(PostText(user_chat.W_NAME, resMsgB)))

                        response = HttpResponseRedirect(reverse('index'))
                        return response

                # else:
                #     return HttpResponse('all is busy') # 前端要效果


        #退出聊天
        if action == 'leave':
            if my.state == '3':
                chat = Chat.objects.select_related().filter(Q(rid=uid) | Q(sid=uid), close='0')
                user_chat = GetUserChat(chat[0],uid)
                my.state = '1'
                my.save()
                user_chat.state = '1'
                user_chat.save()
                chat.update(close='1') #一般只有1个，考虑到容错，就全部更新

                token = GetAccessToken()
                #todoo 给双方发推送告诉已退出聊天
                resMsgA = '你已退出聊天'
                PostMessge(token, str(PostText(my.W_NAME, resMsgA)))

                resMsgB = '对方已退出聊天'
                PostMessge(token, str(PostText(user_chat.W_NAME, resMsgB)))

            if my.state == '2':
                my.state = '1'
                my.save()
            response = HttpResponseRedirect(reverse('index'))
            return response


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
        content = {'my': my, 'user_chat':user_chat, 'state':my.state,
                   'url_gochat':url_gochat, 'url_leave':url_leave, 'url_info':url_info, 'url_site':url_site,
                   'score_available':score_aviable}
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
    url_friend = GetSiteUrl(req)
    content = {'user': user, 'myself':myself, 'url_friend':url_friend}
    #打气 (所有判断在前端完成)
    if action == 'daqi':
        response = render(req, 'user/daqi.html', content)
        return response

    response = render(req, 'user/invite.html', content)
    return response


def score_desc(req):
    content = {}
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
    context = {'chatList': chats, 'url_site':url_site}
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
            saveMessage(req, uid, rid, msg)
        url_full = HttpRequest.build_absolute_uri(req)
        return HttpResponseRedirect(url_full)



    else:
        #对方名字
        userbName = User.objects.get(id=rid).name
        userbUrl = GetUserUrl(req, rid)
        result = Message.objects.select_related().\
            filter(Q(sid_id=uid, rid_id=rid) | Q(sid_id=rid,rid_id=uid)).order_by('-s_time')[:100]

    context = {'msgs': result,
               'name':userbName,
               'url':userbUrl
               }
    response = render(req, 'message/message.html', context)
    return response



#保存信息
def saveMessage(req, sid, rid, msg):
    message = Message(sid_id=sid,
                      rid_id=rid,
                      content=msg,
                      s_time=GetTimeNow())
    message.save()

   #统计对方未读信息
    unread = Message.objects.filter(sid_id=sid, rid_id=rid, read_not=0).count()

    #在ChatList是保存两人之间的最新的对话，在数据库保留写入两条记录，a-b,b-a,但实际上只从第二个字段进行查找
    # 所以先删除旧的，再插入新的
    result = ChatList.objects.filter(Q(sid_id=sid, rid_id=rid) | Q(sid=rid, rid=sid))
    if result.count() >= 1:
        result.delete()

    chat = ChatList(sid_id=sid, rid_id=rid, unread=unread, content=msg, time=GetTimeNow())
    chat.save()
    #反过来再插入一条
    chat = ChatList(sid_id=rid, rid_id=sid, unread=unread, content=msg, time=GetTimeNow())
    chat.save()


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
    url_site = GetSiteUrl(req)
    url_info = GetSiteUrl(req) + 'user/' + uid
    url_daqi =  GetSiteUrl(req) + 'invite?action=daqi&uid=' + str(uid)
    context = {'my': my, 'url_info':url_info, 'url_daqi':url_daqi, 'url_site':url_site}
    response = render(req, 'user/my.html', context)
    return response


@csrf_exempt
def modifyInfo(req):
    if req.method == 'POST':
        uid = req.COOKIES.get('UID')
        my = User.objects.get(id=uid)

        #更新头像
        avatar_key = req.POST.get('avatar_key','')
        if avatar_key == '1':
            my.image1.delete()  #先删除原来头像
            avatar = req.FILES['avatar']
            my.image1 = avatar
            my.image1.name = 'avatar' + str(uid) + '.jpg'
            my.save()
            my.image_url = GetSiteUrl(req) + 'media/' + my.image1.name
            my.save()
            return HttpResponse('1')


        #删除图片
        delete_img = req.POST.get('delete_img')  #
        if delete_img != None :
            result = UserImg.objects.filter(uid_id=uid)
            result[int(delete_img)].image.delete()
            result[int(delete_img)].delete()

        else:
            # 异步更新图片
            # imgData = req.POST.get('base64')
            image = req.FILES.get('fileVal')
            if image == ' ':
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


#查询在线用户
def onlineUser(req):
    content = {}
    response = render(req, 'chat/online_user.html', content)
    return









#定时器
def timer(req):
    #定时触发，更新所有人的在线状态
    return


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