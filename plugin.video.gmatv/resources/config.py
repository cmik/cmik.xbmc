# -*- coding: utf-8 -*-

'''
    GMA.tv Add-on
    Copyright (C) 2020 cmik
'''


#---------------------- CONFIG ----------------------------------------
# Cookies
cookieFileName = 'gmatv.cookie'

# Cache
shortCache = {'name' : 'gmatv', 'ttl': 1}
longCache = {'name' : 'gmatv_db', 'ttl': 24*7}
urlCachePrefix = 'urlcache_'

# HOSTS / URI / SERVICES
webserviceUrl = 'https://data.igma.tv'
websiteUrl = 'https://www.gmanetwork.com'
websiteSecuredUrl = 'https://www.gmanetwork.com'
websiteCDNUrl = 'https://aphrodite.gmanetwork.com'
youtubeVideoUrl = 'https://www.youtube.com/watch?v=%s'
uri = {
    'base' : '/fullepisodes/',
    'search' : '/fullepisodes/search?q=%s',
    'showPage' : '/fullepisodes/home/%s',
    'imageLowRes' : '/entertainment/shows/images/480_360_%s',
    'image' : '/entertainment/shows/images/640_480_%s',
    'posterLowRes' : '/entertainment/shows/images/480_360_%s',
    'poster' : '/entertainment/shows/images/640_480_%s',
    'banner' : '/entertainment/shows/images/1867_1050_%s',
    'episodeLowRes' : '/entertainment/videos/images/480_360_%s',
    'episode' : '/entertainment/videos/images/640_480_%s',
    'castLowRes' : '/entertainment/tv/castinformation/320_240_%s',
    'cast' : '/entertainment/tv/castinformation/640_480_%s',
}
services = {
    'sections' : '/entertainment/fulleps/sections/home.gz',
    'sectionDetails' : '/entertainment/fulleps/shelves/%s.gz',
    'showDetails' : '/entertainment/tv/%s/show_details.gz',
    'showNbEpisodePages' : '/entertainment/tracker/list_tv_%s_episodes.gz',
    'showNbFullEpisodePages' : '/entertainment/tracker/list_tv_%s_full_episode.gz',
    'episodesPerPage' : '/entertainment/listing/tv/%s/episodes/%s.gz',
    'fullEpisodesPerPage' : '/entertainment/listing/tv/%s/full_episode/%s.gz',
    'episodeDetails' : '/entertainment/listing/tv/%s/full_episode/%s.gz',
    'showCasts' : '/entertainment/tv/%s/listing_tv_cast.gz'
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
MYLISTSHOWLASTEPISODES = 19
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
PERSONALIZESETTINGS = 55
OPTIMIZELIBRARY = 56
RESETCATALOG = 57
IMPORTSHOWDB = 58
IMPORTEPISODEDB = 59
IMPORTALLDB = 60
FIRSTINSTALL = 98
ENDSETUP = 99


