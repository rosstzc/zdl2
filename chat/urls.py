from django.conf.urls import  url


from chat import views

urlpatterns = [

    #chat
    url(r'^$', views.index, name='index'),
    url(r'^index/$', views.index, ),
    url(r'^login/$', views.Login.as_view(), ),
    url(r'^register/$', views.Register.as_view(), ),

    #user, uid = objectId
    url(r'^my/$', views.my),
    url(r'^user/(?P<uid>.{1,50})/$', views.userProfile),
    url(r'^modify-info/$', views.ModifyInfo.as_view(), name = 'modifyInfo'),
    url(r'^online-user/$', views.onlineUser, name='onlineUser'),

    #message
    url(r'^chat-list/$', views.chatList, name='chatList'),
    url(r'^message/(?P<uid>.{1,50})/$', views.message, name='message'),

    #manage
    url(r'^manage/login$', views.manageLogin, name=''),
    url(r'^manage/list-active-user$', views.manageListActiveUser, name=''),
    url(r'^manage/user-active-data$', views.userActiveData, name=''),
    url(r'^manage/message$', views.manageMessage, name=''),
    url(r'^manage/addUser', views.manageAddUser, name=''),
    url(r'^manage/send-message', views.manageSendMessage, name=''),

    #chat-api
    # url(r'^api/register2/$', views.api_register, ),

    # get user info
    url(r'^api/user/(?P<uid>.{1,50})/$', views.apiUser, name="api_user"),
    url(r'^api/chat_magic/$', views.apiChatMagic, name="chat_magic"),

    url(r'^api/register/$', views.API_Register.as_view(), name= "api_register" ),
    url(r'^api/chat_state/$', views.apiChatState, ),

    #message





    #my



    #discovery



    #admin


    #

]


# from lru import views
#
# urlpatterns = patterns(
#     '',
#     url(r'^$', views.index, name='index')
# )