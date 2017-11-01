# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.

#api doc  https://www.showdoc.cc/zdl?page_id=15227642

# #所有表
# 1. 数据库-表
# 2. User 用户表
# 3. Complain 投诉表（投诉、举报）
# 4. Block 屏蔽表
# 5. Invite 邀请表
# 6. Buy 购买表（金币、积分、礼物）
# 7. Like 喜欢表
# 8. Give 送礼物表
# 9. Chat 聊天配对表
# 10. Message 聊天消息表
# 11. --
# 12. Interest 兴趣表



class User(models.Model):
    # W_ID = models.CharField(max_length=50, blank=True ,verbose_name='* 微信号',
    #                         help_text='到微信的"个人信息"复制微信号，粘贴到这里。注意不是名字哦' )
    W_NAME = models.CharField(max_length=50, verbose_name='* W_NAME', blank=True)
    username = models.CharField(max_length=50, verbose_name='', blank=True)
    password = models.CharField(max_length=50, verbose_name='', blank=True)
    name = models.CharField(max_length=50, verbose_name='' , blank=True)

    sex_choices = (
        ('0', '女'),
        ('1', '男'),
        ('2', '其他'),
    )
    sex = models.CharField(max_length=10, choices=sex_choices, default='2', verbose_name='* 性别 /Sex', blank=True)

    age_choices = (
        ('1', '12~18'),
        ('2', '18~25'),
        ('3', '25~32'),
        ('4', '33~40'),
        ('5', '40以上'),
    )
    age = models.CharField(max_length=10, choices=age_choices, default='2' ,verbose_name='* 年龄 /Age' , blank=True)

    xingzuo =  models.CharField(max_length=50, verbose_name='星座', blank=True)
    like =  models.CharField(max_length=50, verbose_name='', blank=True)
    score_today = models.CharField(max_length=50, verbose_name='', blank=True)
    score_forever = models.CharField(max_length=50, default='10', verbose_name='', blank=True)   #永久可用积分，比较花钱买物品送的积分
    score_sum = models.CharField(max_length=50, default='10',verbose_name='', blank=True)  #累计积分，用做等级统计
    coin = models.CharField(max_length=50, default='0',verbose_name='', blank=True)
    online = models.CharField(max_length=50, default='1',verbose_name='', blank=True)
    state = models.CharField(max_length=50, default='1',verbose_name='', blank=True)
    time_login_today = models.CharField(max_length=100,blank=True)
    city = models.CharField(max_length=50, verbose_name='', blank=True)
    industry = models.CharField(max_length=50, verbose_name='', blank=True)
    introduction = models.TextField()

    interest = models.CharField(max_length=200, verbose_name='', blank=True)
    user_type = models.CharField(max_length=200, default='1', verbose_name='', blank=True)

    #image0, image1, image2...
    image_url = models.TextField(blank=True,) #用json呈现
    gift =  models.TextField(blank=True,)
    image1 = models.FileField(upload_to='fig/', blank=True)
    # image1 = models.FileField(upload_to='../media/fig/', blank=True)

    # IMG = models.FileField(upload_to='../media/fig/', verbose_name='* 上传头像 /Photo', blank=True,
    #                        help_text='提示：1）有照片的人会获得更多交流机会. 2）严禁情色、暴力、政治等违反中国法规的图片，一经发现直接封ID。3)暂不支持gif图片和大尺寸图片，会出错哦，亲 ')
    # AUDIO = models.TextField(max_length=400, verbose_name=' 个人简介 /Introduction', blank=True, help_text='(说说你的兴趣、爱好、最近想法、学英语情况等等,以便对方更好与你交流)')
    # W_SEX = models.CharField(max_length=10,blank=True,) #老版本字段，老版本字段，标识期望的对话的人的性别
    # STATE = models.TextField(blank=True,)
    # S_WID = models.TextField(blank=True,)  #老版本字段，现在不用，标识随机匹配的4个用户的微信号
    R_TIME = models.CharField(max_length=100, blank=True)
    # W_TIME = models.CharField(max_length=100, blank=True)
    # TIME = models.CharField(max_length=100, blank=True)
    POSITION = models.CharField(max_length=50, blank=True, verbose_name='所在城市|地区 /City')
    #
    # state_service = models.SmallIntegerField(max_length=5, default=1,blank=True)  #1空闲，2邀请中，3配对中，4对话中，5离开，6退出， 8话题在聊，9话题围观
    #
    # language = models.CharField(max_length=50, blank=True)
    # city = models.CharField(max_length=50, blank=True)
    province = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=50, blank=True)
    remind_key = models.CharField(max_length=10, default='0',blank=True)  #用户48小时服务到期提醒
    remind_time = models.CharField(max_length=100,blank=True)   #用于每天未读提醒、推送提醒
    unread = models.CharField(max_length=10, default='0',blank=True)
    # headimgurl = models.CharField(max_length=500, blank=True)
    # unionid = models.CharField(max_length=200, blank=True)
    #
    # mail = models.CharField(max_length=100, blank=True,verbose_name='邮箱 /Email',help_text='仅用于系统通知，不会公开显示')
    # mobile = models.CharField(max_length=50, blank=True,verbose_name='手机 /Mobile No.',help_text='仅用于帐号识别，不会公开显示')
    #
    # key_choices = (
    #     (1, 'Yes'),
    #     (0, 'No'),
    # )
    # meg_remind_key = models.SmallIntegerField(max_length=20, choices=key_choices, default=1,verbose_name='* 有私信即时提醒我', blank=True,)
    # invite_choices = (
    #     (1, 'Yes'),
    #     (0, 'No'),
    # )
    # invite_key= models.SmallIntegerField(max_length=20, choices=invite_choices, default=1,verbose_name='* 允许直接邀请我对话', blank=True,)
    #
    # hour_choice =  (
    #     (1, '1'), (2, '2'),(3, '3'),(4, '4'),(5, '5'),(6, '6'), (7, '7'),(8, '8'),(9, '9'), (10, '10'),(11, '11'), (12, '12'),
    #     (13, '13'), (14, '14'),(15, '15'), (16, '16'), (17, '17'),(17, '18'),(19, '19'),(20, '20'),(21, '21'),(22, '22'), (23, '23'), (24, '24'),
    # )
    # time_unbother_start = models.SmallIntegerField(max_length=3,choices=hour_choice,default=23)
    # time_unbother_end = models.SmallIntegerField(max_length=3,choices=hour_choice, default=8)
    #
    # #话题模块新增
    # hour_remind =  (
    #     (0, '无'), (1, '1'), (2, '2'),(3, '3'),(4, '4'),(5, '5'),(6, '6'), (7, '7'),(8, '8'),(9, '9'), (10, '10'),(11, '11'), (12, '12'),
    #     (13, '13'), (14, '14'),(15, '15'), (16, '16'), (17, '17'),(17, '18'),(19, '19'),(20, '20'),(21, '21'),(22, '22'), (23, '23'), (24, '24'),
    # )
    # time_remind = models.SmallIntegerField(max_length=3,choices=hour_remind, default=20)  #设定每天提醒的具体时间
    # time_remind_time =  models.CharField(max_length=100, blank=True) #最近学习提醒的具体时刻



    # REQUEST_choices = (
    #     ('1', '提升能力'),
    #     ('2', '考雅思'),
    #     ('3', '考托福'),
    #     ('4', '识朋友'),
    #     ('5', '商务职业'),
    #     ('6', '旅游'),
    # )
    # REQUEST = models.CharField(max_length=20, default=1,choices=REQUEST_choices, verbose_name='* 学英语目的 /Target',blank=True)

    # LEVEL_choices = (
    #     ('1', '难交流'),
    #     ('2', '很一般'),
    #     ('3', '正常交流'),
    #     ('4', '比较好'),
    #     ('5', '流利'),
    # #    ('6', '母语'), 暂不使用，日后开开了英文版后就引入
    # )
    # LEVEL = models.CharField(max_length=20, choices=LEVEL_choices, verbose_name='* 你的英语水平 /English Level', blank=True,)


    def __unicode__(self):

        return self.name


class UserImg(models.Model):
    uid = models.ForeignKey(User, related_name='uid_img')
    imgData = models.TextField(blank=True)
    time = models.CharField(max_length=100,blank=True)
    image = models.FileField(upload_to='fig/', blank=True)




class Complain(models.Model):
    W_NAME = models.CharField(max_length=50, verbose_name='* W_NAME', blank=True)

class Block(models.Model):
    uid = models.ForeignKey(User, related_name='uid')
    b_uid = models.ForeignKey(User, related_name='buid')


class Invite(models.Model):
    w_name = models.CharField(max_length=50, verbose_name='* W_NAME', blank=True)

class Buy(models.Model):
    w_name = models.CharField(max_length=50, verbose_name='* W_NAME', blank=True)

class Like(models.Model):
    w_name = models.CharField(max_length=50, verbose_name='* W_NAME', blank=True)

class Give(models.Model):
    w_name = models.CharField(max_length=50, verbose_name='* W_NAME', blank=True)


#配对记录表
class Chat(models.Model):
    sid = models.ForeignKey(User, related_name='chat_sid',null=True)
    rid = models.ForeignKey(User,related_name='chat_rid',null=True)
    mode = models.CharField(max_length=5,default=0,blank=True) # 1 配机匹配
    time = models.CharField(max_length=100,blank=True)   #配对时间
    close = models.CharField(max_length=5,default=0,blank=True)  # 对话 1关闭， 0未关闭
    hidden =  models.CharField(max_length=5,default=0,blank=True)
    msg_count = models.CharField(max_length=10,default=0,blank=True)


#消息列表
class Message(models.Model):
    sid = models.ForeignKey(User,related_name='sid_message',null=True) #发送者id
    rid = models.ForeignKey(User, related_name='rid_message',null=True)  #接受者id
    read_not = models.CharField(max_length=2, default='0')  #接收方是否看了   1看了， 0为看
    content= models.TextField(blank=True)  #私信内容
    img = models.TextField(blank=True)    #附件图片 （日后拓展）
    s_time = models.CharField(max_length=50, blank=True)
    r_time = models.CharField(max_length=50, blank=True)  #阅读时间	      与readnot字段一同刷新
    s_del = models.CharField(max_length=20, blank=True)  #发送方删除      1删除，0未删除，
    r_del = models.CharField(max_length=20, blank=True )  #接收方删除      1删除，0未删除


class Interest(models.Model):
    w_name = models.CharField(max_length=50, verbose_name='* W_NAME', blank=True)


#聊天记录表
class ChatList(models.Model):
    sid = models.ForeignKey(User,related_name='_sid_chat_list',null=True) #发送者id
    rid = models.ForeignKey(User, related_name='rid_chat_list',null=True)  #接受者id
    content = models.TextField(blank=True)
    img = models.TextField(blank=True)
    time = models.CharField(max_length=50,blank=True)
    m_type =models.CharField(max_length=2, default='1') # 信息类型，默认为1：私信
    unread = models.SmallIntegerField(default=0,blank=True)



class Config(models.Model):

    key = models.CharField(max_length=100,blank=True)
    value = models.CharField(max_length=1000,blank=True)
    version =  models.SmallIntegerField(default=0,blank=True)  #0是测试环境，1正式环境
    time = models.CharField(max_length=100,blank=True)