#coding=utf-8

from django.http import HttpResponse, HttpResponseRedirect,HttpRequest
from django.template import RequestContext, Template
from django.views.decorators.csrf import csrf_exempt
from django.utils.encoding import smart_str, smart_unicode
from django.shortcuts import render_to_response

from django.contrib.sites.models import get_current_site
from  models import User,Message, UserPlus, WeiXinMessage, ChatRecord,ChatBegin,Ads,AdView

import xml.etree.ElementTree as ET
import urllib,urllib2,time,hashlib, json
import  datetime
from django.db.models import Q          #把多选的list转化为适合filter的字典格式
from .func import *

from weixincorner.views import GetSiteUrl, OnlineTime, GetUserDetail,GetUserUrl,DataMoveSingle,UnreadGroupMsg, \
    SaveMessage,ModState,UserLink,GetUser,UserLinkPost,PostFormat,UnreadTips, UpdateUserOnlineTime, \
    GetTimeNow,GetAccessToken,ShowAds,GetNewMediaID



import sys
reload(sys)
sys.setdefaultencoding('utf8')


TOKEN = "kaikouxue"




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
    rawStr = smart_str(request.raw_post_data)
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
            user.NAME = info['nickname']
            user.SEX = info['sex']
            if info['sex'] == 0:
                user.SEX = 3
            user.language = info['language']
            user.city = info['city']
            user.province = info['province']
            user.country = info['country']
            user.IMG = info['headimgurl']   # /0, 用户头像，最后一个数值代表正方形头像大小（有0、46、64、96、132数值可选，0代表640*640正方形头像）
            # if info['unionid']:  #不能这样判断
            #     user.unionid = info['unionid']
            user.R_TIME = GetTimeNow()
            user.W_NAME = W_NAME
            user.POSITION = info['city'] + ' ' + info['province']
            user.STATE = 2
            user.state_service = 1
            user.save()


            #创建plus表
            uid = User.objects.get(W_NAME=W_NAME).id
            plus = UserPlus()
            plus.uid_id = uid
            plus.view = 1
            plus.time_remind = GetTimeNow()
            plus.time_service = GetTimeNow()
            plus.save()

            #以小秘书名义给用户发一条欢迎私信
            temp = 'Hello, 欢迎加入口语桥大家庭，有任何疑问或想法日后可跟我聊聊喔。查看使用帮助或给我们留言可点右链接： http://m.wsq.qq.com/165500268'
            SaveMessage(request, 1, uid, temp)

            content = 'welcome to 24小时口语桥（首次访问点我）'
            # url = GetSiteUrl(request) + 'modify/' + str(uid) + '/?W_NAME=' + W_NAME
            # replyContent =content + '\n据统计，资料完善的用户更受青睐，请点<a href="' +str(url) + '">完善你的资料</a> 。\n（注：链接是包含隐私信息，切勿转发给TA人）'
            # return getReplyXml(msg,replyContent)

            url = GetSiteUrl(request) + 'modify/' + '?W_NAME=' + user.W_NAME
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
            SaveMessage(request, 1, uid, temp)

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
            message = WeiXinMessage()
            message.uid_id = 1
            message.content = msgContent
            message.W_NAME = W_NAME
            message.time = GetTimeNow()
            message.save()
            replyContent = '出了点错误，请你联系管理员处理，管理员微信号：zhichao'
            return getReplyXml(msg,replyContent)

        user = user[0]
        uid = user.id
        state = user.state_service
        myname = user.NAME
        url = GetSiteUrl(request) + 'user/' + str(uid)
        mylink = '<a href="' + url + '">'+ user.NAME +'</a>'

        #减少写数据库的次数
        start = OnlineTimeMinutes(1)
        if user.TIME < start:
            user.TIME = GetTimeNow()
        user.save()

        #减少写数据库的次数
        temp = user.userplus_set.filter(uid_id=uid)[0]
        start = OnlineTimeMinutes(30)
        #补全那些没有time_service的用户
        if temp.time_service == '' or temp.time_service == None:
            temp.time_service = GetTimeNow()
            temp.save()
        if temp.time_service < start:
            temp.time_service = GetTimeNow()
            temp.save()



        # userPlus = UserPlus.objects.get(uid_id=uid)
        # userPlus.time_service = GetTimeNow()
        # userPlus.save()


        #
        # if eventKey == 'modify':
        #     user.STATE = '1'
        #     user.save()
        #     replyContent = '请回复一张照片作为头像。\n\n（如果暂不上传照片，请点菜单【进入】填写资料后进入英语角）' \
        #                    '\n\n 温馨提示：' \
        #                    '\n 1)有照片的人会获得更多交流机会.' \
        #                    '\n 2)严禁情色、暴力、政治等违反中国法规的图片，一经发现直接封ID。'
        #     return getReplyXml(msg,replyContent)
        #
        #
        # if user.STATE == '1' and msgType == 'text':
        #     if  msgType == 'text':
        #         user.NAME = msgContent
        #         user.save()
        #     replyContent = '请回复一张照片作为头像。\n\n（如果暂不上传照片，请点菜单【进入】填写资料后进入英语角）' \
        #                    '\n\n 温馨提示：' \
        #                    '\n 1)有照片的人会获得更多交流机会.' \
        #                    '\n 2)严禁情色、暴力、政治等违反中国法规的图片，一经发现直接封ID。'
        #     return getReplyXml(msg,replyContent)


        #不上传头像，而点了【进入】菜单
        # if user.STATE == '1' and eventKey == 'getin':
        #     user.STATE ='2'
        #     user.save()
        #     url = GetSiteUrl(request) + 'modify/' + str(uid) + '/?W_NAME=' + W_NAME
        #     replyContent = '为了让其他角友更乐意找你聊天，请点<a href="' +str(url) + '">链接完善你的资料</a>后点【进入】菜单 。\n（注：链接是你进入英语角凭证，切勿转发给TA人）'
        #     #在资料提交修改后，弹出提示让用户到菜单
        #     return getReplyXml(msg,replyContent)

        # #上传头像
        # if user.STATE == '1' and msgType == 'image':
        #     user.IMG = msgPicUrl
        #     user.STATE = '2'
        #     user.save()
        #     DataMoveSingle(W_NAME)
        #     url = GetSiteUrl(request) + 'modify/' + str(uid) + '/?W_NAME=' + W_NAME
        #     replyContent = '上传成功，据统计人们更乐意跟资料完整的人对话，请点<a href="' +str(url) + '">链接完善你的资料</a> 。\n（注：链接是你进入英语角凭证，切勿转发给TA人）'
        #     #在资料提交修改后，弹出提示让用户到菜单
        #     return getReplyXml(msg,replyContent)


        #如果点自定义查单
        if eventMsg == 'CLICK' or eventMsg == 'VIEW' :
            msgContent = eventKey

        #点菜单“进入”
        if eventMsg == 'CLICK' and msgContent == 'getin':
            print 'getin'


            #如果当前为被“邀请中”，那么建立对话
            if state == 2:
                result = ChatBegin.objects.filter(Q(rid=uid)|Q(sid=uid),mode=2,close=0).order_by('-id')[0]

                if result.rid == uid:
                    #用户是B方,建立对话,写入chatRecord表
                    record = ChatRecord()
                    record.sid_id = result.sid
                    record.rid_id = result.rid
                    record.mode = 2
                    record.time = GetTimeNow()
                    record.save()

                    #把初始表记录关闭
                    result.close = 1
                    result.save()

                    ModState(uid, 4)
                    ModState(result.sid, 4)
                    #post给邀请方
                    resMsgA = myname +' 已接受你的邀请，你们可以开始对话 :> \n('+ mylink + '的主页)'
                    # resMsgA = ''
                    resMsgA = PostFormat(resMsgA)
                    userA = User.objects.get(id=result.sid)
                    PostMessge(token,str(PostText(userA.W_NAME,resMsgA)))

                    userb = GetUser(request,result.sid)
                    resMsgB = '你已接受"'+ userb.link + '"的对话邀请，你们可以开始对话 :> '

                    return getReplyXml(msg,resMsgB)

                if result.sid == uid:
                    #用户是A方
                    link = UserLink(request,result.rid)

                    resMsg = '正在等待' + str(link) + '的回应，请稍等！,终止“邀请”请点菜单【退出】'
                    resMsg = resMsg + ShowAds(request,uid)
                    return getReplyXml(msg,resMsg)


            #如果是“配对中”、“对话中”，保持状态
            if state == 3 or state == 4:
                if state == 3:
                    # resMsg = '你正在“随机配对中”，你可以点菜单\n【快聊】刷新或点菜单【退出】终止随机匹配.'
                    resMsg = '正在为你匹配中，请稍等，你也可点菜单:\n【快聊】刷新\n【找角友】对话\n【退出】终止'
                    resMsg = resMsg + UnreadTips(request,uid) + ShowAds(request,uid)
                    return getReplyXml(msg,resMsg)
                if state == 4:
                    link = GetChatUserBLink(request,uid)
                    resMsg = '你正在与角友' + link + '对话中，终止可点菜单【退出】.'
                    resMsg = resMsg + ShowAds(request,uid)
                    return getReplyXml(msg,resMsg)

            #如果为“不打扰”、“离开”、“空闲”，修改状态为“空闲”
            else:
                url = GetSiteUrl(request)
                resMsg = '欢迎进入24小时<a href="'+ url + '">口语桥</a>！点菜单:\n【快聊】或【找角友】\n找个小伙伴聊英语吧'
                unread = UnreadTips(request,uid)  #未读信息
                resMsg = resMsg + unread
                resMsg = resMsg + ShowAds(request,uid)
                result = User.objects.get(id=uid)
                result.state_service = 1
                result.save()
                return getReplyXml(msg,resMsg)


        if eventMsg == 'CLICK' and msgContent == 'random':


            #若为对话中，提示用户正在对话，需先退出
            if state == 4:
                link = GetChatUserBLink(request,uid)
                resMsg = '你正与角友' + link + '“对话”中，若要重新找人，请菜单【退出】。'
                resMsg = resMsg + ShowAds(request,uid)
                return getReplyXml(msg,resMsg)

            #若为邀请中，提示用户先退出
            if state == 2:
                # resMsg = '你当前在“邀请”状态，若要重新找人，请先点菜单【退出】。'
                resMsg = GetInviteUserB(request,uid)
                resMsg = resMsg + ShowAds(request,uid)
                return getReplyXml(msg,resMsg)

            #判断用户是否填写资料，若没有，就提示对方要求资料完善
            if user.AUDIO == '' or user.AUDIO == None:
                url = GetSiteUrl(request) + 'modify/'
                resMsg = '对方要求有“个人简介”的用户才可联系，建议你先去<a href="'+ url +'">完善你的资料</a>'
                resMsg = resMsg + ShowAds(request,uid)
                return getReplyXml(msg,resMsg)


            #若为配对中，把之前记录关闭，新开记录，下面已经包含; 其他状态如空闲，不打扰，离开，直接按本流程处理
            print 'random'
            #到chat按时间倒序找最近触发“快聊”的人;并且今天聊过的不聊
            #查找最近1小时进入“随机”的用户
            start = OnlineTime(1)
            result = ChatBegin.objects.filter(mode=1,close=0,time__gt=start).exclude(sid=uid).order_by('-id')


            #查找最近8小时内与用户聊过的用户
            start = OnlineTime(8)
            temp = ChatRecord.objects.filter(Q(sid_id=uid)|Q(rid_id=uid),time__gt=start)


            rid = 0
            # 找到最近并且没有聊过的人
            for i in result:
                k = 0
                for j in temp:
                    if i.sid == j.sid_id or i.sid == j.rid_id:
                        k = k + 1
                if k == 0:
                    rid = i.sid
                    break

            #修改状态，没匹配到的
            if rid == 0 :
                print 'random_not_match'

                #创建一条begin记录，先把之前的记录close
                ChatBegin.objects.filter(sid=uid,mode=1,close=0).update(close=1)

                temp = ChatBegin()
                temp.sid = uid
                temp.mode = 1
                temp.time = GetTimeNow()
                temp.save()

                ModState(uid, 3)
                resMsg = '角友都在忙喔，系统已把你加入排队，请稍等。\n 若一直没有配对提醒，可点菜单:\n【快聊】刷新\n【找角友】邀请角友对话'
                unread = UnreadTips(request,uid)  #未读信息
                resMsg = resMsg + unread + ShowAds(request,uid)
                return getReplyXml(msg,resMsg)
            #匹配到的
            else:
                print 'random_match'
                #把B方初始表记录close
                ChatBegin.objects.filter(sid=rid,mode=1,close=0).update(close=1)

                #创建一条成功随机配对记录
                chat = ChatRecord()
                chat.sid_id = uid
                chat.rid_id = rid
                chat.time = GetTimeNow()
                chat.mode = 1
                chat.save()
                ModState(uid, 4)
                ModState(rid, 4)

                # B方收到提醒
                userb = GetUser(request,uid)
                resMsg = '为你匹配到“'+ userb.NAME +'”,回复微信即跟TA对话. \n('+ userb.link + '的主页)'  #是否str(link)没关系的
                resMsg = PostFormat(resMsg)
                userB = User.objects.get(id=rid)
                PostMessge(token,str(PostText(userB.W_NAME,resMsg)))

                #A方收到提醒
                link = UserLink(request,rid)
                resMsg = '为你匹配到“'+ link +'”,回复微信即跟TA对话.'
                return getReplyXml(msg,resMsg)


        if eventMsg == 'CLICK' and msgContent == 'state':

            resMsg = ''
            #  空闲中
            if state == 1:
                resMsg = '你当前“空闲”中，可点菜单:\n【快聊】随机对话\n【找角友】邀请对话'
                #邀请中
            if state == 2:
                # resMsg = '你当前对话“邀请”中，如果一直未得到回应，可点菜单【退出】。'
                resMsg = GetInviteUserB(request,uid)
                #配对中
            if state == 3:
                resMsg = '正在帮你“配对”中，若一会儿未匹配成功，可点菜单【快聊】刷新'
                #在聊
            if state == 4:
                link = GetChatUserBLink(request,uid)
                resMsg = '你正在与角友'+ link +'“对话”中；终止对话请点菜单【退出】'
                #不打扰
            if state == 5:
                resMsg = '你在“不打扰”状态，其他人不能邀请，你可以点菜单【进入】英语角'
                #离开
            if state == 6:
                resMsg = '你当前在“离开”状态，可点菜单【进入】英语角'
            unread = UnreadTips(request,uid)  #未读信息
            resMsg = resMsg + unread + ShowAds(request,uid)
            return getReplyXml(msg,resMsg)



        if eventMsg == 'CLICK' and msgContent == 'getout':

            #  空闲中
            if state == 1:
                ModState(uid,5)
                resMsg = '已进入“不打扰”状态，其他人不能邀请你；可点菜单【进入】英语角.'
                unread = UnreadTips(request,uid)  #未读信息
                ad_link = ShowAds(request,uid)
                resMsg = resMsg + unread + ad_link

                ChatClose(uid) #增加异常处理
                temp = getReplyXml(msg,resMsg)
                #广告专用反馈
                # temp = GetResponseXML2(msg,resMsg)
                return temp

                #邀请中
            if state == 2:
                result = ChatBegin.objects.filter(Q(rid=uid)|Q(sid=uid),mode=2,close=0).order_by('-id')
                if result.count() > 0:
                    result = result[0]
                    result.close = 1
                    result.save()
                    ModState(result.sid,1)
                    ModState(result.rid,1)
                else:
                    ModState(uid,1)
                    resMsg = '已进入“空闲”状态，可点菜单【快聊】或【找角友】聊英语。'
                    resMsg = resMsg + ShowAds(request,uid)
                    ChatClose(uid) #增加异常处理
                    return getReplyXml(msg,resMsg)

                #用户为发起方，退出
                if uid == result.sid:
                    #不用提示对话，自己退出即可
                    resMsg = '已退出邀请，可点【快聊】或【找角友】对话。'
                    resMsg = resMsg + ShowAds(request,uid)
                    return getReplyXml(msg,resMsg)
                else:
                    userb = GetUser(request,result.rid)
                    resMsg = '"' + userb.NAME + '"在忙事情，暂时未能跟你聊英语，你可邀请其他角友对话。\n('+ userb.link + '的主页)'
                    resMsg = PostFormat(resMsg)
                    user = User.objects.get(id=result.sid)
                    PostMessge(token,str(PostText(user.W_NAME,resMsg)))

                    resMsg = '已退出邀请，若不想被打扰，可点【退出】进入“不打扰状态”'
                    resMsg = resMsg + ShowAds(request,uid)
                    return getReplyXml(msg,resMsg)

            #配对中
            if state == 3:
                result = ChatBegin.objects.filter(Q(rid=uid)|Q(sid=uid),mode=1,close=0).order_by('-id')
                if result.count() > 0:
                    result = result[0]
                    result.close = 1
                    result.save()
                ModState(uid,1)
                resMsg = '你在“空闲”状态，你可以点菜单:\n【快聊】随机对话\n【找角友】邀请对话\n【退出】不受打扰'
                unread = UnreadTips(request,uid)  #未读信息
                resMsg = resMsg + unread + ShowAds(request,uid)
                ChatClose(uid) #增加异常处理
                return getReplyXml(msg,resMsg)

            #在聊
            if state == 4:
                result = ChatRecord.objects.filter(Q(rid_id=uid)|Q(sid_id=uid),close=0).order_by('-id')
                if result.count() > 0:
                    result = result[0]
                    result.close = 1
                    result.save()
                    ModState(result.sid_id,1)
                    ModState(result.rid_id,1)
                else:
                    #异常情况还是退出了
                    ModState(uid,1)
                    resMsg = '已进入“空闲”状态，可点菜单【快聊】或【找角友】聊英语。'
                    ChatClose(uid) #增加异常处理
                    return getReplyXml(msg,resMsg)


                #现在发起方永远uid的那个人，现在是找rid是谁
                if uid == result.sid_id:
                    sid = uid
                    rid = result.rid_id
                else:
                    sid = uid
                    rid = result.sid_id

                #post给B方
                userb = GetUser(request,sid)
                resMsg = '"' + userb.NAME + '"终止了对话，重新找角友可点菜单:\n【快聊】随机对话\n【找角友】对话'
                resMsg = PostFormat(resMsg)
                user = User.objects.get(id=rid)
                PostMessge(token,str(PostText(user.W_NAME,resMsg)))


                #回应给A方
                link = UserLink(request,rid)
                resMsg = '已终止与'+ str(link) +'的对话，重新找角友可点菜单:\n【快聊】随机对话\n【找角友】对话'
                ChatClose(uid) #增加异常处理
                return getReplyXml(msg,resMsg)


                #不打扰
            if state == 5 or state == 6:
                ModState(uid,6)
                resMsg = '你已进入“离开”状态，你将接收不到我们任何提醒信息，可点菜单【进入】英语角.'
                unread = UnreadTips(request,uid)  #未读信息
                resMsg = resMsg + unread
                ChatClose(uid) #增加异常处理
                return getReplyXml(msg,resMsg)


                # if eventMsg == 'CLICK' and msgContent == 'findfriend':
                # result = User.objects.exclude(id=uid).exclude(state_service=4).exclude(state_service=3).exclude(state_service=5).exclude(state_service=6)
                # result = result.exclude(NAME='').exclude(AUDIO='').exclude(IMG='')
                # start = OnlineTime(2)
                # temp = result.filter(TIME__gt=start)
                # if result.filter(TIME__gt=start).count() > 4:
                #     result = temp.order_by('?')
                # else:
                #     result = result.order_by('-TIME')[:20]
                #     if result.count() < 4:
                #         result = User.objects.order_by('-TIME')[:20]
                # for i in result:
                #     i.SEX = i.get_SEX_display()
                #     i.AUDIO = i.NAME + ' ' + i.SEX + ' ' + i.AUDIO
                #
                # url0 = GetSiteUrl(request) + 'user/'  + str(result[0].id) + '?W_NAME=' + W_NAME
                # url1 = GetSiteUrl(request) + 'user/'  + str(result[1].id) + '?W_NAME=' + W_NAME
                # url2 = GetSiteUrl(request) + 'user/'  + str(result[2].id) + '?W_NAME=' + W_NAME
                # url3 = GetSiteUrl(request) + 'user/'  + str(result[3].id) + '?W_NAME=' + W_NAME
                # url4 = GetSiteUrl(request) + 'index/' + '?W_NAME=' + W_NAME
                #
                # temp =  GetImageTextXML5(msg,
                #
                #                          result[0].AUDIO,
                #                          '',
                #                          result[0].IMG,
                #                          str(url0),#不是为啥，这里不识别，必须先转换string
                #
                #                          result[1].AUDIO,
                #                          '',
                #                          result[1].IMG,
                #                          str(url1),#不是为啥，这里不识别，必须先转换string
                #
                #                          result[2].AUDIO,
                #                          '',
                #                          result[2].IMG,
                #                          str(url2),#不是为啥，这里不识别，必须先转换string
                #
                #                          result[3].AUDIO,
                #                          '',
                #                          result[3].IMG,
                #                          str(url3),#不是为啥，这里不识别，必须先转换string
                #
                #                          '点击我，查看更多角友...',
                #                          '',
                #                          '',
                #                          str(url4),#不是为啥，这里不识别，必须先转换string
                # )
                # return temp
                #
            # if eventMsg == 'CLICK' and msgContent == 'chatted':
        #     url = GetSiteUrl(request) + 'chatted/' + '?W_NAME=' + W_NAME
        #     temp =  GetImageTextXML2(msg,
        #                              '',
        #                              '',
        #                              '',
        #                              str(url),#不是为啥，这里不识别，必须先转换string
        #
        #                              '聊过的',
        #                              '',
        #                              'http://ww4.sinaimg.cn/mw690/6fc73b50jw1e8cvlsqt83j20m80b4mxr.jpg',
        #                              str(url),#不是为啥，这里不识别，必须先转换string
        #     )
        #     return temp

        # if eventMsg == 'CLICK' and msgContent == 'message':
        #     url = GetSiteUrl(request) + 'inbox/' + '?W_NAME=' + W_NAME
        #     temp =  GetImageTextXML2(msg,
        #
        #                              '',
        #                              '',
        #                              '',
        #                              str(url),#不是为啥，这里不识别，必须先转换string
        #
        #                              '私信',
        #                              '',
        #                              'http://ww4.sinaimg.cn/mw690/6fc73b50jw1e8cvlsqt83j20m80b4mxr.jpg',
        #                              str(url),#不是为啥，这里不识别，必须先转换string
        #     )
        #     return temp

        if eventMsg == 'CLICK' and msgContent == 'myprofile':
            profile_url = GetSiteUrl(request) + 'user/' +str(uid) + '/?W_NAME=' + W_NAME
            modify_url = GetSiteUrl(request) + 'modify/' + '?W_NAME=' + W_NAME
            setting_url = GetSiteUrl(request) + 'setting/' + '?W_NAME=' + W_NAME
            message_url  = GetSiteUrl(request) + 'inbox/' + '?W_NAME=' + W_NAME
            temp =  GetImageTextXML3(msg,


                                     '刷新登录',
                                     '',
                                     '',
                                     profile_url,#不是为啥，这里不识别，必须先转换string

                                     '私 信',
                                     '',
                                     'http://ww4.sinaimg.cn/mw690/489cbcd0gw1elajang6fvj20go0go3yu.jpg',
                                     message_url,#不是为啥，这里不识别，必须先转换string

                                     '个人设置',
                                     '',
                                     'http://ww1.sinaimg.cn/small/489cbcd0gw1elajan2es5j2074074aa3.jpg',
                                     setting_url,#不是为啥，这里不识别，必须先转换string
            )
            return temp



        #我向微信发信息
        if eventMsg != 'CLICK':
            print 'sentweixin'

            #写入微信记录
            if msgType == 'text':
                message = WeiXinMessage()
                message.uid_id = uid
                message.content = msgContent
                message.time = GetTimeNow()
                message.save()

            if msgType == 'voice':
                message = WeiXinMessage()
                message.uid_id = uid
                message.content = 'voice'
                message.meg_type = 2
                message.time = GetTimeNow()
                message.save()
            if msgType == 'image':
                message = WeiXinMessage()
                message.uid_id = uid
                message.content = 'image'
                message.meg_type = 3
                message.time = GetTimeNow()
                message.save()


            if state == 1:
                link = ForumLink('给我留言')
                resMsg = '你现在“空闲”中，点菜单【快聊】或【找角友】聊聊英语吧。\n 另感谢你的留言！由于每天收到的留言很多，我们运营mm看不过来，你可以在“论坛”'+ link
                return getReplyXml(msg,resMsg)


            if state == 2:
                # resMsg = '你正在“邀请对话”中，如果你或对方在1分钟内没有响应，本次邀请自动终止。如果你想给英语角负责人说点什么，你可以在“论坛”给我留言。'
                link = ForumLink('给我留言')
                resMsg = GetInviteUserB(request,uid) +'。\n如果你想给英语角负责人说点什么，你可以在“论坛”'+ link
                return getReplyXml(msg,resMsg)


            if state == 3:
                link = ForumLink('给我留言')
                resMsg = '你正在“随机配对”中，如果等了小一会没有成功，你可以点菜单【快聊】刷新。\n------------\n如果你想给英语角负责人说点什么，你可以在“论坛”' + link
                return getReplyXml(msg,resMsg)

            #对话中,用户发信息
            if state == 4:
                result = ChatRecord.objects.filter(Q(rid_id=uid)|Q(sid_id=uid),close=0).order_by('-id')[0]
                #更新对话时间
                result.time = GetTimeNow()
                result.msg_count +=  1
                result.save()

                if result.sid_id == uid:
                    userB_id = result.rid_id
                else:
                    userB_id = result.sid_id
                userA = user #我自己
                userB = User.objects.get(id=userB_id)

                #不同信息类型，处理方式不一样
                if msgType == 'text':
                    if userA.NAME == '' or userA.NAME == ' ' or userA.NAME == None:
                        userA.NAME = 'TA'
                    resMsg = userA.NAME + ': ' + msgContent
                    resMsg = PostFormat(resMsg)
                    #触发一个post文本给B
                    PostMessge(token,str(PostText(userB.W_NAME, resMsg)))

                    #暂时只对文本写入聊天记录,同时修改聊天记录为已读
                    # print msgContent
                    if msgContent != '':
                        SaveMessage(request,uid,userB_id,msgContent)

                        #直接刷新接受方的时间
                        temp = Message.objects.filter(s_uid_id=uid,r_uid=userB_id).order_by('-id')[0]
                        temp.read_not = 1
                        temp.r_time = temp.s_time
                        temp.save()
                        temp = Message.objects.filter(content='')
                        temp.delete()
                        return ''

                if msgType == 'image':

                    PostMessge(token,str(PostImg(userB.W_NAME,MEDIA_ID)))
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
                    #把该mid Post给用户
                    PostMessge(token,PostVocie(userB.W_NAME,New_Media_ID))
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
                    PostMessge(token,str(PostVideo(userB.W_NAME, MEDIA_ID, THUMB_MEDIA_ID, TITLE, DESCRIPTION)))
                    return ''
                if msgType == 'music':
                    MUSIC_TITLE = ''
                    MUSIC_DESCRIPTION = ''
                    MUSIC_URL = ''
                    HQ_MUSIC_URL = ''
                    THUMB_MEDIA_ID = ''
                    PostMessge(token,str(PostMusic(userB.W_NAME, MUSIC_TITLE, MUSIC_DESCRIPTION, MUSIC_URL, HQ_MUSIC_URL, THUMB_MEDIA_ID)))
                    return ''
                    #两条图文信息
                if msgType == 'news':
                    t1 = ''
                    d1 = ''
                    u1 = ''
                    p1 = ''

                    t2 = ''
                    d2 = ''
                    u2 = ''
                    p2 = ''
                    PostMessge(token,str(PostTexImg(t1,d1,u1,p1,t2,d2,u2,p2,userB.W_NAME)))

                #需要给腾讯服务器返回一个空文本
                return ''


                # if msgType == 'location':
                #     #官方没有接口发送
                #     return
                #
                #
                # if msgType == 'link':
                #     #没办法发给对方
                #     return

            if state == 5:
                link = ForumLink('给我留言')
                resMsg = '你当前在“不打扰”状态，其他人没办法找你聊天哦，如果想别人找到你，可点菜单【进入】英语角。\n如果你想给英语角负责人说点什么，你可以在“论坛”' + link
                return getReplyXml(msg,resMsg)

            if state == 6:
                link = ForumLink('给我留言')
                resMsg = '你当前在“离开”状态，系统都找不到你更别说角友，如果想别人找到你，可点菜单【进入】英语角。\n如果你想给英语角负责人说点什么，你可以在“论坛”'+ link
                return getReplyXml(msg,resMsg)



def GetChatUserBLink(request,uid):
    result = ChatRecord.objects.filter(Q(rid_id=uid)|Q(sid_id=uid),close=0).order_by('-id')[0]
    if uid == result.sid_id:
        userB_id = result.rid_id
    else:
        userB_id = result.sid_id
    link = UserLink(request,userB_id)
    return link


#避免异常的处理逻辑，任何时候退出就把begin，record中相关的未关闭的记录close
def ChatClose(uid):
    result = ChatBegin.objects.filter(Q(rid=uid)|Q(sid=uid),close=0)
    result.update(close=1)

    result = ChatRecord.objects.filter(Q(rid_id=uid)|Q(sid_id=uid),close=0)
    result.update(close=1)


def CheckPermission(req):
#临时通过英语角的id来判断权限,必须少于30才能删除内容
    uid = req.COOKIES.get('UID')
    if not uid or int(uid) > 30:
        return '0'

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
           "name":"快聊 Chat",
           "sub_button":[
           {
               "type":"click",
               "name":"进入 In",
               "key":"getin"
            },
            {
               "type":"click",
               "name":"快聊 Chat",
               "key":"random"
            },
            {
               "type":"click",
               "name":"状态 State",
               "key":"state"
            },
            {
               "type":"click",
               "name":"退出 Quit",
               "key":"getout"
            }]
       },
      {
           "name":"找角友 Find",
           "sub_button":[
           {
               "type":"view",
               "name":"找角友 Find",
               "url":"'''+ index_url +'''"
            },
            {
               "type":"view",
               "name":"聊过 Chatted",
               "url":"'''+ chatted_url +'''"
            },
            {
               "type":"view",
               "name":"帮助 Help",
               "url":"'''+ guide_url +'''"
            },
            {
               "type":"click",
               "name":"我的 My",
               "key":"myprofile"
            }]
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




def GetResponseXML2(uid,msg,resMsg):

    ads = Ads.objects.exclude(hide=1).order_by('?')
    #先给一个默认的随机广告
    ad_title = ads[0].title
    ad_img = ads[0].img
    ad_url = ads[0].url

    for i in ads:
        temp = i.view_aid.all().filter(uid=uid)
        if temp.count() < 3:
            ad_title = i.title
            ad_img = i.img
            ad_url = i.url
            break

    temp =  GetImageTextXML2(msg,

                             resMsg,
                             '',
                             '',
                             '',#不是为啥，这里不识别，必须先转换string

                             ad_title,
                             '',
                             ad_img,
                             str(ad_url),#不是为啥，这里不识别，必须先转换string
    )
    return temp


def GetInviteUserB(request,uid):
    result = ChatBegin.objects.filter(Q(rid=uid)|Q(sid=uid),mode=2,close=0).order_by('-id')[0]
    if uid == result.sid:
        userB_id = result.rid
        link = UserLink(request,userB_id)
        resMsg = '你正在等待' + link + '回应，请稍等，终止邀请请点【退出】菜单'
    else:
        userB_id = result.sid
        link = UserLink(request,userB_id)
        resMsg = link + '正等待你回应，接受邀请请点【进入】菜单，拒绝请点【退出】'

    return resMsg


def ForumLink(content):
    url = 'http://wsq.qq.com/reflow/165500268'
    link = '<a href="' + url + '">' + content + '</a>'
    return  link





#------------针对英语角服务号的设计 2014.9.7   以上




# 这方法用于解析xml
def paraseMsgXml(rootElem):
    msg = {}
    if rootElem.tag == 'xml':
        for child in rootElem:
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




