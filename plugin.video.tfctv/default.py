import re
import sys
import urllib, urllib2, ssl, cookielib
import json
import time
import hashlib
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import os.path
from operator import itemgetter
import CommonFunctions as common

try:
   import StorageServer
except:
   from ressources.lib.dummy import storageserverdummy as StorageServer
# Short cache   
shortCache = StorageServer.StorageServer("tfctv", 1/2) # 30 minutes cache
# Long cache
longCache = StorageServer.StorageServer("tfctv_db", 24 * 7) # 1 week cache

sessionCache = {}

addon = xbmcaddon.Addon()
setting = addon.getSetting
lang = addon.getLocalizedString
addonInfo = addon.getAddonInfo
common.plugin = addonInfo('name')

sCacheFunction = shortCache.cacheFunction
lCacheFunction = longCache.cacheFunction

#---------------------- CONFIG ----------------------------------------
# URLs
webserviceUrl = 'https://tfc.tv'
websiteUrl = 'https://tfc.tv'
websiteSecuredUrl = 'https://tfc.tv'
websiteSSOUrl = 'https://kapamilya-accounts.abs-cbn.com'
gigyaCDNUrl = 'https://cdns.us1.gigya.com'
gigyaAccountUrl = 'https://accounts.us1.gigya.com'
gigyaSocializeUrl = 'https://socialize.us1.gigya.com'

# Cache
cacheActive = setting('cacheActive')
if cacheActive == 'false': 
    # sCacheFunction = lambda x, *y: x(*y)
    def sessionCacheFunction(x, *y): 
        hash = ''
        for p in y:
            if isinstance(p, dict):
                for key in sorted(p.iterkeys()):
                    hash += "'%s'='%s'" % (key, p[key])
            elif isinstance(p, list):
                hash += ",".join(["%s" % el for el in p])
            else:
                try:
                    hash += p
                except:
                    hash += str(p)
        sessionCache[hash] = x(*y)
        return sessionCache[hash]
    sCacheFunction = sessionCacheFunction
    lCacheFunction = lambda x, *y: x(*y)

# Debug 
if setting('debug') == 'true':
    common.dbg = True # Default
    common.dbglevel = int(setting('debugLevel')) # Default

   
#---------------------- FUNCTIONS ----------------------------------------
def showMainMenu():
    checkAccountChange()
    
    # if not logged in, ask to log in
    if isLoggedIn() == False:
        if setting('emailAddress') != '':
            if (confirm(lang(57007), line1=lang(57008) % setting('emailAddress'))):
                (account, logged) = checkAccountChange(True)
        else:
            if setting('addonNewInstall') == 'true':
                showMessage(lang(57016), lang(57018))
                addon.setSetting('addonNewInstall', 'false')
            else:
                showNotification(lang(57017), lang(50002))
    elif setting('displayMyList') == 'true':
        addDir('My List', '/', 20, 'icon.png', isFolder = True, **formatMenu())
    
    if setting('displayWebsiteSections') == 'true':
        addDir('By Category', '/', 10, 'icon.png', isFolder = True, **formatMenu())
    else:
        showCategories()
        
    if setting('displayWebsiteSections') == 'true':
        showNotification(lang(57020), lang(50008))
        sections = getWebsiteHomeSections()
        for s in sections:
            addDir(s['name'].title(), str(s['id']), 11, 'icon.png', isFolder = True, **formatMenu())
        
    if setting('displayMyAccountMenu') == 'true':    
        addDir('My Account', '/', 12, 'icon.png', isFolder = True, **formatMenu())
    
    if setting('displayTools') == 'true':
        addDir('Tools', '/', 50, 'icon.png')
        
    xbmcplugin.endOfDirectory(thisPlugin)
    
def showMyList():   
    categories = getMyListCategories()
    for c in categories:
        addDir(c['name'], str(c['id']), 21, 'icon.png', **formatMenu())
    xbmcplugin.endOfDirectory(thisPlugin)
    
def showMyListCategory(url):   
    items = getMylistCategoryItems(url)
    log(items)
    for e in items:
        log(e)
        if e['type'] == 'show':
            addDir(e['name'], str(e['id']), 3, e['image'], isFolder = True, **formatShowInfo(e, addToList=False))
        elif e['type'] == 'episode':
            addDir(e['title'], str(e['id']), 4, e['image'], isFolder = False, **formatVideoInfo(e, addToList=False))
    xbmcplugin.endOfDirectory(thisPlugin)
        
def showCategories():   
    categories = lCacheFunction(getCategories)
    for c in categories:
        addDir(c['name'], str(c['id']), 1, 'icon.png', isFolder = True, **formatMenu())
        
    if setting('displayWebsiteSections') == 'true':
        xbmcplugin.endOfDirectory(thisPlugin)

def showTools():
    addDir('Reload Catalog Cache', '/', 51, 'icon.png')
    addDir('Clean cookies file', '/', 52, 'icon.png')
    xbmcplugin.endOfDirectory(thisPlugin)
      
def showSubCategories(categoryId):
    subCategories = lCacheFunction(getSubCategories, categoryId)
    for s in subCategories:
        addDir(s['name'], str(s['id']), 2, 'menu_logo.png', isFolder = True, **formatMenu())
    xbmcplugin.endOfDirectory(thisPlugin)
   
def showSubCategoryShows(subCategoryId):
    shows = sCacheFunction(getShows, subCategoryId)
    if len(shows) == 0:
        xbmcplugin.endOfDirectory(thisPlugin)
        return False
    displayShows(shows)
    
def showWebsiteSectionContent(section, page=1):
    # checkAccountChange()
    itemsPerPage = int(setting('itemsPerPage'))
    content = getWebsiteSectionContent(section, page, itemsPerPage)
    for e in content:
        if e['type'] == 'show':
            addDir(e['name'], str(e['id']), 3, e['image'], isFolder = True, **formatShowInfo(e))
        elif e['type'] == 'episode':
            addDir(e['title'], str(e['id']), 4, e['image'], isFolder = False, **formatVideoInfo(e))
    if len(content) == itemsPerPage:
        addDir("Next >>", section, 11, '', page + 1)
    xbmcplugin.endOfDirectory(thisPlugin)

def displayShows(shows):
    sortedShowInfos = []
    for show in shows:
        sortedShowInfos.append((show['name'].lower(), show['name'], str(show['id']), 3, show['image'], formatShowInfo(show)))
    
    sortedShowInfos = sorted(sortedShowInfos, key = itemgetter(0))
    for info in sortedShowInfos:
        addDir(info[1], info[2], info[3], info[4], isFolder = True, **info[5])
            
    xbmcplugin.endOfDirectory(thisPlugin)
    
def showEpisodes(showId, page=1):
    itemsPerPage = int(setting('itemsPerPage'))
    episodes = sCacheFunction(getEpisodesPerPage, showId, page, itemsPerPage)
    for e in episodes:
        addDir(e['title'], str(e['id']), 4, e['image'], isFolder = False, **formatVideoInfo(e))
    if len(episodes) == itemsPerPage:
        addDir("Next >>", showId, 3, '', page + 1)
    xbmcplugin.endOfDirectory(thisPlugin)
        
def playEpisode(url):    
    errorCode = -1
    episodeDetails = {}
    episode = url.split('/')[0]
    
    # Check if logged in
    if isLoggedIn() == False:
        showNotification(lang(57012), lang(50002))
        login()
        
    for i in range(int(setting('loginRetries')) + 1):
        episodeDetails = getMediaInfo(episode)
        if episodeDetails and 'errorCode' in episodeDetails and episodeDetails['errorCode'] == 0 and 'data' in episodeDetails:
            break
        else:
            login()
            
    if episodeDetails and 'viewingNotAllowed' not in episodeDetails and 'errorCode' in episodeDetails and episodeDetails['errorCode'] == 0 and 'data' in episodeDetails:
        if 'preview' in episodeDetails['data'] and episodeDetails['data']['preview'] == True:
            showNotification(lang(57025), lang(50002))
        else:
            if 'StatusMessage' in episodeDetails and episodeDetails['StatusMessage'] != '':
                showNotification(episodeDetails['StatusMessage'], lang(50009))
        url = setting('proxyHostUrl') % (setting('proxyPort'), urllib.quote(episodeDetails['data']['uri'])) if (setting('useProxy') == 'true') else episodeDetails['data']['uri']
        plot = episodeDetails['data']['plot']
        fanart = episodeDetails['data']['fanart']
        liz = xbmcgui.ListItem(name, path=url, thumbnailImage=thumbnail, iconImage="DefaultVideo.png")
        liz.setInfo(type='Video', infoLabels={ 'Title': name, 'Plot': plot })
        liz.setProperty('fanart_image', fanart)
        liz.setProperty('IsPlayable', 'true')
        try: 
            return xbmcplugin.setResolvedUrl(thisPlugin, True, liz)
        except: 
            showNotification(lang(57020), lang(50004))
    else:
        if (not episodeDetails) or ('viewingNotAllowed' in episodeDetails) or (episodeDetails and 'errorCode' in episodeDetails and episodeDetails['errorCode'] != 0):
            if 'StatusMessage' in episodeDetails:
                showNotification(episodeDetails['StatusMessage'])
            else:
                showNotification(lang(57001), lang(50009))
    return False
    
def getMediaInfo(episodeId):
    mediaInfo = getMediaInfoFromWebsite(episodeId)
    if mediaInfo and 'errorCode' in mediaInfo and mediaInfo['errorCode'] == 1:
        mediaInfo['errorCode'] = 0
    return mediaInfo
    
def getMediaInfoFromWebsite(episodeId):
    mediaInfo = {}
    url = '/episode/details/%s'
    html = callServiceApi(url % episodeId, base_url = websiteUrl, useCache=False)
    body = common.parseDOM(html, 'body')
    episodeData = json.loads(re.compile('var ldj = (\{.+\})', re.IGNORECASE).search(html).group(1))
    
    # Parental advisory
    if re.compile('var dfp_c = ".*2900.*";', re.IGNORECASE).search(html):
        if setting('parentalAdvisoryCheck') == 'true':
            alert(lang(57011),title=lang(50003))
        if setting('parentalControl') == 'true':
            code = numpad(lang(57021))
            if code != setting('parentalCode'):
                mediaInfo['viewingNotAllowed'] = True
                mediaInfo['StatusMessage'] = lang(57022)
                mediaInfo['errorCode'] = 0
                mediaInfo['data'] = {}
                return mediaInfo
            
    sid = None
    sidmatch = re.compile('(media/fetch.+sid: (\d+),)', re.IGNORECASE).search(html)
    if sidmatch:
        sid = sidmatch.group(2)
            
    if sid:
        cookie = getCookieContent() 
        log(cookie)
        if setting('generateNewFingerprintID') == 'true':
            generateNewFingerprintID()
        
        cookie.append('cc_fingerprintid='+setting('fingerprintID'))
        if setting('previousFingerprintID') != '':
            cookie.append('cc_prevfingerprintid='+setting('previousFingerprintID'))
        
        callHeaders = [
            ('Accept', 'application/json, text/javascript, */*; q=0.01'), 
            ('X-Requested-With', 'XMLHttpRequest'),
            ('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8'),
            ('Cookie', '; '.join(cookie)),
            ('Host', 'tfc.tv'),
            ('Origin', websiteUrl),
            ('Referer', websiteUrl+'/')
            ]
        params = {
            'eid': episodeId, 
            'pv': 'false', 
            'sid' : sid
            }
        episodeDetails = callJsonApi('/media/fetch', params, headers=callHeaders, base_url=websiteSecuredUrl, useCache=False, jsonData=True)
        if episodeDetails and 'StatusCode' in episodeDetails:
            mediaInfo['errorCode'] = episodeDetails['StatusCode']
            if 'media' in episodeDetails and 'source' in episodeDetails['media'] and 'src' in episodeDetails['media']['source'][0] :
                episodeDetails['media']['uri'] = episodeDetails['media']['source'][0]['src'].encode('utf8')
                # DVR Window 
                # episodeDetails['media']['uri'] += '&dw=30&n10'
                # limit by bitrate
                # episodeDetails['media']['uri'] += '&b=700-1800'
                # prefered bitrate
                # episodeDetails['media']['uri'] += '&_b_=1800'
                if setting('streamServerModification') == 'true' and setting('streamServer') != '':
                    episodeDetails['media']['uri'] = episodeDetails['media']['uri'].replace('https://o2-i.', setting('streamServer'))                
                
                # choose best stream quality
                if (setting('chooseBestStream') == 'true'):
                    m3u8 = callServiceApi(episodeDetails['media']['uri'], base_url = '', headers=[])
                    lines = m3u8.split('\n')
                    i = 0
                    bandwidth = 0
                    choosedStream = ''
                    for l in lines:
                        match = re.compile('BANDWIDTH=([0-9]+)', re.IGNORECASE).search(lines[i])
                        if match :
                            if int(match.group(1)) > bandwidth:
                                bandwidth = int(match.group(1))
                                choosedStream = lines[i+1]
                            i+=2
                        else:
                            i+=1
                        if i >= len(lines):
                            break
                    episodeDetails['media']['uri'] = choosedStream
                
                mediaInfo['data'] = episodeDetails['media']
                mediaInfo['data']['plot'] = episodeData.get('description').encode('utf8')
                mediaInfo['data']['fanart'] = episodeData.get('image').encode('utf8')
                mediaInfo['data']['type'] = episodeData.get('@type').encode('utf8').lower()
                
            if 'StatusMessage' in episodeDetails and episodeDetails['StatusMessage'] != '' and episodeDetails['StatusMessage'] != 'OK':
                mediaInfo['StatusMessage'] = episodeDetails['StatusMessage']
                
    return mediaInfo
    
def showMyAccount():
    checkAccountChange(False)
    categories = [
        { 'name' : 'My info', 'url' : '/profile', 'mode' : 13 },
        { 'name' : 'My subscription', 'url' : '/', 'mode' : 14 },
        { 'name' : 'Transactions', 'url' : '/', 'mode' : 15 }
    ]
    for c in categories:
        addDir(c['name'], c['url'], c['mode'], 'icon.png')
    addDir('Logout', '/', 16, 'icon.png', isFolder = False)    
    xbmcplugin.endOfDirectory(thisPlugin)
    
def showMyInfo():
    loggedIn = isLoggedIn()
    message = lang(57002)
    if loggedIn == True:
        try:
            user = getUserInfo()
            message = 'First name: %s\nLast name: %s\nEmail: %s\nState: %s\nCountry: %s\nMember since: %s\n\n' % (
                user.get('firstName', ''),
                user.get('lastName', ''), 
                user.get('email', ''), 
                user.get('state', ''),
                user.get('country', ''), 
                user.get('memberSince', '')
                )
        except:
            pass
    showMessage(message, lang(56001))
    
def showMySubscription():
    sub = getUserSubscription()
    message = ''
    if sub:
        message += '%s' % (sub['Details'])
    else:
        message = lang(57002)
    showMessage(message, lang(56002))
    
def showMyTransactions():
    transactions = getUserTransactions()
    message = ''
    if len(transactions) > 0:
        for t in transactions:
            message += t + "\n"
    else:
        message = lang(57002)
    showMessage(message, lang(56003))
        
def reloadCatalogCache():
    res = updateCatalogCache()
    if res is True:
        showNotification(lang(57003), lang(50001))
    
def updateCatalogCache():
    showNotification(lang(57015))
    longCache.cacheClean(True)
    shortCache.cacheClean(True)
    
    # update sections cache
    if setting('displayWebsiteSections') == 'true':
        showNotification(lang(57013))
        sections = sCacheFunction(getWebsiteHomeSections)
        for section in sections:
            sCacheFunction(getWebsiteSectionContent, section['id'])
    
    # update categories cache
    showNotification(lang(57014))
    categories = lCacheFunction(getCategories)
    for cat in categories:
        subCategories = lCacheFunction(getSubCategories, cat['id'])
        for sub in subCategories:
            shows = sCacheFunction(getShows, sub['id'])
            for s in shows:
                show = lCacheFunction(getShow, s['id'])
                # if show:
                    # episodes = sCacheFunction(getShowEpisodes, show['id'])
    return True
    
    
def getSiteMenu():
    data = []
    
    html = callServiceApi('', base_url = websiteUrl)
    menu = common.parseDOM(html, "div", attrs = { 'id' : 'main_nav_desk' })[0]
    categories = common.parseDOM(menu, "li", attrs = { 'class' : 'has_children' })
    
    for category in categories:
        
        subCategories = []
        name = common.parseDOM(category, "a")[0]
        id = common.parseDOM(category, "a", ret = 'data-id')[0]
        url = common.parseDOM(category, "a", ret = 'href')[0]
        menuitem = common.parseDOM(category, "ul", attrs = { 'class' : 'menu_item' })[0]
        subcatlist = common.parseDOM(menuitem, "li")
        
        for subcat in subcatlist:
            subcatname = common.parseDOM(subcat, "a")[0]
            subcaturl = common.parseDOM(subcat, "a", ret = 'href')[0]
            id = re.compile('/([0-9]+)/', re.IGNORECASE).search(subcaturl).group(1)
        
            subCategories.append({
                'id' : str(id), 
                'name' : common.replaceHTMLCodes(subcatname), 
                'url' : subcaturl
                })
        
        data.append({
            'id' : str(id), 
            'name' : common.replaceHTMLCodes(name), 
            'url' : url, 
            'subcat' : subCategories
            })
    return data
    
def getCategories():
    data = getSiteMenu()
    return data
    
def getSubCategories(categoryId):
    data = []
    categoryData = getSiteMenu()
    for c in categoryData:
        if str(c['id']) == categoryId:
           data = c['subcat']
           break
    return data
    
def getMyListCategories():
    url = '/user/mylist'
    html = callServiceApi(url)
    return extractListCategories(html)
    
def getMylistCategoryItems(id):
    url = '/user/mylist'
    html = callServiceApi(url)
    return extractListCategoryItems(html, id)

def extractListCategoryItems(html, id):   
    data = []
    
    section = common.parseDOM(html, "section", attrs = { 'id' : id })
    content = common.parseDOM(section, "ul", attrs = { 'class' : 'og-grid tv-programs-grid' })
    if len(content) > 0:
        items = common.parseDOM(content, "li")
        
        for item in items:
            url = common.parseDOM(item, "a", ret = 'href')[0]
            if '/show/' in url:
                data.append(extractMyListShowData(url, item))
            elif '/episode/' in url:
                data.append(extracMyListEpisodeData(url, item))
    
    return data
    
def extractMyListShowData(url, html):
    showId = re.compile('/([0-9]+)/', re.IGNORECASE).search(url).group(1)
    showName = common.replaceHTMLCodes(common.parseDOM(html, "div", attrs = { 'class' : 'show-cover-thumb-title-mobile sub-category' })[0])
    image = common.parseDOM(html, "img", ret = 'src')[0]
    
    return {
        'type' : 'show',
        'id' : int(showId),
        'parentid' : -1,
        'parentname' : '',
        'name' : common.replaceHTMLCodes(showName).encode('utf8'),
        'image' : image,
        'description' : '',
        'shortdescription' : '',
        'year' : '',
        'fanart' : image
        }

def extracMyListEpisodeData(url, html):
    episodeId = re.compile('/([0-9]+)/', re.IGNORECASE).search(url).group(1)
    showName = common.replaceHTMLCodes(common.parseDOM(html, "h2", attrs = { 'class' : 'show-cover-thumb-title-mobile sub-category' })[0])
    image = common.parseDOM(html, "img", ret = 'src')[0]
    dateAired = common.parseDOM(html, "h3", attrs = { 'class' : 'show-cover-thumb-title-mobile sub-category' })
    
    year = ''
    episodeNumber = 0
    description = ''
    episodeName = ''
    
    if dateAired and len(dateAired) > 0:
        episodeName = dateAired[0].replace('AIRED:', '')
        year = episodeName.split(', ')[1]
    
    return {
        'id' : int(episodeId), 
        'parentid' : -1,
        'parentname' : '',
        'title' : common.replaceHTMLCodes('%s - %s' % (showName, episodeName)).encode('utf8'), 
        'show' : showName.encode('utf8'), 
        'image' : image, 
        'episodenumber' : episodeNumber,
        'url' : url, 
        'description' : '',
        'shortdescription' : '',
        'dateaired' : episodeName.encode('utf8'),
        'year' : year,
        'fanart' : image,
        'type' : 'episode'
        }
    
def extractListCategories(html):
    data = []
    
    nav = common.parseDOM(common.parseDOM(html, "nav"), "li")
    for li in nav:
        name, count = common.stripTags(common.parseDOM(li, "a")[0]).split(' ', 1)
        data.append({
            'id' : common.parseDOM(li, "a", ret = 'href')[0].replace('#', ''),
            'name' : '%s (%s)' % (name.title(), count)
            })
    # listCat = common.parseDOM(html, "section", attrs = { 'class' : 'sub-category-page' }, ret = 'id')
    # int(re.compile('/([0-9]+)/', re.IGNORECASE).search(url).group(1))
    return data

def getWebsiteHomeSections():   
    data = []
    html = callServiceApi('/home', base_url = websiteUrl)
    sections = common.parseDOM(html, "div", attrs = { 'class' : 'main-container-xl main-container-xl-mobile' })
    i = 1
    for section in sections:
        header = common.parseDOM(section, "a", attrs = { 'class' : 'h2 heading-slider first' })
        if len(header):
            sectionName = common.stripTags(common.replaceHTMLCodes(header[0])).strip()
            exceptSections = [
                'CONTINUE WATCHING', 
                'MY LIST', 
                'IWANT ORIGINALS - EXCLUSIVE FOR PREMIUM'
                ]
            if sectionName not in exceptSections:
                data.append({'id' : str(i), 'name' : sectionName}) #, 'url' : '/', 'fanart' : ''})
        i += 1
    return data
    
def getWebsiteSectionContent(sectionId, page=1, itemsPerPage=8):
    page -= 1
    data = []
    
    html = callServiceApi('/home', base_url = websiteUrl)
    sections = common.parseDOM(html, "div", attrs = { 'class' : 'main-container-xl main-container-xl-mobile' })
    section = sections[int(sectionId)-1]
    links = common.parseDOM(section, "a", attrs = { 'data-category' : 'CTA_Sections' }, ret = 'href')
    items = common.parseDOM(section, "a", attrs = { 'data-category' : 'CTA_Sections' })
    
    index = itemsPerPage * page
    i = 0
    for s in items:
        i += 1
        if i > index:
            url = links[i-1]

            if '/show/' in url:
                data.append(extractWebsiteSectionShowData(url, s))
            elif '/episode/' in url:
                data.append(extractWebsiteSectionEpisodeData(url, s))
                
        if i >= (index + itemsPerPage):
            break
            
    return data
    
def extractWebsiteSectionShowData(url, html):
    
    showId = re.compile('/([0-9]+)/', re.IGNORECASE).search(url).group(1)
    filter = 'port-cover-thumb-title' if 'port-cover-thumb-title' in html else 'show-cover-thumb-title-mobile'
    showName = common.replaceHTMLCodes(common.parseDOM(html, "h3", attrs = { 'class' : filter })[0])
    image = common.parseDOM(html, "div", attrs = { 'class' : 'show-cover' }, ret = 'data-src')[0]
    
    return {
        'type' : 'show',
        'id' : int(showId),
        'parentid' : -1,
        'parentname' : '',
        'name' : common.replaceHTMLCodes(showName).encode('utf8'),
        'image' : image,
        'description' : '',
        'shortdescription' : '',
        'year' : '',
        'fanart' : image
        }

def extractWebsiteSectionEpisodeData(url, html):
    episodeId = re.compile('/([0-9]+)/', re.IGNORECASE).search(url).group(1)
    showName = common.replaceHTMLCodes(common.parseDOM(html, "h3", attrs = { 'class' : 'show-cover-thumb-title-mobile' })[0])
    image = common.parseDOM(html, "div", attrs = { 'class' : 'show-cover' }, ret = 'data-src')[0]
    dateAired = common.parseDOM(html, "h4", attrs = { 'class' : 'show-cover-thumb-aired-mobile' })
    
    year = ''
    episodeNumber = 0
    description = ''
    episodeName = ''
    
    if dateAired and len(dateAired) > 0:
        episodeName = dateAired[0]
        year = episodeName.split(', ')[1]
    
    return {
        'id' : int(episodeId), 
        'parentid' : -1,
        'parentname' : '',
        'title' : common.replaceHTMLCodes('%s - %s' % (showName, episodeName)).encode('utf8'), 
        'show' : showName.encode('utf8'), 
        'image' : image, 
        'episodenumber' : episodeNumber,
        'url' : url, 
        'description' : '',
        'shortdescription' : '',
        'dateaired' : episodeName.encode('utf8'),
        'year' : year,
        'fanart' : image,
        'type' : 'episode'
        }

def getShows(subCategoryId, page = 1):
    data = []
    subCategoryShows = []
    
    url = '/category/list/%s'
    html = callServiceApi(url % subCategoryId)
    
    subCategoryShows.append(extractShows(html))
    
    pagination = common.parseDOM(html, 'ul', attrs = { 'id' : 'pagination' })    
    pages = common.parseDOM(pagination, 'a', ret = 'href')
    if len(pages) > 1:
        for url in pages[1:]:
            subCategoryShows.append(extractShows(callServiceApi(url)))
    
    if len(subCategoryShows) > 0:
        for sub in subCategoryShows:
            for d in sub:
                description = d['blurb'] if 'blurb' in d else ''
                dateAired = d['dateairedstr'] if 'dateairedstr' in d else ''
                data.append({
                    'id' : int(d['id']),
                    'parentid' : d['parentid'],
                    'parentname' : d['parentname'].encode('utf8'),
                    'name' : d['name'].encode('utf8'),
                    'image' : d['image'].replace(' ', '%20'),
                    'description' : d['description'].encode('utf8'),
                    'shortdescription' : d['shortdescription'].encode('utf8'),
                    'year' : dateAired,
                    'fanart' : d['image'].replace(' ', '%20')
                    })
                
    return data
    
def extractShows(html):
    data = []
    list = common.parseDOM(html, "ul", attrs = { 'id' : 'og-grid' })[0]
    shows = common.parseDOM(list, "li", attrs = { 'class' : 'og-grid-item-o' })
    for show in shows:
        name = common.parseDOM(show, "h2")[0]
        aired = common.parseDOM(show, "h3")[0]
        image = common.parseDOM(show, "img", ret = 'src')[0]
        url = common.parseDOM(show, "a", ret = 'href')[0]
        id = re.compile('/([0-9]+)/', re.IGNORECASE).search(url).group(1)
        
        data.append({
            'id' : id,
            'parentid' : -1,
            'parentname' : '',
            'name' : common.replaceHTMLCodes(name),
            'url' : url,
            'image' : image,
            'description' : '',
            'shortdescription' : '',
            'dateairedstr' : aired
            })
            
    return data

def getShow(showId):
    data = {}
    
    url = '/show/details/%s'
    html = callServiceApi(url % showId)
    
    images = common.parseDOM(html, "div", attrs = { 'class' : 'hero-image-logo' })
    if len(images) == 0:
        image = common.parseDOM(html, "link", attrs = { 'rel' : 'image_src' }, ret = 'href')[0]
    else:
        image = common.parseDOM(images, "img", ret = "src")[0]
    
    banners = common.parseDOM(html, "div", attrs = { 'class' : 'header-hero-image topic-page' }, ret = 'style')
    if len(banners) == 0:
        banners = common.parseDOM(html, "div", attrs = { 'class' : 'header-hero-image' }, ret = 'style')
    if len(banners) == 0:
        banners = common.parseDOM(html, "div", attrs = { 'id' : 'detail-video' }, ret = 'style')
    if banners:
        banner = re.compile('url\((.+)\);', re.IGNORECASE).search(banners[0]).group(1)
    else:
        banner = image
        
    name = common.parseDOM(html, "meta", attrs = { 'property' : 'og:title' }, ret = "content")[0]
    description = common.parseDOM(html, "div", attrs = { 'class' : 'celeb-desc-p' })[0]
    genres = common.parseDOM(html, "a", attrs = { 'class' : 'text-primary genre-deets' })
    genre = '' if len(genres) == 0 else genres[0]
    
    # Check episode list
    episodes = {}
    episodeList = common.parseDOM(html, "select", attrs = { 'id' : 'show_episode_list' })
    if episodeList:
        values = common.parseDOM(episodeList, "option", ret = 'value')
        titles = common.parseDOM(episodeList, "option")
        i = 0
        for t in titles:
            id = int(re.compile('/([0-9]+)/', re.IGNORECASE).search(values[i]).group(1))
            episodes.update({id : {
                'title' : common.replaceHTMLCodes(t),
                'episodenumber' : int(re.compile('Ep. ([0-9]+) -', re.IGNORECASE).search(t).group(1)),
                'url' : values[i]
                }})
            i+=1
    
    data = {
        'id' : int(showId),
        'parentid' : -1,
        'parentname' : common.replaceHTMLCodes(genre).encode('utf8'),
        'name' : common.replaceHTMLCodes(name).encode('utf8'),
        'image' : image,
        'description' : common.replaceHTMLCodes(description).encode('utf8'),
        'shortdescription' : common.replaceHTMLCodes(description).encode('utf8'),
        'year' : '',
        'fanart' : banner,
        'episodes' : episodes
        }
        
    return data
    
def formatMenu():
    bgImage = setting('defaultBG')
    data = { 
        'listArts' : { 'fanart' : bgImage, 'banner' : bgImage }
        }
    return data
    
def formatShowInfo(info, addToList=True, options = {}):
    add = { lang(50300) : 'XBMC.Container.Update(%s)' % generatePluginActionUrl(str(info['id']), 22, info['name']) } 
    remove = { lang(50301) : 'XBMC.Container.Update(%s)' % generatePluginActionUrl(str(info['id']), 23, info['name']) } 
    contextMenu = add if addToList == True else remove
    
    data = { 
        'listArts' : { 'fanart' : info['fanart'], 'banner' : info['fanart'] }, 
        'listInfos' : { 
            'video' : { 'plot' : info['description'], 'year' : info['year'] } 
            },
        'contextMenu' : contextMenu
        }
    return data
        
def formatVideoInfo(info, addToList=True, options = {}):
    add = { lang(50300) : 'XBMC.Container.Update(%s)' % generatePluginActionUrl(str(info['id']), 24, info['title']) } 
    remove = { lang(50301) : 'XBMC.Container.Update(%s)' % generatePluginActionUrl(str(info['id']), 25, info['title']) } 
    contextMenu = add if addToList == True else remove

    data = { 
        'listArts' : { 'fanart' : info['fanart'], 'banner' : info['fanart'] }, 
        'listProperties' : { 'IsPlayable' : 'true' } , 
        'listInfos' : { 
            'video' : { 
                'tvshowtitle' : info['show'], 
                'episode' : info['episodenumber'], 
                'tracknumber' : info['episodenumber'], 
                'plot' : info['description'], 
                'aired' : info['dateaired'], 
                'year' : info['year'] 
                } 
            },
        'contextMenu' : contextMenu
        }
    return data

def getEpisodesPerPage(showId, page=1, itemsPerPage=8):
    data = []
    
    # max nb items per page that TFC website can provide
    websiteNbItemsPerPage = 8
    # Calculating page index and needed pages to request for building next page to display
    firstPage = 1 if page == 1 else ((itemsPerPage / websiteNbItemsPerPage) * (page - 1) + 1)
    lastPage = itemsPerPage / websiteNbItemsPerPage * page
    
    paginationURL = '/modulebuilder/getepisodes/%s/show/%s'
    showDetails = sCacheFunction(getShow, showId)
    
    for page in range(firstPage, lastPage+1, 1):
        html = callServiceApi(paginationURL % (showId, page))
    
        # if page does not exist
        if page > 1 and html == '':
            break
        # if no pagination, it's a movie or special
        elif page == 1 and html == '':
            showDetailURL = '/show/details/%s'
            html = callServiceApi(showDetailURL % showId)
            episodeId = int(re.compile('var dfp_e = "(.+)";', re.IGNORECASE).search(html).group(1))
            data.append({
                'id' : episodeId,
                'title' : showDetails.get('name'),
                'show' : showDetails.get('name'),
                'image' : showDetails.get('image'),
                'episodenumber' : 0,
                'description' : showDetails.get('description'),
                'shortdescription' : showDetails.get('description'),
                'dateaired' : '',
                'year' : showDetails.get('year'),
                'fanart' : showDetails.get('fanart')
                })
                
            break
        else:
            i = 0
            episodes = common.parseDOM(html, 'li', attrs = {'class' : 'og-grid-item'})
            descriptions = common.parseDOM(html, 'li', attrs = {'class' : 'og-grid-item'}, ret = 'data-show-description')
            titles = common.parseDOM(html, 'li', attrs = {'class' : 'og-grid-item'}, ret = 'data-aired')
            
            for e in episodes:
                url = common.parseDOM(e, "a", ret = 'href')[0]
                episodeId = int(re.compile('/([0-9]+)/', re.IGNORECASE).search(url).group(1))
                image = common.parseDOM(e, "div", attrs = {'class' : 'show-cover'}, ret = 'data-src')[0]
                title = common.replaceHTMLCodes(titles[i])
                dateAired = title
                showTitle = showDetails.get('name')
                fanart = showDetails.get('fanart')
                year = title.split(', ').pop()
                description = common.replaceHTMLCodes(descriptions[i])
                shortDescription = description
                episodeNumber = 0
                
                episodeData = showDetails.get('episodes').get(episodeId)
                if episodeData:
                    title = episodeData.get('title')
                    episodeNumber = episodeData.get('episodenumber')
                
                data.append({
                    'id' : episodeId,
                    'title' : title.encode('utf8'),
                    'show' : showTitle,
                    'image' : image,
                    'episodenumber' : episodeNumber,
                    'description' : description.encode('utf8'),
                    'shortdescription' : shortDescription.encode('utf8'),
                    'dateaired' : dateAired,
                    'year' : year,
                    'fanart' : fanart
                    })
                    
                i += 1
            
    # return sorted(data, key=lambda episode: episode['title'], reverse=True)
    return data
      
def getShowEpisodes(showId):
    data = {}
    showData = sCacheFunction(getShow, showId)
    url = '/Episodes?showId=%s'
    showEpisodes = callJsonApi(url % showId)
    if showData and showEpisodes:
        for e in showEpisodes:
            e['show'] = showData.get('name')
            e['showimage'] = showData.get('image').replace(' ', '%20')
            e['fanart'] = showData.get('banner').replace(' ', '%20')
            e['image'] = e.get('ImageList')
            e['description'] = e.get('Synopsis')
            e['shortdescription'] = e.get('Description')
            e['episodenumber'] = e.get('EpisodeNumber')
            e['dateaired'] = e.get('DateAired').split('T')[0]
            data[e.get('EpisodeId')] = e
    return data
      
def getEpisodeDataByShow(showId, episodeId):
    data = {}
    episodes = sCacheFunction(getShowEpisodes, showId)
    if episodes and episodeId in episodes:
        data = episodes[episodeId]
    else:
        episode = lCacheFunction(getEpisodeData, episodeId)
        if episode:
            episode['title'] = episode.get('dateaired')
            episode['description'] = episode.get('synopsis')
            data = episode
    return data
    
def getEpisodeData(episodeId):
    data = {}
    url = '/Episode?episodeId=%s'
    res = callJsonApi(url % episodeId)
    if 'statusCode' in res and res['statusCode'] == 1:
        data = res['episode']
        data['title'] = data['streamInfo']['streamTitle']
        data['url'] = data['streamInfo']['streamURL']
        data['dateaired'] = data['dateAired'].split('T')[1]
        data['year'] = data['dateAired'].split('-')[0]
        data['description'] = data['synopsis']
        data['image'] = data['image']['video']
    return data
    
def getEpisodeVideo(episodeId):
    data = {}
    url = '/Media?episodeId=%s&isPv=false'
    res = callJsonApi(url % episodeId, useCache = False)
    if res and 'statusCode' in res:
        data = res
        data['errorCode'] = 1 if res['statusCode'] == 0 else 0
            
    return data
    
def getCelebrities():
    data = []
    url = '/Synapse/GetAllCelebrities'
    data = callJsonApi(url)
    return data
    
def getUserInfo():
    url = '/profile'
    html = callServiceApi(url, useCache = False)
    
    # Retrieve info from website
    profileHeader = common.parseDOM(html, 'div', attrs = {'class' : 'profile_header'})
    name = common.parseDOM(profileHeader, 'div', attrs = {'class' : 'name'})[0]
    state = common.parseDOM(profileHeader, 'div', attrs = {'class' : 'name'})[0]
    memberSince = common.parseDOM(profileHeader, 'div', attrs = {'class' : 'date'})[0]    
    
    # Retrieve info from account JSON string
    user = json.loads(setting('accountJSON')).get('profile')
    
    return {
        'name' : name.encode('utf8'),
        'firstName' : user.get('firstName', '').encode('utf8'),
        'lastName' : user.get('lastName', '').encode('utf8'),
        'email' : user.get('email', '').encode('utf8'),
        'state' : state.encode('utf8'),
        'country' : user.get('country', '').encode('utf8'),
        'memberSince' : memberSince.replace('MEMBER SINCE ', '').encode('utf8')
    }
    
def getUserSubscription():
    url = '/profile/details'
    subscription = callJsonApi(url, useCache=False)
    
    first_cap_re = re.compile('(.)([A-Z][a-z]+)')
        
    subKeys = ['Type', 'SubscriptionName', 'SubscriptionStatus', 'ExpirationDate', 'ExpirationDate', 'BillingPeriod', 'AutoRenewal']
    details = ''
    if 'Details' in subscription:
        for d in subscription['Details']:
            for key in subKeys:
                label = first_cap_re.sub(r'\1 \2', key)
                if key in d:
                    value = ''
                    if isinstance(d[key], (bool)):
                        value = 'ACTIVE' if d[key] == True else 'NON ACTIVE'
                    else:
                        value = d[key]
                    details += "%s: %s\n" % (label, value)
            details += "\n"
    return {
            'Details' : details
        }
    
def getUserTransactions():
    TAG_HTML = re.compile('<[^>]+>')

    data = []
    url = '/profile'
    html = callServiceApi(url, useCache = False)
    
    transactionsHtml = common.parseDOM(html, 'div', attrs = {'id' : 'transactions'})
    transactions = common.parseDOM(common.parseDOM(transactionsHtml, 'tbody'), 'tr')
    
    header = []
    headers = common.parseDOM(common.parseDOM(transactionsHtml, 'thead'), 'th')
    for h in headers:
        header.append(h.encode('utf8'))
    
    for transaction in transactions:
        columns = common.parseDOM(transaction, 'td', attrs = {'class' : 'loader'})
        if len(columns) > 0:
            continue
        
        columns = common.parseDOM(transaction.replace('<td></td>', '<td>-</td>'), 'td')
        t = ''
        i = 0
        
        for c in columns:
            value = '-'
            if not TAG_HTML.search(c):
                value = c.encode('utf8')
            t += "%s: %s\n" % (header[i], value)
            i+=1
        data.append(t)
                
    return data
    
def addToMyList(url, name, type):
    log(url)
    showNotification(lang(57026))
    # url = '/method/addtolist'
    # data = callJsonApi(url, params = {'CategoryId': 4894, 'EpisodeId': 167895, 'type': 'episode'}, useCache=False)

def removeFromMyList(url, name, type):
    log(url)
    showNotification(lang(57026))
    # url = '/method/deletefromlist'
    # data = callJsonApi(url, params = {'CategoryId': 4894, 'EpisodeId': 167895, 'type': 'episode'}, useCache=False)
    
def checkAccountChange(forceSignIn=False):
    email = setting('emailAddress')
    password = setting('password')
    hash = hashlib.sha1(email + password).hexdigest()
    hashFile = os.path.join(xbmc.translatePath(addonInfo('profile')), 'a.tmp')
    savedHash = ''
    accountChanged = False
    logged = False
    loginSuccess = False
    
    if os.path.exists(hashFile):
        if forceSignIn == True: 
            os.unlink(hashFile)
        else: 
            with open(hashFile) as f:
                savedHash = f.read()
                f.close()
                
    if savedHash != hash:
        accountChanged = True
        logout()
        logged = True
    elif not isLoggedIn():
        log('Not logged in')
        logged = True
    
    if logged:
        loginSuccess = login()
        if loginSuccess == True and os.path.exists(xbmc.translatePath(addonInfo('profile'))):
            with open(hashFile, 'w') as f:
                f.write(hash)
                f.close()
        elif os.path.exists(hashFile)==True: 
            os.unlink(hashFile)
        
    return (accountChanged, loginSuccess)
    
def login(quiet=False):
    signedIntoWebsite = loginToWebsite(quiet)
    return signedIntoWebsite
    
def isLoggedIn():
    html = callServiceApi("/profile", headers = [('Referer', websiteSecuredUrl+'/')    ], base_url = websiteSecuredUrl, useCache = False)
    return False if 'TfcTvId' not in html else True
    
def loginToWebsite(quiet=False): 
    from random import randint
    import time
    global cookieJar
    
    logged = False
    
    if quiet == False:
        showNotification(lang(57019), lang(50005))
    
    emailAddress = addon.getSetting('emailAddress')
    password = addon.getSetting('password')
    authData = { "loginID" : emailAddress, "password": password }
    
    # Init oauth
    params = {
        'client_id' : 'tfconline', 
        'redirect_uri': 'https://tfc.tv/callback', 
        'response_type' : 'id_token token', 
        'scope' : 'openid profile offline_access', 
        'nonce' : time.time()
        }
    callServiceApi(
        '/connect/authorize?' + urllib.urlencode(params),
        base_url = websiteSSOUrl, 
        useCache = False
    )
    
    # Login into kapamilya-accounts
    data = callJsonApi("/api/spa/login", authData, base_url=websiteSSOUrl, useCache = False, jsonData=True)
    if (not data or ('errorCode' in data and data.get('errorCode') != 0) or ('errorMessage' in data)) and quiet == False:
        if 'errorMessage' in data:
            showNotification(data.get('errorMessage'), lang(50006))
        else:
            showNotification(lang(57024), lang(50006))
    else:
    
        gigyaUrl = ''
        gigyaBuild = ''
        gigyaVersion = ''
        gigyaJSON = {}
        apikey = ''
        ssoKey = ''
        loginToken = ''
        UID = ''
        UIDSignature = ''
        
        apikey = getFromCookieByName('app_apikey').value
        
        # Retrieve Gigya version and build
        params = {'apikey' : apikey, '_': time.time()}
        gigyaHtml = callServiceApi(
            '/js/gigya.js?' + urllib.urlencode(params), 
            base_url = gigyaCDNUrl, 
            useCache = False
        )
        gigyaVersion = re.compile('"version":?"([\d.]+)",').search(gigyaHtml).group(1)
        gigyaBuild = re.compile('"number":([\d.]+),').search(gigyaHtml).group(1)
        
        # Retrieve Gigya ssoKey
        params = {'apiKey' : apikey, 'version': gigyaVersion}
        webSdkURI = '/gs/webSdk/Api.aspx?' + urllib.urlencode(params)
        gigyaHtml = callServiceApi(
            webSdkURI, 
            base_url = gigyaCDNUrl, 
            useCache = False
        )
        defaultApiDomain = re.compile('gigya.defaultApiDomain=\'([a-zA-Z.]+)\';').search(gigyaHtml).group(1)
        dataCenter = re.compile('gigya.dataCenter=\'([a-zA-Z0-9.]+)\';').search(gigyaHtml).group(1)
        ssoKey = re.compile('"ssoKey":"([a-zA-Z0-9_-]+)",').search(gigyaHtml).group(1)       
        apiDomainCookie = 'apiDomain_' + ssoKey + '=' + dataCenter + '.' + defaultApiDomain
        apiDomain = dataCenter + '.' + defaultApiDomain
        
        # Retrieve authorization code from cookie
        gacCookie = getFromCookieByName('gac_', startWith=True)
        gacToken = gacCookie.value

        # Retrieve needed cookies
        params = {
            'apiKey' : apikey, 
            'pageURL' : 'https://kapamilya-accounts.abs-cbn.com/signin', 
            'format': 'json', 
            'context' : 'R' + str(randint(10000, 99999)**2)
            }
        callServiceApi(
            '/accounts.webSdkBootstrap?' + urllib.urlencode(params),
            headers = [
                ('Cookie', apiDomainCookie),
                ('Referer', gigyaCDNUrl + webSdkURI)
                ], 
            base_url= gigyaAccountUrl, 
            useCache = False
            )

        params = {
            'APIKey' : ssoKey, 
            'ssoSegment' : '', 
            'version': gigyaVersion, 
            'build' : gigyaBuild
            }
        sso = callServiceApi(
            '/gs/sso.htm?' + urllib.urlencode(params),
            base_url= gigyaSocializeUrl, 
            useCache = False
            )
        
        cookie = getCookieContent(['hasGmid', 'gmid', 'ucid'])   
        cookie.append(apiDomainCookie)
        
        # Retrieve the login token
        params = {
            'sessionExpiration' : -2, 
            'authCode' : gacToken, 
            'APIKey': apikey, 
            'sdk' : 'js_' + gigyaVersion,
            'authMode' : 'cookie',
            'pageURL' : 'https://kapamilya-accounts.abs-cbn.com/welcome',
            'format' : 'json',
            'context' : 'R' + str(randint(10000, 99999)**2)
            }
        gigyaJSON = callJsonApi(
            '/socialize.notifyLogin?' + urllib.urlencode(params),
            headers = [
                ('Cookie', '; '.join(cookie)),
                ('Referer', gigyaCDNUrl + webSdkURI)
                ], 
            base_url= gigyaSocializeUrl, 
            useCache = False
            )
        
        # Retrieve login token from cookie
        if 'errorMessage' in gigyaJSON:
            showNotification(gigyaJSON.get('errorMessage'), lang(50004))
                
        if 'statusCode' in gigyaJSON and gigyaJSON.get('statusCode') == 200 and 'login_token' in gigyaJSON:
            loginToken = gigyaJSON.get('login_token').encode('utf8')
            
            # Retrieve UID, UIDSignature and signatureTimestamp
            params = {
                'include' : 'profile,', 
                'APIKey': apikey, 
                'sdk' : 'js_' + gigyaVersion,
                'login_token' : loginToken,
                'authMode' : 'cookie',
                'pageURL' : 'https://kapamilya-accounts.abs-cbn.com/checksession',
                'format' : 'json',
                'context' : 'R' + str(randint(10000, 99999)**2)
                }
            accountJSON = callJsonApi(
                '/accounts.getAccountInfo?' + urllib.urlencode(params), 
                headers = [
                    ('Cookie', '; '.join(cookie)),
                    ('Referer', gigyaCDNUrl + webSdkURI)
                    ], 
                base_url= gigyaAccountUrl, 
                useCache = False
                )
            
            if 'errorMessage' in accountJSON:
                showNotification(accountJSON.get('errorMessage'), lang(50004))
            
            if 'statusCode' in accountJSON and accountJSON.get('statusCode') == 200:
                
                # get Gmid Ticket
                cookieJar.set_cookie(cookielib.Cookie(version=0, name='gig_hasGmid', value='ver2', port=None, port_specified=False, domain='.tfc.tv', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False))
                cookie = getCookieContent(['hasGmid', 'gmid', 'ucid', 'gig_hasGmid'])   
                cookie.append(apiDomainCookie)
                params = {
                    'apiKey': apikey,
                    'expires' : 3600,
                    'pageURL' : 'https://kapamilya-accounts.abs-cbn.com/welcome',
                    'format' : 'json',
                    'context' : 'R' + str(randint(10000, 99999)**2)
                    }
                gmidJSON = callJsonApi(
                    '/socialize.getGmidTicket?' + urllib.urlencode(params),
                    headers = [
                        ('Cookie', '; '.join(cookie)),
                        ('Referer', gigyaCDNUrl + webSdkURI)
                        ], 
                    base_url= gigyaSocializeUrl, 
                    useCache = False
                    )
                
                if 'statusCode' in gmidJSON and gmidJSON.get('statusCode') == 200 and 'gmidTicket' in gmidJSON:
                    
                    UID = accountJSON.get('UID')
                    UIDSignature = accountJSON.get('UIDSignature')
                    signatureTimestamp = accountJSON.get('signatureTimestamp')
                    
                    addon.setSetting('UID', UID)
                    addon.setSetting('UIDSignature', UIDSignature)
                    addon.setSetting('signatureTimestamp', signatureTimestamp)
                    
                    # Generate authorization
                    redirectParams = {
                        'client_id' : 'tfconline', 
                        'redirect_uri': 'https://tfc.tv/callback', 
                        'response_type' : 'id_token token',
                        'scope' : 'openid profile offline_access',
                        'nonce' : time.time()
                        }
                    # SSOGateway
                    gmidTicket = gmidJSON.get('gmidTicket').encode('utf8')
                    redirectURL = websiteSSOUrl + '/connect/authorize/callback?' + urllib.urlencode(redirectParams)
                    params = {
                        'sessionExpiration' : -2, 
                        'apiDomain' : apiDomain, 
                        'apiKey': apikey, 
                        'gmidTicket' : gmidTicket,
                        'loginToken' : loginToken,
                        'redirectURL' : redirectURL.replace('+', '%20')
                        }
                    SSOGateway = callServiceApi(
                        '/gs/SSOGateway.aspx',
                        params,
                        headers = [
                            ('Cookie', '; '.join(cookie)),
                            ('Origin', 'https://kapamilya-accounts.abs-cbn.com'),
                            ('Referer', 'https://kapamilya-accounts.abs-cbn.com/welcome'),
                            ('Content-Type', 'application/x-www-form-urlencoded')
                            ], 
                        base_url = gigyaSocializeUrl,
                        useCache = False
                        )
                    UUID = re.compile('UUID=([a-zA-Z0-9.]+)\';').search(SSOGateway).group(1)
                    
                    # gltAPIToken = urllib.urlencode({ 'glt_' + apikey : loginToken + '|UUID=' + UUID })
                    cookieJar.set_cookie(cookielib.Cookie(version=0, name='glt_' + apikey, value=loginToken + '|UUID=' + UUID, port=None, port_specified=False, domain='.tfc.tv', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False))
                    gltSSOToken = urllib.urlencode({ 'glt_' + ssoKey : loginToken + '|UUID=' + UUID })
                    # writeFile('additionalCookie', '; '.join([apiDomainCookie, gltAPIToken, 'gig_hasGmid=ver2']))
                    
                    cookie = getCookieContent(exceptFilter=[gacCookie.name]) 
                    cookie.append(apiDomainCookie)
                    cookie.append(gltSSOToken)
                    
                    # Authorize callback URL
                    callServiceApi(
                        '/connect/authorize/callback?' + urllib.urlencode(redirectParams),
                        headers = [
                            ('Cookie', '; '.join(cookie))
                        ], 
                        base_url = websiteSSOUrl, 
                        useCache = False
                        )
                        
                    # Authenticate into TFC.tv
                    params = {
                        'u' : UID, 
                        's' : UIDSignature, 
                        't' : signatureTimestamp,
                        'returnUrl' : '/' 
                        }
                    html = callServiceApi(
                        '/sso/authenticate?' + urllib.urlencode(params), 
                        headers = [
                            ('Cookie', '; '.join(cookie)),
                            ('Referer', websiteUrl+'/')
                        ], 
                        base_url = websiteUrl, 
                        useCache = False
                        )
                    log(cookieJar)
                    # If no error, check if connected
                    if 'TFC - Error' not in html:
                        # Check if session OK
                        params = {
                            'u' : UID, 
                            's' : UIDSignature, 
                            't' : signatureTimestamp
                            }
                        checksession = callJsonApi(
                            '/sso/checksession?' + urllib.urlencode(params), 
                            headers = [
                                ('Cookie', '; '.join(cookie)),
                                ('Referer', websiteUrl+'/')
                            ], 
                            base_url = websiteUrl, 
                            useCache = False
                            )
                    
                    if checksession and 'StatusCode' in checksession and checksession.get('StatusCode') == 0:
                        logged = True
                        generateNewFingerprintID()
                    
        if quiet == False:
            if logged == True:
                addon.setSetting('accountJSON', json.dumps(accountJSON))
                showNotification(lang(57009) % accountJSON.get('profile').get('firstName'), lang(50007))
            else:
                showNotification(lang(57024), lang(50006))
            
    return logged 
    
def getFromCookieByName(string, startWith=False):
    global cookieJar
    cookieObj = None
    
    for c in cookieJar:
        if (startWith and c.name.startswith(string)) or (not startWith and c.name == string) :
            cookieObj = c
            break
                
    return cookieObj
    
def getCookieContent(filter=False, exceptFilter=False):
    global cookieJar
    cookie = []
    for c in cookieJar:
        if (filter and c.name not in filter) or (exceptFilter and c.name in exceptFilter):
            continue
        cookie.append('%s=%s' % (c.name, c.value))
    return cookie

def generateNewFingerprintID(previous=False):
    from random import randint
    if previous == False:
        addon.setSetting('previousFingerprintID', setting('fingerprintID'))
    else:
        addon.setSetting('previousFingerprintID', previous)
    addon.setSetting('fingerprintID', hashlib.md5(setting('emailAddress')+str(randint(0, 1000000))).hexdigest())
    if setting('generateNewFingerprintID') == 'true':
        addon.setSetting('generateNewFingerprintID', 'false')
    return True
    
def logout(quiet=True):
    # https://kapamilya-accounts.abs-cbn.com/api/spa/SSOLogout
    if quiet == False and isLoggedIn() == False:
        showNotification(lang(57000), lang(50005))
    callServiceApi("/logout", headers = [('Referer', websiteUrl+'/')], base_url = websiteUrl, useCache = False)
    cookieJar.clear()
    if quiet == False and isLoggedIn() == False:
        showNotification(lang(57010))
        xbmc.executebuiltin("XBMC.Container.Update(path,replace)")

def generateHashKey(string):
    return hashlib.md5(string).hexdigest()

def callServiceApi(path, params = {}, headers = [], base_url = websiteUrl, useCache = True, jsonData=False):
    global cacheActive, cookieJar
    
    res = ''
    cached = False
    toCache = False
    
    key = generateHashKey(base_url + path + urllib.urlencode(params))
    log('Key %s : %s - %s' % (key, base_url + path, params))
    
    if useCache == True:
        if cacheActive == 'true':
            if shortCache.get(key):
                cached = True
                res = shortCache.get(key)
                log('Used cache for (%s)' % key)
            else:
                toCache = True
                log('No cache for (%s)' % key)
        else:
            if key in sessionCache:
                cached = True
                res = sessionCache[key]
                log('Used session cache for (%s)' % key)
            else:
                toCache = True
                log('No session cache for (%s)' % key)
    
    if cached is False:
        opener = urllib2.build_opener(urllib2.HTTPRedirectHandler(), urllib2.HTTPCookieProcessor(cookieJar))
        userAgent = userAgents[base_url] if base_url in userAgents else userAgents['default']
        headers.append(('User-Agent', userAgent))
        opener.addheaders = headers
        log('### Request headers, URL & params ###')
        log(headers)
        log('%s - %s' % (base_url + path, params))
        requestTimeOut = int(setting('requestTimeOut')) if setting('requestTimeOut') != '' else 20
        response = None
        
        try:
            if params:
                if jsonData == True:                    
                    request = urllib2.Request(base_url + path)
                    request.add_header('Content-Type', 'application/json')
                    response = opener.open(request, json.dumps(params), timeout = requestTimeOut)
                else:
                    data_encoded = urllib.urlencode(params)
                    response = opener.open(base_url + path, data_encoded, timeout = requestTimeOut)
            else:
                response = opener.open(base_url + path, timeout = requestTimeOut)
                
            log('### Response headers ###')
            log(response.geturl())
            log('### Response redirect URL ###')
            log(response.info())
            res = response.read() if response else ''
            log('### Response ###')
            log(res)
        except (urllib2.URLError, ssl.SSLError) as e:
            log(e)
            message = '%s : %s' % (e, base_url + path)
            # message = "Connection timeout : " + base_url + path
            log(message)
            showNotification(message)
        
        if toCache == True and res:
            if cacheActive == 'true':
                shortCache.set(key, res)
                log('Stored in cache (%s) : %s' % (key, res))
            else:
                sessionCache[key] = res
                log('Stored in session cache (%s) : %s' % (key, res))
    
    return res

def callJsonApi(path, params = {}, headers = [('X-Requested-With', 'XMLHttpRequest')], base_url = webserviceUrl, useCache = True, jsonData = False):
    data = {}
    res = callServiceApi(path, params, headers, base_url, useCache, jsonData)
    try:
        data = json.loads(res) if res != '' else []
    except:
        pass
    return data
    
def getParams():
    param = {}
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
            params = sys.argv[2]
            cleanedparams = params.replace('?','')
            if (params[len(params)-1] == '/'):
                    params = params[0:len(params)-2]
            pairsofparams=cleanedparams.split('&')
            param = {}
            for i in range(len(pairsofparams)):
                    splitparams = {}
                    splitparams = pairsofparams[i].split('=')
                    if (len(splitparams)) == 2:
                            param[splitparams[0]] = splitparams[1]
    return param

def addDir(name, url, mode, thumbnail, page = 0, isFolder = True, **kwargs):
    u = generatePluginActionUrl(url, mode, name, thumbnail, page)
    liz = xbmcgui.ListItem(name, iconImage = "DefaultFolder.png", thumbnailImage = thumbnail)
    liz.setInfo( type = "Video", infoLabels = { "Title": name } )
    for k, v in kwargs.iteritems():
        if k == 'listProperties':
            for listPropertyKey, listPropertyValue in v.iteritems():
                liz.setProperty(listPropertyKey, listPropertyValue)
        if k == 'listInfos':
            for listInfoKey, listInfoValue in v.iteritems():
                liz.setInfo(listInfoKey, listInfoValue)
        if k == 'listArts':
            for listArtKey, listArtValue in v.iteritems():
                liz.setArt(v)
        if k == 'contextMenu':
            menuItems = []
            for label, action in v.iteritems():
                menuItems.append((label, action))
            if len(menuItems) > 0: liz.addContextMenuItems(menuItems)
    return xbmcplugin.addDirectoryItem(handle = thisPlugin, url = u,listitem = liz, isFolder = isFolder)

def generatePluginActionUrl(url, mode, name=None, thumbnail='', page = 0):
    url = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) 
    try:
        if name != None: url += "&name=" + urllib.quote_plus(name) 
    except:
        pass
    try:
        if int(page) >= 0: url += "&page=" + str(page) 
    except:
        pass
    try:
        if thumbnail != '': url += "&thumbnail=" + urllib.quote_plus(thumbnail)
    except:
        pass
        
    return url       
    
def showMessage(message, title = lang(50001)):
    if not message:
        return
    xbmc.executebuiltin("ActivateWindow(%d)" % 10147)
    win = xbmcgui.Window(10147)
    xbmc.sleep(100)
    win.getControl(1).setLabel(title)
    win.getControl(5).setText(message)
    
def confirm(message, line1='', line2='', title=lang(50001)):
    if not message:
        return
    return xbmcgui.Dialog().yesno(title, message, line1, line2)  
    
def numpad(message, default=''):
    if not message:
        return
    return xbmcgui.Dialog().numeric(0, message, default)
    
def alert(message, line1='', line2='', title=lang(50001)):
    if not message:
        return
    return xbmcgui.Dialog().ok(title, message, line1, line2)
    
def showNotification(message, title=lang(50001)):
    xbmc.executebuiltin('Notification(%s, %s)' % (title, message))
    
def log(mixed, level=0):
    if common.dbg and common.dbglevel > level:
        common.log(mixed)

def readFile(name):
    filePath = os.path.join(xbmc.translatePath(addonInfo('profile')), name)
    if os.path.exists(filePath):
        with open(filePath) as f:
            content = f.read()
            f.close()
            return content
    return False
    
def writeFile(name, string):
    filePath = os.path.join(xbmc.translatePath(addonInfo('profile')), name)
    with open(filePath, 'w') as f:
        f.write(string)
        f.close()
    if os.path.exists(filePath):
        return True
    return False
        
# This function is a workaround to fix an issue on cookies conflict between live stream and shows episodes
def cleanCookies(notify=True):
    message = ''
    if os.path.exists(os.path.join(xbmc.translatePath('special://home'), 'cache', 'cookies.dat'))==True:  
        log('cookies file FOUND (cache)')
        try: 
            os.unlink(os.path.join(xbmc.translatePath('special://home'), 'cache', 'cookies.dat'))
            message = lang(57004)
        except: 
            message = lang(57005)
                
    elif os.path.exists(os.path.join(xbmc.translatePath('special://home'), 'temp', 'cookies.dat'))==True:  
        log('cookies file FOUND (temp)')
        try: 
            os.unlink(os.path.join(xbmc.translatePath('special://home'), 'temp', 'cookies.dat'))
            message = lang(57004)
        except: 
            message = lang(57005)
    elif os.path.exists(os.path.join(xbmc.translatePath(addonInfo('profile')), cookieFileName))==True:  
        log('cookies file FOUND (profile)')
        try: 
            os.unlink(os.path.join(xbmc.translatePath(addonInfo('profile')), cookieFileName))
            message = lang(57004)
        except: 
            message = lang(57005)
    else:
        message = lang(57006)
        
    if notify == True:
        showNotification(message)
    
#---------------------- MAIN ----------------------------------------
thisPlugin = int(sys.argv[1])
# xbmcplugin.setPluginFanart(thisPlugin, 'fanart.jpg')

userAgents = { 
    webserviceUrl : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36',
    websiteUrl : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36',
    'default' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36'
    }
    
cookieJar = cookielib.CookieJar()
cookieFileName = 'tfctv.cookie'
cookieFile = ''
cookieJarType = ''

if os.path.exists(xbmc.translatePath(addonInfo('profile'))):
    cookieFile = os.path.join(xbmc.translatePath(addonInfo('profile')), cookieFileName)
    cookieJar = cookielib.LWPCookieJar(cookieFile)
    cookieJarType = 'LWPCookieJar'
    
if cookieJarType == 'LWPCookieJar':
    try:
        cookieJar.load()
    except:
        loginToWebsite()

params = getParams()
url = None
name = None
mode = None
page = 1
thumbnail = ''


try:
    url = urllib.unquote_plus(params["url"])
except:
    pass
try:
    name = urllib.unquote_plus(params["name"])
except:
    pass
try:
    mode = int(params["mode"])
except:
    pass
try:
    page = int(params["page"])
    page = 1 if page == 0 else page
except:
    pass
try:
    thumbnail = urllib.unquote_plus(params["thumbnail"])
except:
    pass
    
# check cache for better experience
# updateCatalogCache()
    
if (mode not in [10, 12]) and ((mode == None) or (url == None) or (len(url) < 1)):
    showMainMenu()
elif mode == 1:
    showSubCategories(url)
elif mode == 2:
    showSubCategoryShows(url)
elif mode == 3:
    showEpisodes(url, page)
elif mode == 4:
    playEpisode(url)
elif mode == 10:
    showCategories()
elif mode == 11:
    showWebsiteSectionContent(url, page)
elif mode == 12:
    showMyAccount()
elif mode == 13:
    showMyInfo()
elif mode == 14:
    showMySubscription()
elif mode == 15:
    showMyTransactions()
elif mode == 16:
    logout(quiet=False)
elif mode == 20:
    showMyList()
elif mode == 21:
    showMyListCategory(url)
elif mode == 22:
    addToMyList(url, name, 'show')
elif mode == 23:
    removeFromMyList(url, name, 'show')
elif mode == 24:
    addToMyList(url, name, 'episode')
elif mode == 25:
    removeFromMyList(url, name, 'episode')
elif mode == 50:
    showTools()
elif mode == 51:
    reloadCatalogCache()
elif mode == 52:
    cleanCookies()
elif mode == 99:
    cookieJar.clear()
    
if cookieJarType == 'LWPCookieJar':
    cookieJar.save()

if setting('lastVersion') != addonInfo('version'):
    showMessage(lang(57023) % addonInfo('version'), lang(50002))
    addon.setSetting('lastVersion', addonInfo('version'))
        
# fix itemsPerPage value
itemsPerPageMultiple = 8
if (int(setting('itemsPerPage')) % itemsPerPageMultiple) > 0:
    addon.setSetting('itemsPerPage', str(itemsPerPageMultiple))
