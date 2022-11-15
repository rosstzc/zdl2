[Chinese Version](https://github.com/rosstzc/zdl2/blob/master/README_CH.MD)

[English Version](https://github.com/rosstzc/zdl2/blob/master/README.md)




# A Chat App based on The WeChat
a Chat app base on the WeChat Official Accounts.
## **Project Introduction**

This project is a stranger chatting app based on the WeChat platform. Meeting new friends is a common need of our human beings. WeChat is the largest social platform in China. Since the positioning of WeChat is friend, there are almost no entrances for meeting strangers on WeChat. So it was my idea to develop a chat application on WeChat.

I found a method that uses the official account as a message forwarder to help two people establish communication. After following the Official Account, Users send messages to the Official Account and the Official Account replies to messages programmatically. Based on this rule, two people can chat with each other, although they are not friends on WeChat.

## **Works in this project**

1. Used Django to build a web app for users to enter and display personal dating info. The web app also includes these features, such as displaying lists of recommended users, chat invites, chat history, etc.
2. Integrated with the WeChat API. Interfaces included authorization, message forwarding, available status checking, etc.

Applied technology:

1. Python + Django: built a web app for users to enter and display dating information.
2. jquery.js: processed some logical judgements after clicking button
3. WeChat API: integrated with WeChat
4. weui.css and weui.js: made the style of the web app consistent with WeChat

## **Project Experience**

Since this is a project based on a third-party platform, it is very important to understand the limitations of the platform. As an example, the message API has a 48-hours limitation. If a guy did not interact with the official account, he would lose his connection with the official account and nobody could send messages to him across the official account. This factor impacted the user experience of the product. Another poor interactive experience is the process of chatting. After starting a chat on the web app, it need to jump back to the message box of the official account for chatting.

Therefore, for similar projects that are based on third-party platforms, it is very important to understand the rules of the platform, because it deeply impacts the product design and the user experience.

## **Precautions**

This project is a complete development project that can be deployed online, but the premise is that you must know how to connect to the WeChat public platform. If you want to understand this project, you can download it and view the code detail. If you already have experience with Django, it shouldn't be a problem to run the project locally, and you can try some features.

## 项目一些截图展示：

### 下图是关注公众后进入app的首页，可以随机配对聊天或者邀请在线的用户聊天。

<img src="https://user-images.githubusercontent.com/5052733/201883426-46086c2e-d28d-4070-83fe-d6076f66ce1b.png" width="300px">

<img src="https://user-images.githubusercontent.com/5052733/201883445-772329f2-e62a-46b9-a238-683da537aec0.png" width="300px">



### 下图展示用户的资料信息，图中绿色按钮表示用户处于在线状态，可以给他发起聊天邀请。

<img src="https://user-images.githubusercontent.com/5052733/201890832-7908c4d2-5acf-4825-89e2-6c281116a3b8.png" width="300px">


<img src="https://user-images.githubusercontent.com/5052733/201890848-a815605f-2b12-4ef5-a67d-07752d4303bc.png" width="300px">



### 下面展示聊天配对成功后的聊天过程。

<img src="https://user-images.githubusercontent.com/5052733/201891088-3574e7e9-0b94-4762-8461-a7651e0232d5.png" width="300px">

<img src="https://user-images.githubusercontent.com/5052733/201891105-cf1a6d4b-68c7-4667-be65-bbd36786be88.png" width="300px">
