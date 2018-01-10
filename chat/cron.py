# -*- coding: utf-8 -*-
# from __future__ import unicode_literals

from models import *
from views import *




# 9点开始，每分钟执行
def test():
    test2()
    # unreadReminder()
    # chatReminder()



def unreadNoteForMan():
    unreadReminder('1')
    return

def unreadNoteForWoman():
    unreadReminder('0')
    return


def chatNote():
    #针对那些没有未读用户进行提醒
    chatReminder()
    return

def creatPushFlowerRecord():
    pushFlowerRecord()
    return

def oneMin():

    return

def serviceNote():
    serviceRemind()

def minCheck():
    checkMin()
    #根据pushFlowerLogic的记录，按时间推送给用户
    pushFlower()
