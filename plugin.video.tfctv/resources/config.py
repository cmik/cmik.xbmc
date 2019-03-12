# -*- coding: utf-8 -*-

'''
    Tfc.tv Add-on
    Copyright (C) 2018 cmik
'''


#---------------------- CONFIG ----------------------------------------
# Cookies
cookieFileName = 'tfctv.cookie'

# Cache
shortCache = {'name' : 'tfctv', 'ttl': 1/2}
longCache = {'name' : 'tfctv_db', 'ttl': 24*7}
urlCachePrefix = 'url_'

# HOSTS / URI
webserviceUrl = 'https://tfc.tv'
websiteUrl = 'https://tfc.tv'
websiteSecuredUrl = 'https://tfc.tv'
websiteSSOUrl = 'https://kapamilya-accounts.abs-cbn.com'
gigyaCDNUrl = 'https://cdns.us1.gigya.com'
gigyaAccountUrl = 'https://accounts.us1.gigya.com'
gigyaSocializeUrl = 'https://socialize.us1.gigya.com'
uri = {
    'base' : '/',
    'home' : '/home',
    'profile' : '/profile',
    'profileDetails' : '/profile/details',
    'logout' : "/logout",
    'login' : '/api/spa/login',
    'callback' : '/callback',
    'authSSO' : '/sso/authenticate',
    'checkSSO' : '/sso/checksession',
    'signin' : '/signin',
    'welcome' : '/welcome',
    'checksession' : '/checksession',
    'webSdkApi' : '/gs/webSdk/Api.aspx',
    'webSdkBootstrap' : '/accounts.webSdkBootstrap',
    'gigyaSSO' : '/gs/sso.htm',
    'gigyaJS' : '/js/gigya.js',
    'gigyaNotifyLogin' : '/socialize.notifyLogin',
    'gigyaAccountInfo' : '/accounts.getAccountInfo',
    'gigyaGmidTicket' : '/socialize.getGmidTicket',
    'authCallback' : '/connect/authorize/callback',
    'episodeDetails' : '/episode/details/%s',
    'mediaFetch' : '/media/fetch',
    'myList' : '/user/mylist',
    'categoryList' : '/category/list/%s',
    'showDetails' : '/show/details/%s',
    'episodePagination' : '/modulebuilder/getepisodes/%s/show/%s',
    'addToList' : '/method/addtolist',
    'removeFromList' : '/method/deletefromlist',
}

# User-agent
userAgents = { 
    webserviceUrl : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36',
    websiteUrl : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36',
    'default' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36'
    }

# MODES
SUBCATEGORIES = 1
SUBCATEGORYSHOWS = 2
SHOWEPISODES = 3
PLAY = 4
CHOOSEBANDWIDTH = 5
CATEGORIES = 10
SECTIONCONTENT = 11
MYACCOUNT = 12
MYINFO = 13
MYSUBSCRIPTIONS = 14
MYTRANSACTIONS = 15
LOGOUT = 16
MYLIST = 20
LISTCATEGORY = 21
ADDTOLIST = 22
REMOVEFROMLIST = 23
ADDTOLIBRARY = 24
REMOVEFROMLIBRARY = 25
CHECKLIBRARYUPDATES = 26
EXPORTEDSHOWS = 27
SEARCHMENU = 30
EXECUTESEARCH = 31
TOOLS = 50
RELOADCATALOG = 51
CLEANCOOKIES = 52
OPENSETTINGS = 53
ENTERCREDENTIALS = 54
PERSONALIZESETTINGS = 55
OPTIMIZELIBRARY = 56
RESETCATALOG = 57
IMPORTSHOWDB = 58
IMPORTEPISODEDB = 59
IMPORTALLDB = 60
FIRSTINSTALL = 98
ENDSETUP = 99


