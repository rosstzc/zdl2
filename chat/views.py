# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from datetime import datetime

from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseServerError
from django.urls import reverse
from django.views import View

from django.shortcuts import render
from django.views.generic import View  #通用类
from models import *
from django.db.models import Q

from view_func import *    #公共方法


from django.template.context import RequestContext
# Create your views here.
import leancloud
leancloud.init("TpiAufPcAVp2cR1GRpJQIX5X-gzGzoHsz", "NSXmOEgBlq8Aghgh7LhQAUda")
from leancloud import Object
from leancloud import Query
from leancloud.errors import LeanCloudError

import logging
logging.basicConfig(level=logging.DEBUG)
from django.http import HttpResponse

from django.template.loader import get_template



# 首页
def index(req):
    #GET  从api/chat_state 获取数据，然后返回到chat.html
    currentUser = leancloud.User.get_current()
    # todoo, 触发配对,日后也是要异步操作
    if req.method == 'POST':

        #先找到所符合匹配条件的人
        sex = req.POST.get('sex') #配对性别要求
        user = leancloud.Object.extend('_User')
        query = user.query
        query.equal_to('state', '2')
        query.equal_to('sex', sex)
        queryResult = query.find()

        #todoo 今天匹配过的不重复匹配
        startTime = OnlineTime(8)
        chatRecord = leancloud.Object.extend('ChatRecord')
        query2 = chatRecord.query
        query3 = chatRecord.query
        query2.equal_to('sid',currentUser.uid)
        query2.greater_than_or_equal_to('startTime',startTime)
        query3.equal_to('rid',currentUser.uid)
        query3.greater_than_or_equal_to('startTime',startTime)
        result = leancloud.Query.or_(query2,query3)
        # result = query2.find()
        #todoo 把user查询结果与聊天记录表校验，
        rid = 0
        for i in queryResult:
            k = 0
            for j in result:
                if i.uid == j.get('sid') or i.uid == j.get('rid'):
                    k = k + 1
            if k == 0:
                rid = i.uid
                break


        #没匹配到,提示没找到
        if rid == 0:
            print ('random_not_match')

            return
        else:
            print ('random_match')
            record = chatRecord()
            record.set('sid',currentUser.uid)
            record.set('rid',rid)
            record.set('close','0')


        return

    #get方法
    else:
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
        if action == 'gochat':
            if my.state == '3':   #在聊中
                response = HttpResponseRedirect(reverse('index'))
                return response
            else:
                #到user表找 匹配中的人； todoo 写入一个最近匹配时间，这样就不用一个自动脚本来刷新用户状态
                user = User.objects.filter(state='2').exclude(id=uid)
                if user.count() > 0:
                    user_chat = user[0]
                    time = GetTimeNow()
                    chat = Chat(sid_id=user_chat.id, rid_id=uid, mode='1', time=time, close='0')
                    chat.save()

                    my.state = '3'
                    my.save()
                    user_chat.state = '3'
                    user_chat.save()
                    response = HttpResponseRedirect(reverse('index'))
                else:
                    return HttpResponse('all is busy')

        #退出聊天
        if action == 'leave':
            if my.state == '3':
                chat = Chat.objects.select_related().filter(Q(rid=uid) | Q(sid=uid), close='0')
                user_chat = GetUserChat(chat[0],uid)
                my.state = '2'
                my.save()
                user_chat.state = '2'
                user_chat.save()
                chat.update(close='1') #一般只有1个，考虑到容错，就全部更新
            response = HttpResponseRedirect(reverse('index'))
            return response


        #如果状态是"聊天中"，要获取对方资料; select_related表示外键关联查询
        if my.state == '3':
            chat = Chat.objects.select_related().filter(Q(rid=uid) | Q(sid=uid), close='0')
            user_chat = ''
            if chat.count() > 0:
                user_chat = GetUserChat(chat[0],uid)

            content = {'my': my, 'user_chat':user_chat, 'state':'3'}
            response = render(req, 'chat/chat.html', content)
            return response


        content = {'my': my, 'state':my.state}
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


# find the user chatting with me
def GetUserChat(chat, uid):
    if uid == str(chat.rid.id):
        user_chat = chat.sid
    else:
        user_chat = chat.rid
    return user_chat


#查询某用户信息
def getUserInfo(uid):
    user = leancloud.Object.extend('_User')
    query = user.query
    my = query.get(uid)
    return my


#修改用户状态
def modifyState():
    return



#注册
class Register(View):
    def post(self, req):
        username = req.POST.get('username')
        password = req.POST.get('password')
        name = req.POST.get('name')
        #不能有相同用户名
        test = User.objects.filter(username=username)
        if test.count() > 0:
            return HttpResponse('have the same username')


        user = User(username= username, password= password, name=username)
        user.save()
        context = {'user': user}

        url = reverse('index')
        response = HttpResponseRedirect(url)
        # response.set_cookie('W_NAME', user, max_age=10000000000)
        response.set_cookie('UID', user.id, max_age=10000000000)
        # response.set_cookie('NAME', user.id, max_age=10000000000)
        return response


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
        uid = user[0].id
        if user.count() > 0:
            response = HttpResponseRedirect(reverse('index'))
            # response.set_cookie('wname', user.get('wname'), max_age=10000000000)
            response.set_cookie('UID', uid, max_age=10000000000)
            # response.set_cookie('name', user.get('name'), max_age=10000000000)
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



def chatList(req):
    context = {'user': ''}
    response = render(req, 'message/chat_list.html', context)
    return response


def message(req,uid):

    if req.method == 'POST':
        #发送信息，日后采用异步实现
        return

    context = {'user': ''}
    response = render(req, 'message/message.html', context)
    return response


def userProfile(req,uid):

    #参考 口语桥 profile方法
    #根据objectId查询该用户信息并且展示； 如果是自己有修改按钮修改资料

    #封装获某用户资料方法，其他地方会用到

    return

def my(req):

    context = {'user': ''}
    response = render(req, 'user/my.html', context)
    return response


class ModifyInfo(View):

    def post(self,req):
        return
    def get(self,req):
        user = leancloud.User.get_current()
        content = {
            user: user.get('name'),
            # gender
            # age

        }

        #前端更换图片，异步调用updatePhoto把图片保存到数据库


        response = render(req, 'user/modify_info.html',content)
        return


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







# def api_register2(req):
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
#     return

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
class API_Register(View):
    def get(self, req):
        username = req.GET.get('username')
        password = req.GET.get('password')
        name = req.GET.get('name')
        try:
            user = leancloud.User()
            user.set_username(username)
            user.set_password(password)
            user.name = name
            user.sign_up()
            print (user._attributes)
            info = user._attributes

        except LeanCloudError as e:
            return HttpResponseServerError(e)

        print(leancloud.User.get_current())
        # return HttpResponse(leancloud.User.get_current())
        return HttpResponse(user._attributes)
        # url = GetSiteUrl(req)
        # return HttpResponseRedirect(url)

    def post(self,req):
        return



def apiChatState(req):
    return



def apiLogin(req):
    return






        # def index(request):
#     latest_question_list = Question.objects.order_by('-pub_date')[:5]
#     context = {'latest_question_list': latest_question_list}
#     return render(request, 'polls/index.html', context)