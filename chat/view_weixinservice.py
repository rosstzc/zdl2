# -*- coding: utf-8 -*-
from __future__ import unicode_literals



from datetime import datetime

from django.http import HttpResponse, HttpRequest, QueryDict
from django.http import HttpResponseRedirect
from django.http import HttpResponseServerError
from django.urls import reverse
from django.views import View

from django.views.decorators.csrf import csrf_exempt
from django.utils.encoding import smart_str
import xml.etree.ElementTree as ET

from django.shortcuts import render
from django.views.generic import View  #通用类
from models import *
from django.db.models import Q

from view_func import *    #公共方法
import  hashlib

from views import GetSiteUrl, OnlineTime, GetUserUrl, saveMessage,GetTimeNow,GetAccessToken
from  view_func import PostMessge


import sys
reload(sys)
sys.setdefaultencoding('utf8')


TOKEN = "zdl"




@csrf_exempt
def handleRequest(request):
    print 'handleRequest'
    if request.method == 'GET':
        print '111'
        #response = HttpResponse(request.GET['echostr'],content_type="text/plain")
        #增加自定义菜单创建部分
        action = request.GET.get('custom')
        if action:
            if CheckPermission(request) == '0':
                return HttpResponse('你没有权限修改')
            info= CustomMenu(request,action)
            return HttpResponse(info)
        response = HttpResponse(checkSignature(request),content_type="text/plain")
        return response

    elif request.method == 'POST':
        #c = RequestContext(request,{'result':responseMsg(request)})
        #t = Template('{{result}}')
        #response = HttpResponse(t.render(c),content_type="application/xml")
        response = HttpResponse(responseMsg(request),content_type="application/xml")
        return response
    else:
        return None

def checkSignature(request):
    global TOKEN
    signature = request.GET.get("signature", None)
    timestamp = request.GET.get("timestamp", None)
    nonce = request.GET.get("nonce", None)
    echoStr = request.GET.get("echostr",None)

    token = TOKEN
    tmpList = [token,timestamp,nonce]
    tmpList.sort()
    tmpstr = "%s%s%s" % tuple(tmpList)
    tmpstr = hashlib.sha1(tmpstr).hexdigest()
    if tmpstr == signature:
        return echoStr
    else:
        return None


def responseMsg(request):
    print 'responseMsg'
    #获取微信post过来的xml，若是新用户就给一个“提示登录的”逻辑， 若是老用户就再给一个逻辑。
    rawStr = smart_str(request.body)
    #rawStr = smart_str(request.POST['XML'])
    msg = paraseMsgXml(ET.fromstring(rawStr))
    eventMsg = msg.get('Event')
    msgType = msg.get('MsgType')
    eventKey = msg.get('EventKey') #自定义菜单增加
    msgPicUrl = msg.get('PicUrl')
    msgContent = msg.get('Content')
    W_NAME =  msg.get('FromUserName')#微信openid，对应着user表的w_name

    #新增 普通信息类型相关参数，语音、视频、地理位置...
    #图片
    msgMediaId = msg.get('MediaId')
    MEDIA_ID = msg.get('MediaId')
    #语音
    msgFormat = msg.get('Format')
    #视频
    msgThumbMediaId = msg.get('ThumbMediaId')
    THUMB_MEDIA_ID = msg.get('ThumbMediaId')
    #地理
    msgLocation_X = msg.get('Location_X')
    msgLocation_Y = msg.get('Location_Y')
    msgScale = msg.get('Scale')
    msgLabel = msg.get('Label')
    #链接
    msgTitle = msg.get('Title')
    msgDescription = msg.get('Description')
    msgUrl = msg.get('Url')




    #如果存事件参数，表明是接收事件推送；表示用户注册
    if eventMsg == 'subscribe':
        print 'subscribe'
        count = User.objects.filter(W_NAME=W_NAME).count()
        if count == 0:

            #通过接口，获取用户信息
            token = GetAccessToken()
            response = GetUserWeixinInfo(token,W_NAME)
            html = response.read()
            info = json.loads(html)

            user = User()
            user.name = info['nickname']
            user.sex = info['sex']
            if info['sex'] == 0:
                user.sex = '2'
            if info['sex'] == 1:
                user.sex = '1'
            else:
                user.sex = '0'
            user.language = info['language']
            user.city = info['city']
            user.province = info['province']
            user.country = info['country']
            # user.image1.name = info['headimgurl']   # /0, 用户头像，最后一个数值代表正方形头像大小（有0、46、64、96、132数值可选，0代表640*640正方形头像）
            # if info['unionid']:  #不能这样判断
            #     user.unionid = info['unionid']
            user.R_TIME = GetTimeNow()
            user.W_NAME = W_NAME
            user.POSITION = info['city'] + ' ' + info['province']
            user.state = 1
            user.save()


            #创建plus表
            uid = User.objects.get(W_NAME=W_NAME).id
            # plus = UserPlus()
            # plus.uid_id = uid
            # plus.view = 1
            # plus.time_remind = GetTimeNow()
            # plus.time_service = GetTimeNow()
            # plus.save()

            #以小秘书名义给用户发一条欢迎私信
            temp = 'Hello, 欢迎加入口语桥大家庭，有任何疑问或想法日后可跟我聊聊喔。查看使用帮助或给我们留言可点右链接： http://m.wsq.qq.com/165500268'
            saveMessage(request, 1, uid, temp)

            content = 'welcome to 24小时口语桥（首次访问点我）'
            # url = GetSiteUrl(request) + 'modify/' + str(uid) + '/?W_NAME=' + W_NAME
            # replyContent =content + '\n据统计，资料完善的用户更受青睐，请点<a href="' +str(url) + '">完善你的资料</a> 。\n（注：链接是包含隐私信息，切勿转发给TA人）'
            # return getReplyXml(msg,replyContent)

            url = GetSiteUrl(request) + 'modify-info/' + '?W_NAME=' + user.W_NAME
            temp =  GetImageTextXML2(msg,

                                     content,
                                     '',
                                     '',
                                     str(url),#不是为啥，这里不识别，必须先转换string

                                     '据统计，资料完善的用户更受青睐，现在去完善资料>>',
                                     '',
                                     'http://ww1.sinaimg.cn/small/489cbcd0gw1elajan2es5j2074074aa3.jpg',
                                     str(url),#不是为啥，这里不识别，必须先转换string
            )
            return temp


        else:
            user = User.objects.get(W_NAME=W_NAME)
            user.save()
            replyContent = '欢迎回到24小时英语角！点菜单:【快聊】或【找角友】找小伙伴聊英语吧'
            uid = User.objects.get(W_NAME=W_NAME).id
            # unread = UnreadTips(request,uid)  #未读信息
            # replyContent = replyContent + unread

            #以小秘书名义给用户发一条欢迎私信
            temp = 'Hello, 欢迎加入口语桥大家庭，有任何疑问或想法日后可跟我聊聊喔。查看使用帮助或给我们留言可点右链接： http://m.wsq.qq.com/165500268'
            saveMessage(request, 1, uid, temp)

            # url = 'http://' + get_current_site(request).domain + '/register/' + W_NAME +'/'
            # replyContent = '欢迎进入24小时英语角，随时找人练口语、结伴学英语。点链接<a href="' +str(url) + '">花10秒完善资料后进入英语角！</a>   （注：链接是你进入英语角凭证，切勿转发给TA人）'
            #     return getReplyXml(msg,replyContent)
            url = GetSiteUrl(request) + 'index/' + '?W_NAME=' + user.W_NAME
            temp =  GetImageTextXML2(msg,
                                     '点我刷新登录',
                                     '',
                                     '',
                                     str(url),#不是为啥，这里不识别，必须先转换string

                                     replyContent,
                                     '',
                                     '',
                                     str(url),#不是为啥，这里不识别，必须先转换string
            )
            return temp


    if eventMsg == 'unsubscribe':
        #用户退订，标记一下状态
        # user = User.objects.get(W_NAME=W_NAME)
        # user.STATE = 0
        # user.save()
        replyContent = '我们会努力做好、准备更好的内容，迎接你下次再到24英语角 :>'
        return getReplyXml(msg,replyContent)
        #如果用户正常回复信息（不管回复什么）


    #先获取用户基本信息，并且更新服务时间
    if W_NAME:
        OPENID = W_NAME
        print 'W_NAME start'
        token = GetAccessToken()
        # print 'token' + str(token)

        #一开始先刷新用户的状态时间
        user = User.objects.filter(W_NAME=W_NAME)


        #插入一个异常处理，用户数据有错
        if user.count() != 1:

            # message = WeiXinMessage()
            # message.uid_id = 1
            # message.content = msgContent
            # message.W_NAME = W_NAME
            # message.time = GetTimeNow()
            # message.save()
            replyContent = '出了点错误，请你联系管理员处理，管理员微信号：zhichao'
            return getReplyXml(msg,replyContent)


        #点自定义菜单 快聊
        if eventMsg == 'CLICK' and eventKey == 'chat':
            url = reverse('index') + '?W_NAME=' + user.W_NAME
            replyContent = '点我登录'
            temp = GetImageTextXML2(msg,
                                    '点我登录',
                                    '',
                                    '',
                                    str(url),  # 不是为啥，这里不识别，必须先转换string

                                    replyContent,
                                    '',
                                    '',
                                    str(url),  # 不是为啥，这里不识别，必须先转换string
                                    )
            return temp


        #点自定义菜单 消息
        if eventMsg == 'CLICK' and eventKey == 'message':
            url = reverse('showMessage') + '?W_NAME=' + user.W_NAME
            replyContent = '查看消息'
            temp = GetImageTextXML2(msg,
                                    '查看消息',
                                    '',
                                    '',
                                    str(url),  # 不是为啥，这里不识别，必须先转换string

                                    replyContent,
                                    '',
                                    '',
                                    str(url),  # 不是为啥，这里不识别，必须先转换string
                                    )
            return temp
        #点自定义菜单 我的
        if eventMsg == 'CLICK' and eventKey == 'my':
            url = reverse('my') + '?W_NAME=' + user.W_NAME
            replyContent = '查看我的'
            temp = GetImageTextXML2(msg,
                                    '查看我的',
                                    '',
                                    '',
                                    str(url),  # 不是为啥，这里不识别，必须先转换string

                                    replyContent,
                                    '',
                                    '',
                                    str(url),  # 不是为啥，这里不识别，必须先转换string
                                    )
            return temp


        #我向微信发信息
        if eventMsg != 'CLICK':
            print 'sentweixin'

            if user.state == '1':
                resMsg = '你在空闲状态，可点自定义菜单『快聊』匹配聊天。若有问题或建议，请加客服微信：XXXXX 交流'
                return getReplyXml(msg,resMsg)

            if user.state == '2':
                resMsg = '你在配对中，系统正在随时为你匹配到聊天朋友，请你留意消息通知通知。若有问题或建议，请加客服微信：XXXXX 交流'
                return getReplyXml(msg,resMsg)

            #在对话状态，我给微信发信息就是给对方发信息
            if user.state == '3':
                chat = Chat.objects.select_related().filter(Q(rid=user.id) | Q(sid=user.id), close='0')
                chat = chat[0]
                if user.id == chat.rid_id :
                    user_chat = chat.sid
                else:
                    user_chat = chat.rid


                #不同类型的信息处理不一样，若非文本，在message不保存记录
                if msgType == 'text':
                    if user.name == '' or user.name == ' ' or user.name == None:
                        user.name = 'TA'
                    resMsg = user.name + ': ' + msgContent
                    resMsg = PostFormat(resMsg)
                    # 触发一个post文本给B
                    PostMessge(token, str(PostText(user_chat.W_NAME, resMsg)))
                    #本地写信息
                    if msgContent != '':
                        saveMessage(request, user.id, user_chat.id, msgContent)
                        return ''

                if msgType == 'image':
                    PostMessge(token, str(PostImg(user_chat.W_NAME, MEDIA_ID)))
                    # saveMessage(request, user.id, user_chat.id, '[图片]')
                    return ''

                if msgType == 'voice':
                    # url = 'http://ke.yuesia.com/getvoice/' +'?token=' + token + '&mid=' + MEDIA_ID
                    # req = urllib2.Request(url)
                    # response = urllib2.urlopen(req)
                    # info = json.load(response)
                    # MEDIA_ID = info['media_id']
                    New_Media_ID = GetNewMediaID(MEDIA_ID)
                    print 'newmediaid'
                    print New_Media_ID
                    # 把该mid Post给用户
                    PostMessge(token, PostVocie(user_chat.W_NAME, New_Media_ID))
                    # message = Message()
                    # message.s_uid_id = uid
                    # message.r_uid = userB_id
                    # message.content = MEDIA_ID
                    # message.cal = 1
                    # message.s_time = GetTimeNow()
                    # message.save()
                    return ''

                if msgType == 'video':
                    TITLE = ''
                    DESCRIPTION = ''
                    PostMessge(token, str(PostVideo(user_chat.W_NAME, MEDIA_ID, THUMB_MEDIA_ID, TITLE, DESCRIPTION)))
                    return ''
                if msgType == 'music':
                    MUSIC_TITLE = ''
                    MUSIC_DESCRIPTION = ''
                    MUSIC_URL = ''
                    HQ_MUSIC_URL = ''
                    THUMB_MEDIA_ID = ''
                    PostMessge(token, str(
                        PostMusic(user_chat.W_NAME, MUSIC_TITLE, MUSIC_DESCRIPTION, MUSIC_URL, HQ_MUSIC_URL,
                                  THUMB_MEDIA_ID)))
                    return ''
                    # 两条图文信息
                if msgType == 'news':
                    t1 = ''
                    d1 = ''
                    u1 = ''
                    p1 = ''

                    t2 = ''
                    d2 = ''
                    u2 = ''
                    p2 = ''
                    PostMessge(token, str(PostTexImg(t1, d1, u1, p1, t2, d2, u2, p2, user_chat.W_NAME)))

                #需要给腾讯服务器返回一个空文本
                return ''








def CheckPermission(req):
#临时通过英语角的id来判断权限,必须少于30才能删除内容
    uid = req.COOKIES.get('UID')
    if not uid or int(uid) > 30:
        return '0'

import requests
def GetNewMediaID(mediaID):
    token = GetAccessToken()
    urlGet = "http://file.api.weixin.qq.com/cgi-bin/media/get?access_token="+ token +"&media_id=" + mediaID
    # 获取音频文件流
    reqGet = requests.get(urlGet)

    from requests_toolbelt import MultipartEncoder
    urlPost = "http://file.api.weixin.qq.com/cgi-bin/media/upload?access_token="+token+"&type=voice"
    m = MultipartEncoder(fields={'media': (mediaID+'.amr', reqGet.content, 'text/plain')})
    # 发送音频流
    r = requests.post(urlPost, data=m,headers={'Content-Type': m.content_type})
    returnText = json.loads(r.text)
    return returnText['media_id']



def CustomMenu(request,para):

    delMenuUrl = "https://api.weixin.qq.com/cgi-bin/menu/delete?access_token="
    createUrl = "https://api.weixin.qq.com/cgi-bin/menu/create?access_token="
    getMenuUrl="https://api.weixin.qq.com/cgi-bin/menu/get?access_token="

    index_url = GetSiteUrl(request) + 'index/' + '?para=custom'
    chatted_url = GetSiteUrl(request) + 'chatted/' + '?para=custom'
    guide_url = GetSiteUrl(request) + 'guide/' + '?para=custom'

    # inbox_url = GetSiteUrl(request) + 'inbox/' + '?para=custom'
    # modify_url = GetSiteUrl(request) + 'modify/' + '?para=custom'

    token = GetAccessToken()
    response = 0
    if para == 'create':
        menu ='''
 {
     "button":[
      {
          "type":"click",
          "name":"快聊",
          "key":"chat"
       },
      {
          "type":"click",
          "name":"消息",
          "key":"message"
       },
        {
          "type":"click",
          "name":"我的",
          "key":"my"
       },
        ]
 }
            '''
        print 'customGet'
        url = createUrl + str(token)
        req = urllib2.Request(url, menu)
        response = urllib2.urlopen(req)

    elif para == 'del':
        url = delMenuUrl + str(token)
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)

    elif para == 'get':
        url = getMenuUrl + str(token)
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)

    #打印微信返回错误码
    html = response.read()
    info = json.loads(html)
    # token=tokeninfo['access_token']

    return html



def GetUserWeixinInfo(token,OPENID):
    url = 'https://api.weixin.qq.com/cgi-bin/user/info?access_token=' + str(token) + '&openid=' + str(OPENID)
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    return response














#------------针对英语角服务号的设计 2014.9.7   以上




# 这方法用于解析xml
def paraseMsgXml(rootelem):
    msg = {}
    if rootelem.tag == 'xml':
        for child in rootelem:
            msg[child.tag] = smart_str(child.text)
    return msg



def GetMusicXML(msg,title,desc,music_url,hq_music_url,image):
    extTpl ="<xml>" \
            "<ToUserName><![CDATA[%s]]></ToUserName>" \
            "<FromUserName><![CDATA[%s]]></FromUserName>" \
            "<CreateTime>%s</CreateTime>" \
            "<MsgType><![CDATA[music]]></MsgType>" \
            "<Music>" \
            "<Title><![CDATA[%s]]></Title>" \
            "<Description><![CDATA[%s]]></Description>" \
            "<MusicUrl><![CDATA[%s]]></MusicUrl>" \
            "<HQMusicUrl><![CDATA[%s]]></HQMusicUrl>" \
            "<ThumbMediaId><![CDATA[%s]]></ThumbMediaId>" \
            "</Music>" \
            "</xml>"
    extTpl = extTpl % (msg['FromUserName'],
                       msg['ToUserName'],
                       str(int(time.time())),

                       title,
                       desc,
                       music_url,
                       hq_music_url,
                       image,
    )
    return extTpl


# 这方法是构建回复的xml内容模板，下面是一个text消息的模板
def getReplyXml(msg,replyContent):
    extTpl = "<xml>" \
             "<ToUserName><![CDATA[%s]]></ToUserName>" \
             "<FromUserName><![CDATA[%s]]></FromUserName>" \
             "<CreateTime>%s</CreateTime>" \
             "<MsgType><![CDATA[%s]]></MsgType>" \
             "<Content><![CDATA[%s]]></Content>" \
             "</xml>"
    extTpl = extTpl % (msg['FromUserName'],
                       msg['ToUserName'],
                       str(int(time.time())),
                       'text',
                       replyContent)
    return extTpl


def GetImageTextXML1(msg, title1,desc1,img_url1,url1):
    extTpl ="<xml>" \
            "<ToUserName><![CDATA[%s]]></ToUserName>" \
            "<FromUserName><![CDATA[%s]]></FromUserName> " \
            "<CreateTime>%s</CreateTime>" \
            "<MsgType><![CDATA[%s]]></MsgType>" \
            "<ArticleCount>%s</ArticleCount>" \
            "<Articles>" \
            "<item>" \
            "<Title><![CDATA[%s]]></Title>" \
            "<Description><![CDATA[%s]]></Description>" \
            "<PicUrl><![CDATA[%s]]></PicUrl>" \
            "<Url><![CDATA[%s]]></Url>" \
            "</item>" \
            "</Articles>" \
            "</xml>" \

    ArticleCount = 1
    extTpl = extTpl % (msg['FromUserName'],
                       msg['ToUserName'],
                       str(int(time.time())),
                       'news',
                       ArticleCount,
                       #第一个图片信息
                       title1,#'欢迎加入24英语角,跟大伙一起学英语，练口语，很有feel！点本信息马上进入英语角>>',# 1标题信息
                       desc1, #2描述内容
                       img_url1,#3图片url
                       url1,  #4连接url
    )
    return extTpl



def GetImageTextXML2(msg, title1,desc1,img_url1,url1,title2,desc2,img_url2,url2):
    extTpl ="<xml>" \
            "<ToUserName><![CDATA[%s]]></ToUserName>" \
            "<FromUserName><![CDATA[%s]]></FromUserName> " \
            "<CreateTime>%s</CreateTime>" \
            "<MsgType><![CDATA[%s]]></MsgType>" \
            "<ArticleCount>%s</ArticleCount>" \
            "<Articles>" \
            "<item>" \
            "<Title><![CDATA[%s]]></Title>" \
            "<Description><![CDATA[%s]]></Description>" \
            "<PicUrl><![CDATA[%s]]></PicUrl>" \
            "<Url><![CDATA[%s]]></Url>" \
            "</item>" \
            "<item>" \
            "<Title><![CDATA[%s]]></Title>" \
            "<Description><![CDATA[%s]]></Description>" \
            "<PicUrl><![CDATA[%s]]></PicUrl>" \
            "<Url><![CDATA[%s]]></Url>" \
            "</item>" \
            "</Articles>" \
            "</xml>" \

    ArticleCount = 2
    extTpl = extTpl % (msg['FromUserName'],
                       msg['ToUserName'],
                       str(int(time.time())),
                       'news',
                       ArticleCount,
                       #第一个图片信息
                       title1,#'欢迎加入24英语角,跟大伙一起学英语，练口语，很有feel！点本信息马上进入英语角>>',# 1标题信息
                       desc1, #2描述内容
                       img_url1,#3图片url
                       url1,  #4连接url

                       #第二个图片信息
                       title2,# 1标题信息
                       desc2, #2描述内容
                       img_url2,#3图片url
                       url2,  #4连接url
    )
    return extTpl



def GetImageTextXML3(msg, title1,desc1,img_url1,url1,title2,desc2,img_url2,url2,title3,desc3,img_url3,url3):
    extTpl ="<xml>" \
            "<ToUserName><![CDATA[%s]]></ToUserName>" \
            "<FromUserName><![CDATA[%s]]></FromUserName> " \
            "<CreateTime>%s</CreateTime>" \
            "<MsgType><![CDATA[%s]]></MsgType>" \
            "<ArticleCount>%s</ArticleCount>" \
            "<Articles>" \
            "<item>" \
            "<Title><![CDATA[%s]]></Title>" \
            "<Description><![CDATA[%s]]></Description>" \
            "<PicUrl><![CDATA[%s]]></PicUrl>" \
            "<Url><![CDATA[%s]]></Url>" \
            "</item>" \
            "<item>" \
            "<Title><![CDATA[%s]]></Title>" \
            "<Description><![CDATA[%s]]></Description>" \
            "<PicUrl><![CDATA[%s]]></PicUrl>" \
            "<Url><![CDATA[%s]]></Url>" \
            "</item>" \
            "<item>" \
            "<Title><![CDATA[%s]]></Title>" \
            "<Description><![CDATA[%s]]></Description>" \
            "<PicUrl><![CDATA[%s]]></PicUrl>" \
            "<Url><![CDATA[%s]]></Url>" \
            "</item>" \
            "</Articles>" \
            "</xml>" \

    ArticleCount = 3
    extTpl = extTpl % (msg['FromUserName'],
                       msg['ToUserName'],
                       str(int(time.time())),
                       'news',
                       ArticleCount,
                       #第一个图片信息
                       title1,#'欢迎加入24英语角,跟大伙一起学英语，练口语，很有feel！点本信息马上进入英语角>>',# 1标题信息
                       desc1, #2描述内容
                       img_url1,#3图片url
                       url1,  #4连接url

                       #第二个图片信息
                       title2,# 1标题信息
                       desc2, #2描述内容
                       img_url2,#3图片url
                       url2,  #4连接url

                       # #第二个图片信息
                       title3,# 1标题信息
                       desc3, #2描述内容
                       img_url3,#3图片url
                       url3,  #4连接url
    )
    return extTpl


def GetImageTextXML4(msg, title1,desc1,img_url1,url1,title2,desc2,img_url2,url2,title3,desc3,img_url3,url3,title4,desc4,img_url4,url4):
    extTpl ="<xml>" \
            "<ToUserName><![CDATA[%s]]></ToUserName>" \
            "<FromUserName><![CDATA[%s]]></FromUserName> " \
            "<CreateTime>%s</CreateTime>" \
            "<MsgType><![CDATA[%s]]></MsgType>" \
            "<ArticleCount>%s</ArticleCount>" \
            "<Articles>" \
            "<item>" \
            "<Title><![CDATA[%s]]></Title>" \
            "<Description><![CDATA[%s]]></Description>" \
            "<PicUrl><![CDATA[%s]]></PicUrl>" \
            "<Url><![CDATA[%s]]></Url>" \
            "</item>" \
            "<item>" \
            "<Title><![CDATA[%s]]></Title>" \
            "<Description><![CDATA[%s]]></Description>" \
            "<PicUrl><![CDATA[%s]]></PicUrl>" \
            "<Url><![CDATA[%s]]></Url>" \
            "</item>" \
            "<item>" \
            "<Title><![CDATA[%s]]></Title>" \
            "<Description><![CDATA[%s]]></Description>" \
            "<PicUrl><![CDATA[%s]]></PicUrl>" \
            "<Url><![CDATA[%s]]></Url>" \
            "</item>" \
            "<item>" \
            "<Title><![CDATA[%s]]></Title>" \
            "<Description><![CDATA[%s]]></Description>" \
            "<PicUrl><![CDATA[%s]]></PicUrl>" \
            "<Url><![CDATA[%s]]></Url>" \
            "</item>" \
            "</Articles>" \
            "</xml>" \

    ArticleCount = 4
    extTpl = extTpl % (msg['FromUserName'],
                       msg['ToUserName'],
                       str(int(time.time())),
                       'news',
                       ArticleCount,
                       #第一个图片信息
                       title1,#'欢迎加入24英语角,跟大伙一起学英语，练口语，很有feel！点本信息马上进入英语角>>',# 1标题信息
                       desc1, #2描述内容
                       img_url1,#3图片url
                       url1,  #4连接url

                       #第二个图片信息
                       title2,# 1标题信息
                       desc2, #2描述内容
                       img_url2,#3图片url
                       url2,  #4连接url

                       #第三个图片信息
                       title3,# 1标题信息
                       desc3, #2描述内容
                       img_url3,#3图片url
                       url3,  #4连接url

                       #第四个图片信息
                       title4,# 1标题信息
                       desc4, #2描述内容
                       img_url4,#3图片url
                       url4,  #4连接url

    )
    return extTpl



def GetImageTextXML5(msg, title1,desc1,img_url1,url1,title2,desc2,img_url2,url2,title3,desc3,img_url3,url3,title4,desc4,img_url4,url4,title5,desc5,img_url5,url5):
    extTpl ="<xml>" \
            "<ToUserName><![CDATA[%s]]></ToUserName>" \
            "<FromUserName><![CDATA[%s]]></FromUserName> " \
            "<CreateTime>%s</CreateTime>" \
            "<MsgType><![CDATA[%s]]></MsgType>" \
            "<ArticleCount>%s</ArticleCount>" \
            "<Articles>" \
            "<item>" \
            "<Title><![CDATA[%s]]></Title>" \
            "<Description><![CDATA[%s]]></Description>" \
            "<PicUrl><![CDATA[%s]]></PicUrl>" \
            "<Url><![CDATA[%s]]></Url>" \
            "</item>" \
            "<item>" \
            "<Title><![CDATA[%s]]></Title>" \
            "<Description><![CDATA[%s]]></Description>" \
            "<PicUrl><![CDATA[%s]]></PicUrl>" \
            "<Url><![CDATA[%s]]></Url>" \
            "</item>" \
            "<item>" \
            "<Title><![CDATA[%s]]></Title>" \
            "<Description><![CDATA[%s]]></Description>" \
            "<PicUrl><![CDATA[%s]]></PicUrl>" \
            "<Url><![CDATA[%s]]></Url>" \
            "</item>" \
            "<item>" \
            "<Title><![CDATA[%s]]></Title>" \
            "<Description><![CDATA[%s]]></Description>" \
            "<PicUrl><![CDATA[%s]]></PicUrl>" \
            "<Url><![CDATA[%s]]></Url>" \
            "</item>" \
            "<item>" \
            "<Title><![CDATA[%s]]></Title>" \
            "<Description><![CDATA[%s]]></Description>" \
            "<PicUrl><![CDATA[%s]]></PicUrl>" \
            "<Url><![CDATA[%s]]></Url>" \
            "</item>" \
            "</Articles>" \
            "</xml>" \

    ArticleCount = 5
    extTpl = extTpl % (msg['FromUserName'],
                       msg['ToUserName'],
                       str(int(time.time())),
                       'news',
                       ArticleCount,
                       #第一个图片信息
                       title1,#'欢迎加入24英语角,跟大伙一起学英语，练口语，很有feel！点本信息马上进入英语角>>',# 1标题信息
                       desc1, #2描述内容
                       img_url1,#3图片url
                       url1,  #4连接url

                       #第二个图片信息
                       title2,# 1标题信息
                       desc2, #2描述内容
                       img_url2,#3图片url
                       url2,  #4连接url

                       #第三个图片信息
                       title3,# 1标题信息
                       desc3, #2描述内容
                       img_url3,#3图片url
                       url3,  #4连接url

                       #第四个图片信息
                       title4,# 1标题信息
                       desc4, #2描述内容
                       img_url4,#3图片url
                       url4,  #4连接url

                       #第五个图片信息
                       title5,# 1标题信息
                       desc5, #2描述内容
                       img_url5,#3图片url
                       url5,  #4连接url
    )
    return extTpl



