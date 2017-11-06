from django.conf.urls import  url
from django.conf import settings
from django.conf.urls.static import static

from chat import views
from chat import view_weixinservice

urlpatterns = [

    #chat
    url(r'^MP_verify_U4Tmj9FOXTelfMyx.txt$', views.test, name=''),  #vervification for wechat
    url(r'^$', views.index, name='index'),
    url(r'^index/$', views.index, ),
    url(r'^login/$', views.Login.as_view(), ),
    url(r'^register/$', views.Register.as_view(), ),
    url(r'^invite/$', views.invite, ),
    url(r'^score-desc/$', views.score_desc, ),

    #user, uid = objectId
    url(r'^my/$', views.my, name='my'),
    url(r'^user/(?P<uid>.{1,50})/$', views.userProfile),
    url(r'^modify-info/$', views.modifyInfo, name = 'modifyInfo'),
    url(r'^online-user/$', views.onlineUser, name='onlineUser'),

    #message
    url(r'^chat-list/$', views.chatList, name='chatList'),
    url(r'^message/(?P<rid>.{1,50})/$', views.showMessage, name='showMessage'),

    #manage

    url(r'^manage/login/$', views.manageLogin, name=''),
    url(r'^manage/timer/$', views.timer, name=''),
    url(r'^manage/list-active-user/$', views.manageListActiveUser, name=''),
    url(r'^manage/user-active-data/$', views.userActiveData, name=''),
    url(r'^manage/message/$', views.manageMessage, name=''),
    url(r'^manage/addUser/', views.manageAddUser, name=''),
    url(r'^manage/send-message/', views.manageSendMessage, name=''),

    #chat-api
    # url(r'^api/register2/$', views.api_register, ),

    # get user info
    url(r'^api/user/(?P<uid>.{1,50})/$', views.apiUser, name="api_user"),
    url(r'^api/chat_magic/$', views.apiChatMagic, name="chat_magic"),

    # url(r'^api/register/$', views.API_Register.as_view(), name= "api_register" ),
    url(r'^api/chat_state/$', views.apiChatState, ),


    url(r'^test/$', views.test, ),

    #message


    #my



    #discovery



    #admin


    #weixin
    url(r'^weixinservice/$',view_weixinservice.handleRequest, name=""),
    url(r'^oauth2/$',view_weixinservice.oauth2, name=""),



]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)






# from lru import views
#
# urlpatterns = patterns(
#     '',
#     url(r'^$', views.index, name='index')
# )