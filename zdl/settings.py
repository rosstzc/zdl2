# -*- coding: utf-8 -*-


"""
Django settings for zdl project.

Generated by 'django-admin startproject' using Django 1.11.4.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""


import os
import platform

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))



if 'centos' in platform.platform():
    #线上
    DEBUG = False
    # DEBUG = True
else:
    #开发
    DEBUG = True
    # DEBUG = False

ADMINS = (
# ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS





# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'i6m5^6xdt9bmn=zh2v8jwjz(donw)b(zo8p@a6evbp7(%r@-zf'

# SECURITY WARNING: don't run with debug turned on in production!


ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'chat',
    'django_crontab', #定时任务

]

#定时任务
CRONJOBS = [
    # ('*/1 * * * *', 'chat.cron.test', '>>/home/test.log')
    # ('*/1 * * * * sleep 10', 'chat.cron.test', '>>/home/test.log')
    # ('*/1 * * * *', 'zdl.chat.cron.test')
    # ('*/1 * * * * sleep 10', 'chat.cron.test'),  # not work
    # ('*/1 * * * *', 'chat.views.timer'),  # not work

    # ('*/1 * * * *', 'chat.cron.test'),


    ('0 21 * * *', 'chat.cron.unreadNote'),   #给又未读信息的人提醒
    # ('1 21 * * *', 'chat.cron.unreadNote'),   #给又未读信息的人提醒
    # ('2 21 * * *', 'chat.cron.unreadNote'),   #给又未读信息的人提醒

    ('1 21 * * *', 'chat.cron.chatNote'),   #给没有未读的人发每天提醒
    ('2 21 * * *', 'chat.cron.chatNote'),   #给没有未读的人发每天提醒
    ('3 21 * * *', 'chat.cron.chatNote'),   #给没有未读的人发每天提醒

    ('* */1 * * *', 'chat.cron.serviceNote'),   #每小时一次

]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'zdl.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'zdl.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases



    #

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'zdl',
#         'USER':'root',
#         'PASSWORD':'lbj100200',
#         'HOST':'120.25.13.110',
#         'PORT':'3306',
#     }
# }


# 线上数据库的配置

if 'centos' in platform.platform():
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'zdl',
            'USER':'root',
            'PASSWORD':'lbj100200',
            'HOST':'120.25.13.110',
            'PORT':'3306',
        }
    }
else:
# 本地环境
    # Make `python manage.py syncdb` works happy!
    MYSQL_HOST = ''
    MYSQL_PORT = ''
    MYSQL_USER = 'root'
    MYSQL_PASS = ''
    MYSQL_DB   = 'en2401'

    DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        # 'NAME': os.path.join(BASE_DIR, 'test.db'),
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
#         'NAME': MYSQL_DB,                      # Or path to database file if using sqlite3.
#         # The following settings are not used with sqlite3:
#         'USER': MYSQL_USER,
#         'PASSWORD': MYSQL_PASS,
#         'HOST': MYSQL_HOST,                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
#         'PORT': MYSQL_PORT,                      # Set to empty string for default.
#     }
# }




# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

# TIME_ZONE = 'UTC'
TIME_ZONE = 'Asia/Shanghai'


USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

MEDIA_ROOT = os.path.join(BASE_DIR, 'media').replace('\\','/')
MEDIA_URL = '/media/'


STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')