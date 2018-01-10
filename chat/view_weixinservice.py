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
import re

# from  view_func import PostMessge,GetSiteUrl, saveMessage,GetTimeNow, score_today



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
    print(W_NAME)
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
        users = User.objects.filter(W_NAME=W_NAME)
        count = users.count()
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
            user.image_url = info['headimgurl']   # /0, 用户头像，最后一个数值代表正方形头像大小（有0、46、64、96、132数值可选，0代表640*640正方形头像）
            # if info['unionid']:  #不能这样判断
            #     user.unionid = info['unionid']
            user.R_TIME = GetTimeNow()
            user.time_login_today = GetTimeNow()
            user.remind_time = GetTimeNow()
            user.time_gochat = GetTimeNow()
            user.W_NAME = W_NAME
            user.POSITION = info['city'] + ' ' + info['province']
            user.state = 1
            user.save()
            user = get_score_today(user)[0] #首次注册获得今日积分


            #创建plus表
            uid = User.objects.get(W_NAME=W_NAME).id
            # plus = UserPlus()
            # plus.uid_id = uid
            # plus.view = 1
            # plus.time_remind = GetTimeNow()
            # plus.time_service = GetTimeNow()
            # plus.save()

            #以小秘书名义给用户发一条欢迎私信
            temp = '欢迎到九点聊天，点菜单【配对】就可去聊天，给相册放些照片会更受欢迎。 有疑问请给我留言哦...'
            saveMessage( 1, uid, temp,'0','0', GetTimeNow())

            # content = '欢迎到[九点聊天]，点我去完善的个人档案让你更受青睐，用心聊天，开心聊天！'
            content = '欢迎 '+ user.name +' ，点菜单【配对】去聊天 ；点【我的】给相册添加照片.'
            # url = GetSiteUrl(request) + 'modify/' + str(uid) + '/?W_NAME=' + W_NAME
            # replyContent =content + '\n据统计，资料完善的用户更受青睐，请点<a href="' +str(url) + '">完善你的资料</a> 。\n（注：链接是包含隐私信息，切勿转发给TA人）'
            # return getReplyXml(msg,replyContent)


            url = GetSiteUrl(request) + 'my/' + '?W_NAME=' + user.W_NAME
            temp =  GetImageTextXML2(msg,

                                     content,
                                     '',
                                     '',
                                     str(url),#不是为啥，这里不识别，必须先转换string

                                     '每天晚上九点，不聊不散',
                                     '',
                                     '',
                                     str(url),#不是为啥，这里不识别，必须先转换string
            )


            # getReplyXml(msg, content)
            return temp


        else:
            user = User.objects.get(W_NAME=W_NAME)
            # user.save()
            replyContent = '感谢你再次关注我们，祝聊天愉快！'
            # unread = UnreadTips(request,uid)  #未读信息
            # replyContent = replyContent + unread

            #以小秘书名义给用户发一条欢迎私信
            temp = '你一定在想念我们，如对产品有建议请直接回复我；另外，聊天请注意文明用语哦'
            saveMessage( 1, user.id, temp,'0','0',GetTimeNow())

            # url = 'http://' + get_current_site(request).domain + '/register/' + W_NAME +'/'
            # replyContent = '欢迎进入24小时英语角，随时找人练口语、结伴学英语。点链接<a href="' +str(url) + '">花10秒完善资料后进入英语角！</a>   （注：链接是你进入英语角凭证，切勿转发给TA人）'
            #     return getReplyXml(msg,replyContent)
            url = GetSiteUrl(request) + '?W_NAME=' + user.W_NAME
            temp =  GetImageTextXML2(msg,
                                     replyContent,
                                     '',
                                     '',
                                     str(url),#不是为啥，这里不识别，必须先转换string

                                     '每一次相遇都是不一样的体验',
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
            replyContent = '出了点错误，请取消关注，然后再关注试试；若还不行，请联系管理员微信号：40429602'
            return getReplyXml(msg,replyContent)
        user = user[0]

        #点自定义菜单 配对
        if eventMsg == 'CLICK' and eventKey == 'chat':
            url = GetSiteUrl(request) + '?W_NAME=' + user.W_NAME
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


        #点自定义菜单 留言
        if eventMsg == 'CLICK' and eventKey == 'message':
            url =  GetSiteUrl(request)+ 'chat-list/' + '?W_NAME=' + user.W_NAME
            replyContent = '查看留言'
            temp = GetImageTextXML2(msg,
                                    '查看留言',
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
            url = GetSiteUrl(request)+ 'my' + '?W_NAME=' + user.W_NAME
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

            #针对对管理员特殊文本识别，替机器人回复
            if user.id == 817:
                if msgType == 'text':
                    # msgContent = 'dfasdfa @@123'
                    if '@@' in msgContent:
                        id = re.findall(r"@@(.+$)", msgContent)
                        id = int(id[0])
                        msgContent = re.sub(r"@@.*$", "", msgContent)
                        if id == '' or id == None:
                            resMsg = '没有找到相应广告机器人id'
                            return getReplyXml(msg, resMsg)
                        else:
                            user = User.objects.get(id=id)  # 机器人用户
                    # str = "a123b"
                    # print re.findall(r"a(.+?)b", str)  #
                    # 输出['123']


            #下面没有用的，因为自定义菜单默认post一个信息到weixinservice
            if eventMsg == 'VIEW':
                print('view menu')
                return
                # def remindLogin(req, uid):
                #     if uid == None or uid == '':
                #         resMsg = '你未登录，请点击下面菜单【我的 > 登录】'
                #         resMsg = PostFormat(resMsg)
                #         token = GetAccessToken()
                #         # 触发一个post文本给B
                #         PostMessge(token, str(PostText(user_chat.W_NAME, resMsg)))
                #         return temp


            print 'sentweixin'
            if user.state == '1':
                resMsg = '【系统消息】你在空闲状态，可点自定义菜单『配对』匹配聊天。有问题或建议，请加客服微信号:yingyumishu （英语秘书的拼音）'
                return getReplyXml(msg,resMsg)

            if user.state == '2':
                resMsg = '【系统消息】你在自动配对中，系统正在为你匹配到聊天朋友，请留意消息通知。有问题或建议，请加客服微信号:yingyumishu （英语秘书的拼音）'
                return getReplyXml(msg,resMsg)



            #在对话状态，我给微信发信息就是给对方发信息
            if user.state == '3':
                chat = Chat.objects.select_related().filter(Q(rid=user.id) | Q(sid=user.id), close='0')
                chat = chat[0]
                if user.id == chat.rid_id :  #找到对方
                    user_chat = chat.sid
                else:
                    user_chat = chat.rid

                #这里统一刷新chat表 time_end的时间
                chat.time_end = GetTimeNow()
                chat.save()

                #如果被配对的用户是机器人，就要转到我的手机上
                adMode = '0'
                adminUserWname = ''
                textAdd = ' from-' + str(user.id) + '-to-' + str(user_chat.id)
                if (user_chat.id in adUser('0')) or (user_chat.id in adUser('1')):
                    adMode = '1'
                    adminUserWname = 'oe6opwMK08ZI1VzQ4T5ahhO18TGQ'  #


                #不同类型的信息处理不一样，若非文本，在message不保存记录
                if msgType == 'text':
                    if user.name == '' or user.name == ' ' or user.name == None:
                        user.name = 'TA'
                    resMsg = user.name + ': ' + msgContent
                    resMsg = PostFormat(resMsg)
                    # 触发一个post文本给B
                    PostMessge(token, str(PostText(user_chat.W_NAME, resMsg)))

                    #发给机器人的信息转给我
                    if adMode == '1':
                        resMsg = resMsg + textAdd
                        PostMessge(token, str(PostText(adminUserWname, resMsg)))

                    #本地写信息
                    if msgContent != '':
                        saveMessage(user.id, user_chat.id, msgContent, '1','0',GetTimeNow())
                        return ''

                if msgType == 'image':
                    PostMessge(token, str(PostImg(user_chat.W_NAME, MEDIA_ID)))
                    # saveMessage(request, user.id, user_chat.id, '[图片]','1')

                    # 发给机器人的信息转给我
                    if adMode == '1':
                        PostMessge(token, str(PostImg(adminUserWname, MEDIA_ID)))
                        resMsg = '图片' + textAdd
                        PostMessge(token, str(PostText(adminUserWname, resMsg)))

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

                    # 发给机器人的信息转给我
                    if adMode == '1':
                        PostMessge(token, PostVocie(adminUserWname, New_Media_ID))
                        resMsg = '语音' + textAdd
                        PostMessge(token, str(PostText(adminUserWname, resMsg)))

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
                    return ''
                #需要给腾讯服务器返回一个空文本
                # else:
                #     resMsg = ' 暂不支持该信息类型，请发文字、语音、图片'
                #     return getReplyXml(msg,resMsg)






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



def oauth2(request):
    print('oauth2')
    code = request.GET.get('code')
    state = request.GET.get('state')
    print('state:' + state)

    appid = 'wxc5853ef7e04ad6d7'
    secret = 'b4e16bf8f6f1fa35db574df49d7ac137'
    web_access_token_url = "https://api.weixin.qq.com/sns/oauth2/access_token?appid=" + appid + "&secret="+ secret +"&code="+ code+ "&grant_type=authorization_code"

    response = urllib2.urlopen(web_access_token_url)
    html = response.read()
    tokeninfo = json.loads(html)
    W_NAME = tokeninfo['openid'] #openid

    url0 = GetSiteUrl(request) + '?W_NAME=' + W_NAME
    url1 = GetSiteUrl(request) + 'chat-list/' + '?W_NAME=' + W_NAME
    url2 = GetSiteUrl(request) + 'my' + '?W_NAME=' + W_NAME

    if state == '0':
        response = HttpResponseRedirect(url0)
        return response
    if state == '1':
        response = HttpResponseRedirect(url1)
        return response
    if state == '2':
        response = HttpResponseRedirect(url2)
        return response
    return


def CustomMenu(request,para):

    delMenuUrl = "https://api.weixin.qq.com/cgi-bin/menu/delete?access_token="
    createUrl = "https://api.weixin.qq.com/cgi-bin/menu/create?access_token="
    getMenuUrl="https://api.weixin.qq.com/cgi-bin/menu/get?access_token="

    # chat_url = GetSiteUrl(request)
    # chatlist_url = GetSiteUrl(request) +'chat-list/'
    # url2 = GetSiteUrl(request) + 'my' + '?W_NAME=' + W_NAME


    token = GetAccessToken()
    response = 0
    if para == 'create':
        appid = Config.objects.get(key='appid', version=0).value
        redirect_uri = GetSiteUrl(request) + 'oauth2'
        redirect_uri = urllib.quote(redirect_uri,safe='')
        #0,1,2 state用户标记跳转到那个页面, 0首页， 1消息列表， 2我的
        oauth2_url_0 = "https://open.weixin.qq.com/connect/oauth2/authorize?appid=" + appid+ "&redirect_uri=" + redirect_uri + "&response_type=code&scope=snsapi_base&state=0#wechat_redirect"
        oauth2_url_1 = "https://open.weixin.qq.com/connect/oauth2/authorize?appid=" + appid+ "&redirect_uri=" + redirect_uri + "&response_type=code&scope=snsapi_base&state=1#wechat_redirect"
        oauth2_url_2 = "https://open.weixin.qq.com/connect/oauth2/authorize?appid=" + appid+ "&redirect_uri=" + redirect_uri + "&response_type=code&scope=snsapi_base&state=2#wechat_redirect"
        # # url_site = "http://baidu.com"

        print(oauth2_url_0)
        data =  {
         "button":[
             {
                  "type":"view",
                  "name":"配对",
                  "url": oauth2_url_0
              },
             {
                  "type":"view",
                  "name":"留言",
                  "url": oauth2_url_1
              },
             {
                 "type": "view",
                 "name": "我的",
                 "url": oauth2_url_2
             },
            ]
        }
        data = json.dumps(data, ensure_ascii=False)  #原data内中文被dict为unicode，所有要decode一下
        data = str(data)
        url = createUrl + str(token)
        req = urllib2.Request(url, data)
        response = urllib2.urlopen(req)


# #bakup
    if para == 'createOld':
        menu ='''
        {
            "button":[
             {
                 "type":"click",
                 "name":"配对",
                 "key":"chat"
              },
             {
                 "type":"click",
                 "name":"留言",
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



