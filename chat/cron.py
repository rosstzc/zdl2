# -*- coding: utf-8 -*-
# from __future__ import unicode_literals

from models import *
from views import *




# 9点开始，每分钟执行
def test():
    # user = User(username='444')
    # user.save()

    unreadReminder()
    chatReminder()
    serviceRemind()
    print ('123')



