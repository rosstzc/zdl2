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

### **Precautions**

This project is a complete development project that can be deployed online, but the premise is that you must know how to connect to the WeChat public platform. If you want to understand this project, you can download it and view the code detail. If you already have experience with Django, it shouldn't be a problem to run the project locally, and you can try some features.
