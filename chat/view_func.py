#coding=utf-8

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage   #分页
from django.contrib.sites.shortcuts import get_current_site
import  datetime
import urllib,time,hashlib, json
import urllib,urllib2,time,hashlib, json



import sys


def GetSiteUrl(req):
    url = get_current_site(req)
    # url = RequestSite(req)
    site_url = 'http://' + url.domain + '/'
    return site_url


def GetUserUrl(req, uid):
    url = get_current_site(req)
    user_url = 'http://' + url.domain + '/user/' + str(uid) + '/'
    return user_url


#分页，req是get请求，result是查询结果，row是每页的行数，paginator是官方方法
def Paging(req, result, row):
    paginator = Paginator(result, row)
    page = req.GET.get('page')
    try:
        show_lines = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        show_lines = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        show_lines = paginator.page(paginator.num_pages)
        #获取url完整路径
    return show_lines


# 文本截断，注意在本函数，一个字母或中文字都按一个单位计算,所以英文会短些
    #replace是表示若没有填写时的替代文本（若为0，就不用替代文本），tag是截断文本后加的字符（比如...）
def StringCut(string, length, replace, tag):
    string = string.encode('utf8')  #这时候a是str型(从数据库读取的数据类型为unicode，经过这个encode后转化为字符)
    string = string.decode('utf8')[0:length].encode('utf8')
    if len(string) >= 2*length:    #特别说明：len查的的长度，一个中文字符按3个长度算
        string = string + tag
    if  len(str(string)) < 1 and replace != 0:
        string = replace
    return string


def SimpleCut(string, length):
    string = string.encode('utf8')  #这时候a是str型(从数据库读取的数据类型为unicode，经过这个encode后转化为字符)
    string = string.decode('utf8')[0:length].encode('utf8')
    if len(string) >= 2*length:    #特别说明：len查的的长度，一个中文字符按3个长度算
        string = string + '...'
    return string

#把换行符转换为html识别的标签
def WrapToHTML(content):
    content = content.replace('\n','<br>')
    # content = content.replace(' ','&nbsp')
    return content

def HTMLToWrap(content):
    content = content.replace('<br>','\n')
    content = content.replace('&nbsp',' ')
    return content



def UserDefaultImg(req, img):
    url = get_current_site(req)
    import random
    # img = str(img) +'?random='+ str(random.randint(12, 1000))
    if not img:
        img = 'http://' + url.domain + '/static/img/erweima.jpg'
    return img


def OnlineTime(hour):
    if not hour:
        hour = 4
    now = datetime.datetime.now()
    start = now - datetime.timedelta(hours=hour)
    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    start = start.strftime(DATETIME_FORMAT) #转发为unicode的格式，与数据库存储一致
    return start

def OnlineTimeMinutes(minutes):
    now = datetime.datetime.now()
    start = now - datetime.timedelta(minutes=minutes)
    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    start = start.strftime(DATETIME_FORMAT) #转发为unicode的格式，与数据库存储一致
    return start


def GetTimeBefore(time,hour):
    dd=datetime.datetime.strptime(time,'%Y-%m-%d %H:%M:%S')
    start =dd - datetime.timedelta(hours=hour)
    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    start = start.strftime(DATETIME_FORMAT) #转发为unicode的格式，与数据库存储一致
    return start

def GetTimeNow():
    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return time

def PostMessge(token,post):
    url = 'https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token=' + str(token)
    req = urllib2.Request(url,post)
    response = urllib2.urlopen(req)
    return response


def PostText(OPENID,content):
    #文本
    template = '{ "touser":"'+ OPENID + '", "msgtype":"text", "text":{"content":"'+ content + '"}}'
    return template

def PostImg(OPENID,MEDIA_ID):
    template = '{"touser":"' + OPENID + '","msgtype":"image","image":{"media_id":"' + MEDIA_ID + '"}}'
    return template

def PostVocie(OPENID,MEDIA_ID):
    template = '{"touser":"' + OPENID + '","msgtype":"voice","voice":{"media_id":"' + MEDIA_ID + '"}}'
    print template
    return template

def PostVideo(OPENID, MEDIA_ID, THUMB_MEDIA_ID, TITLE, DESCRIPTION):

    template = '{ "touser":"' + OPENID + '","msgtype":"video", "video":{"media_id":"' + MEDIA_ID + '", "thumb_media_id":"'+ THUMB_MEDIA_ID + '","title":"' + TITLE + '","description":"' + DESCRIPTION + '"}}'
    return template

def PostMusic(OPENID, MUSIC_TITLE, MUSIC_DESCRIPTION, MUSIC_URL, HQ_MUSIC_URL, THUMB_MEDIA_ID):
    template = '{"touser":"' + OPENID + '", "msgtype":"music", "music": { "title":"' + MUSIC_TITLE + '", "description":"' + MUSIC_DESCRIPTION + '", "musicurl":"' + MUSIC_URL + '", "hqmusicurl":"' + HQ_MUSIC_URL + '", "thumb_media_id":"' + THUMB_MEDIA_ID + '" }}'
    return template

def PostTexImg(t1,d1,u1,p1,t2,d2,u2,p2,OPENID):

    article1 = '"title":"' + t1 + '", "description":"' + d1 + '", "url":"' + u1 + '", "picurl":"' + p1 + '"'
    article2 = '"title":"' + t2 + '", "description":"' + d2 + '", "url":"' + u2 + '", "picurl":"' + p2 + '"'

    template = '{"touser":"' + OPENID + '", "msgtype":"news", "news":{ "articles": [ { ' + article1 + ' },{ ' + article2 + ' }]}}'
    return template

