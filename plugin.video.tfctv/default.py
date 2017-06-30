import sys, urllib, urllib2, ssl, json, cookielib, time, os.path, hashlib
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
from operator import itemgetter
import CommonFunctions

try:
   import StorageServer
except:
   from ressources.lib.dummy import storageserverdummy as StorageServer
# Short cache   
shortCache = StorageServer.StorageServer("tfctv", 1/2) # 30 minutes cache
# Long cache
longCache = StorageServer.StorageServer("tfctv_db", 24 * 7) # 1 week cache

sessionCache = {}

common = CommonFunctions
addon = xbmcaddon.Addon()
setting = addon.getSetting
lang = addon.getLocalizedString
addonInfo = addon.getAddonInfo
common.plugin = addonInfo('name')

sCacheFunction = shortCache.cacheFunction
lCacheFunction = longCache.cacheFunction

#---------------------- CONFIG ----------------------------------------
# URLs
webserviceUrl = 'https://api.tfcone.com'
websiteUrl = 'http://tfc.tv'
websiteSecuredUrl = 'https://tfc.tv'

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
# common.dbg = True # Default
# common.dbglevel = 3 # Default

   
#---------------------- FUNCTIONS ----------------------------------------
def showMainMenu():
    checkAccountChange()
    # cleanCookies(False)
    
    # if setting('displayMostLovedShows') == 'true':
        # addDir('Most Loved Shows', '/', 5, 'icon.png')
    
    if setting('displayWebsiteSections') == 'true':
        addDir('By Category', '/', 10, 'icon.png')
    else:
        showCategories()
        
    if setting('displayWebsiteSections') == 'true':
        sections = getWebsiteHomeSections()
        for s in sections:
            addDir(s['name'].title(), str(s['id']), 11, 'icon.png')
        
    if setting('displayMyAccountMenu') == 'true':    
        addDir('My Account', '/', 12, 'icon.png')
    
    if setting('displayTools') == 'true':
        addDir('Tools', '/', 50, 'icon.png')
        
    xbmcplugin.endOfDirectory(thisPlugin)
    
def showCategories():   
    categories = lCacheFunction(getCategories)
    for c in categories:
        addDir(c['name'], str(c['id']), 1, 'icon.png')
        
    if setting('displayWebsiteSections') == 'true':
        xbmcplugin.endOfDirectory(thisPlugin)

def showTools():
    addDir('Reload Catalog Cache', '/', 51, 'icon.png')
    addDir('Clean cookies file', '/', 52, 'icon.png')
    xbmcplugin.endOfDirectory(thisPlugin)
      
def showSubCategories(categoryId):
    subCategories = lCacheFunction(getSubCategories, categoryId)
    for s in subCategories:
        addDir(s['name'], str(s['id']), 2, 'menu_logo.png')
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
    content = sCacheFunction(getWebsiteSectionContent, section, page, itemsPerPage)
    for e in content:
        if e['type'] == 'show':
            addDir(e['name'], str(e['id']), 3, e['image'], isFolder = True, **formatShowInfo(e))
        elif e['type'] == 'episode':
            addDir(e['title'], str(e['id']), 4, e['image'], isFolder = False, **formatVideoInfo(e))
    if len(content) == itemsPerPage:
        addDir("Next >>", section, 11, '', page + 1)
    xbmcplugin.endOfDirectory(thisPlugin)

def showMostLovedShows():
    shows = sCacheFunction(getMostLovedShowsData)
    if len(shows) == 0:
        xbmcplugin.endOfDirectory(thisPlugin)
        return False
    displayShows(shows)
    
def showLiveStreams(url):
    episodes = sCacheFunction(getLiveStreamData, url)
    for e in episodes:
        addDir(e['title'], str(e['id']), 4, e['image'], isFolder = False, **formatVideoInfo(e))
    xbmcplugin.endOfDirectory(thisPlugin)

def displayShows(shows):
    listSubscribedFirst = True if setting('listSubscribedFirst') == 'true' else False
    italiciseUnsubscribed = True if setting('italiciseUnsubscribed') == 'true' else False
    listSubscribedFirst = False
    italiciseUnsubscribed = False
    subscribedShowIds = []
    
    if listSubscribedFirst or italiciseUnsubscribed: 
        # make an API call only if we're checking against subscribed shows
        subscribedShowIds = getSubscribedShowIds()
        
    if listSubscribedFirst:
        unsubscribedShows = []
        sortedShowInfos = []
        sortedUnsubscibed = []
        
        for show in shows:
            if show['id'] in subscribedShowIds:
                sortedShowInfos.append((show['name'].lower(), show['name'], str(show['id']), 3, show['image'], formatShowInfo(show)))
            else:
                showTitle = '[I]' + show['name'] + '[/I]' if italiciseUnsubscribed else show['name']
                sortedUnsubscibed.append((show['name'].lower(), showTitle, str(show['id']), 3, show['image'], formatShowInfo(show)))
        
        sortedShowInfos = sorted(sortedShowInfos, key = itemgetter(0))
        sortedUnsubscibed = sorted(sortedUnsubscibed, key = itemgetter(0))
        
        for info in sortedShowInfos:
            addDir(info[1], info[2], info[3], info[4], isFolder = True, **info[5])
            
        for info in sortedUnsubscibed:
            addDir(info[1], info[2], info[3], info[4], isFolder = True, **info[5])
    else:
        sortedShowInfos = []
        for show in shows:
            showTitle = '[I]' + show['name'] + '[/I]' if italiciseUnsubscribed and show['id'] in subscribedShowIds else show['name']
            sortedShowInfos.append((show['name'].lower(), showTitle, str(show['id']), 3, show['image'], formatShowInfo(show)))
        
        sortedShowInfos = sorted(sortedShowInfos, key = itemgetter(0))
        for info in sortedShowInfos:
            addDir(info[1], info[2], info[3], info[4], isFolder = True, **info[5])
            
    xbmcplugin.endOfDirectory(thisPlugin)
    
def showEpisodes(showId, page=1):
    itemsPerPage = 8 #int(setting('itemsPerPage'))
    episodes = sCacheFunction(getEpisodesPerPage, showId, page, itemsPerPage)
    for e in episodes:
        addDir(e['title'], str(e['id']), 4, e['image'], isFolder = False, **formatVideoInfo(e))
    if len(episodes) == itemsPerPage:
        addDir("Next >>", showId, 3, '', page + 1)
    xbmcplugin.endOfDirectory(thisPlugin)
        
def playEpisode(url):
    cleanCookies(False)
    errorCode = -1
    episodeDetails = {}
    episode = url.split('/')[0]
    for i in range(int(setting('loginRetries')) + 1):
        episodeDetails = getMediaInfo(episode)
        if episodeDetails and 'errorCode' in episodeDetails and episodeDetails['errorCode'] == 0 and 'data' in episodeDetails:
            break
        else:
            login()
    if episodeDetails and 'errorCode' in episodeDetails and episodeDetails['errorCode'] == 0 and 'data' in episodeDetails:
        if 'preview' in episodeDetails['data'] and episodeDetails['data']['preview'] == True:
            showNotification(lang(50207), lang(50002))
        else:
            if 'StatusMessage' in episodeDetails and episodeDetails['StatusMessage'] != '':
                showNotification(episodeDetails['StatusMessage'], lang(57000))
        url = episodeDetails['data']['uri']
        # url = url.replace('=/', '=%2f')
        liz = xbmcgui.ListItem(name, iconImage = "DefaultVideo.png", thumbnailImage = thumbnail, path = url)
        liz.setInfo( type = "Video", infoLabels = { "Title": name } )
        liz.setProperty('IsPlayable', 'true')
        return xbmcplugin.setResolvedUrl(thisPlugin, True, liz)
    else:
        if (not episodeDetails) or (episodeDetails and 'errorCode' in episodeDetails and episodeDetails['errorCode'] != 0):
            if 'StatusMessage' in episodeDetails:
                showNotification(episodeDetails['StatusMessage'])
            else:
                showNotification(lang(57001), lang(57000))
    return False
    
def getMediaInfo(episodeId):
    # mediaInfo = getEpisodeVideo(episodeId)
    # If media info can't be retrieve from JSON webservices, then we try from website HTML page
    # if 'errorCode' in mediaInfo and mediaInfo['errorCode'] != 0:
    mediaInfo = getMediaInfoFromWebsite(episodeId)
    if mediaInfo and 'errorCode' in mediaInfo and mediaInfo['errorCode'] == 1:
        mediaInfo['errorCode'] = 0
    if 'data' in mediaInfo and 'Url' in mediaInfo['data']:
        mediaInfo['data']['uri'] = mediaInfo['data']['Url']
    return mediaInfo
    
def getMediaInfoFromWebsite(episodeId):
    import re
    mediaInfo = {}
    url = '/episode/details/%s'
    html = callServiceApi(url % episodeId, base_url = websiteUrl, useCache=False)
    body = common.parseDOM(html, "body")
    scripts = common.parseDOM(body, "script", attrs = { 'type' : 'text/javascript' })
    mediaToken = None
    for script in scripts:
        line = script.strip();
        tokenmatch = re.compile('/Scripts/amp-.+\.js\?token\=(.+)" type', re.IGNORECASE).search(line)
        if tokenmatch:
            mediaToken = tokenmatch.group(1).encode("ascii")
            break
    if mediaToken:
        cookie = []
        for c in cookieJar:
            cookie.append('%s=%s' % (c.name, c.value))
        cookie.append('cc_fingerprintid='+hashlib.md5(setting('emailAddress')).hexdigest())
        
        callHeaders = [
            ('Accept', 'application/json, text/javascript, */*; q=0.01'), 
            ('X-Requested-With', 'XMLHttpRequest'),
            ('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8'),
            ('Cookie', '; '.join(cookie)),
            ('mediaToken', mediaToken),
            ('Host', 'tfc.tv'),
            ('Origin', websiteUrl),
            ('Referer', websiteUrl+'/')
            ]
        episodeDetails = callJsonApi('/media/get', params = {'id': episodeId, 'pv': 'false'}, headers = callHeaders, base_url = websiteUrl, useCache=False)
        if episodeDetails and 'StatusCode' in episodeDetails:
            mediaInfo['errorCode'] = episodeDetails['StatusCode']
            if 'MediaReturnObj' in episodeDetails and 'uri' in episodeDetails['MediaReturnObj']:
                episodeDetails['MediaReturnObj']['uri'] = episodeDetails['MediaReturnObj']['uri'].replace('&b=100-1000', '')
                # episodeDetails['MediaReturnObj']['uri'] += '&b=2000-4000'
                mediaInfo['data'] = episodeDetails['MediaReturnObj']
            if 'StatusMessage' in episodeDetails and episodeDetails['StatusMessage'] != '' and episodeDetails['StatusMessage'] != 'OK':
                mediaInfo['StatusMessage'] = episodeDetails['StatusMessage']
    return mediaInfo
    
def showCelebrities():
    celebrities = getCelebrities()
    for c in celebrities:
        image = c['ImageUrl'].encode('utf8').replace(' ', '%20')
        lastName = c['LastName'].encode('utf8') if c['LastName'] else ''
        firstName = c['FirstName'].encode('utf8') if c['FirstName'] else ''
        addDir('%s %s' % (lastName, firstName), '/Synapse/GetCelebrityDetails/%s' % c['CelebrityId'], 7, image, isFolder = False)
    xbmcplugin.endOfDirectory(thisPlugin)
    
def showCelebrityInfo(url):
    d = callJsonApi(url)
    name = d['name'].encode('utf8') if d['name'] else ''
    if d['birthday'] or d['birthplace'] or d['description']:
        birthday = d['birthday'].encode('utf8') if d['birthday'] else '-'
        birthplace = d['birthplace'].encode('utf8') if d['birthplace'] else '-'
        description = d['description'].encode('utf8') if d['description'] else ''
        message = 'Birthday: %s\nBirth place: %s\n\n%s\n\n' % (birthday, birthplace, description)
    else:
        message = lang(57002)
    showMessage(message, name)
    
def showMyAccount():
    checkAccountChange(False)
    categories = [
        { 'name' : 'My info', 'url' : '/', 'mode' : 13 },
        { 'name' : 'Entitlements', 'url' : '/', 'mode' : 14 },
        { 'name' : 'Transactions', 'url' : '/', 'mode' : 15 }
    ]
    for c in categories:
        addDir(c['name'], c['url'], c['mode'], 'icon.png')
    addDir('Logout', '/', 16, 'icon.png', isFolder = False)    
    xbmcplugin.endOfDirectory(thisPlugin)
    
def showMyInfo():
    UID = getUserUID()
    message = ''
    if UID:
        user = getUserInfo(UID)
        message = 'Email: %s\nFirst name: %s\nLast name: %s\nCountry: %s\nState: %s\nCity: %s\n\n' % (user['Email'].encode('utf8'), user['FirstName'].encode('utf8'), user['LastName'].encode('utf8'), user['CountryCode'].encode('utf8'), user['State'].encode('utf8'), user['City'].encode('utf8'))
    else:
        message = lang(57002)
    showMessage(message, lang(56001))
    
def showMyEntitlements():
    data = getUserEntitlements()
    message = ''
    if data['total'] > 0:
        for entitlement in data['data']:
            entitlementEntry = 'Package Name: %s\n    EID: %s\n    Expiry Date: %s\n\n' % (entitlement['Content'], entitlement['EntitlementId'], entitlement['ExpiryDate'])
            message += entitlementEntry
    else:
        message = lang(57002)
    showMessage(message, lang(56002))
    
def showMyTransactions():
    transactions = getUserTransactions()
    message = ''
    if len(transactions) > 0:
        for t in transactions:
            expiryUnixTime = (int(t['TransactionDate'].replace('/Date(','').replace(')/', ''))) / 1000
            message += 'TID: %s\nProduct: %s\nDate: %s\nAmount: %.2f\nCurrency: %s\nType: %s\nMode: %s\nReference: %s\n\n' % (t['TransactionId'], t['ProductName'].encode('utf8'), time.strftime('%B %d, %Y %X %Z', time.localtime(expiryUnixTime)), t['Amount'], t['Currency'].encode('utf8'), t['TransactionType'].encode('utf8'), t['Method'].encode('utf8'), t['Reference'].encode('utf8'))
    else:
        message = lang(57002)
    showMessage(message, lang(56003))
    
def getSubscribedShowIds():
    return getSubscribedShows()[0]
    
def getSubscribedShows():
    jsonData = ''
    entitlementsData = getEntitlementsData()
    subscribedShows = []
    showIds = []
    for e in entitlementsData['data']:
        expiry = int(e['ExpiryDate'].replace('/Date(','').replace(')/', ''))
        if expiry >= (time.time() * 1000):
            if e['PackageId']:
                url = "/Packages/GetShows?packageId=%s" % (e['PackageId'])
                packagesData = []
                for i in range(int(setting('loginRetries')) + 1):
                    jsonData = callServiceApi(url)
                    packagesData = json.loads(jsonData)
                    if packagesData:
                        break
                    else:
                        loginToWebsite()
                for p in packagesData:
                    if p['ShowId'] in showIds:
                        pass
                    else:
                        subscribedShows.append(p)
                        showIds.append(p['ShowId'])
            else:
                if e['CategoryId'] and e['CategoryId'] not in showIds:
                    e['MainCategory'] = u'A la carte'
                    e['ShowId'] = e['CategoryId']
                    e['Show'] = e['Content']
                    subscribedShows.append(e)
                    showIds.append(e['CategoryId'])
    return showIds, subscribedShows
    
def normalizeCategoryName(categoryName):
    return categoryName.replace('LITE', '').replace('PREMIUM', '').strip()
    
def showSubscribedCategories(url):
    subscribedShows = getSubscribedShows()[1]
    categories = []
    for s in subscribedShows:
        categoryName = normalizeCategoryName(s['MainCategory'])
        if categoryName in categories:
            pass
        else:
            categories.append(categoryName)
            addDir(categoryName, categoryName, 11, 'menu_logo.png')
    xbmcplugin.endOfDirectory(thisPlugin)
    
def showSubscribedShows(url):
    subscribedShows = getSubscribedShows()[1]
    shows = [s for s in subscribedShows if s['MainCategory'].startswith(url)]
    thumbnails = {}
    showThumbnails = True if setting('showSubscribedShowsThumbnails') == 'true' else False
    showThumbnails = False # currently broken, disabled for now
    showListData = {}
    for s in shows:
        thumbnail = ''
        showId = s['ShowId']
        if showThumbnails and 'MainCategoryId' in s:
            categoryId = s['MainCategoryId']
            # get the showListData only once. don't get it if it's already set
            try:
                showListData = showListData if showListData else getShowListData(categoryId)
            except:
                pass
            if showId in showListData:
                thumbnail = showListData[showId][1]
            else:
                # the show must be new and the thumbnail is probably not in cache ...
                # ... or the first set of thumbnails might be from a LITE subscription (less shows vs PREMIUM)
                try:
                    showListData = getShowListData(categoryId)
                except:
                    pass
                if showId in showListData:
                    thumbnail = showListData[showId][1]
        showTitle = common.replaceHTMLCodes(s['Show'].encode('utf8'))
        addDir(showTitle, str(showId), 3, thumbnail)
    xbmcplugin.endOfDirectory(thisPlugin)
    
def reloadCatalogCache():
    res = updateCatalogCache()
    if res is True:
        showNotification(lang(57003), lang(50001))
    
def updateCatalogCache():
    # update sections cache
    if setting('displayWebsiteSections') == 'true':
        sections = sCacheFunction(getWebsiteHomeSections)
        for section in sections:
            sCacheFunction(getWebsiteSectionContent, section['id'])
        
    # update Live streams cache
    if setting('displayLiveCategory') == 'true':
        sCacheFunction(getLiveStreamData, '/category/list/3954')
    
    # update categories cache
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
    
def getLiveStreamData(url):
    import re
    data = []
    html = callServiceApi(url, base_url = websiteUrl)
    div = common.parseDOM(html, "div", attrs = { 'class' : 'main' })
    shows = common.parseDOM(div, "li", attrs = { 'class' : 'og-grid-item-o' })
    
    for show in shows:
        image = common.parseDOM(show, "img", ret = "src")[0]
        name = common.parseDOM(common.parseDOM(show, "div", attrs = { 'class' : 'show-cover-thumb-title' }), "a")[0]
        url = common.parseDOM(common.parseDOM(show, "div", attrs = { 'class' : 'show-cover-thumb-aired-watch' }), "a", ret = 'href')[0]
        episodeId = re.compile('/([0-9]+)/', re.IGNORECASE).search(url).group(1)
        data.append({
            'id' : int(episodeId), 
            'title' : common.replaceHTMLCodes(name).encode('utf8'), 
            'show' : common.replaceHTMLCodes(name).encode('utf8'), 
            'image' : image, 
            'url' : url, 
            'episodenumber' : 0,
            'description' : '',
            'shortdescription' : '',
            'dateaired' : '',
            'year' : '',
            'fanart' : image
            })
            
    showsImages = common.parseDOM(div, "show-cover", attrs = { 'class' : 'hidden-sm hidden-xs hidden-md' }, ret = 'data-src')
    i = 0
    for image in showsImages:
        data[i]['image'] = image
        i += 1       
    return data
    
def getSiteMenu():
    import re
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

def getWebsiteHomeSections():
    data = []
    html = callServiceApi('', base_url = websiteUrl)
    sections = common.parseDOM(html, "div", attrs = { 'class' : 'main-container-xl main-container-xl-mobile' })
    i = 1
    for section in sections:
        header = common.parseDOM(section, "a", attrs = { 'class' : 'h2 heading-slider first' })
        if len(header) > 0:
            data.append({'id' : str(i), 'name' : common.replaceHTMLCodes(header[0])}) #, 'url' : '/', 'fanart' : ''})
        else:
            continue
        i += 1
    return data
    
def getWebsiteSectionContent(sectionId, page=1, itemsPerPage=10):
    
    page -= 1
    data = []
    
    html = callServiceApi('', base_url = websiteUrl)
    sections = common.parseDOM(html, "div", attrs = { 'class' : 'main-container-xl main-container-xl-mobile' })
    section = sections[int(sectionId) - 1]
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
    import re
    
    showId = re.compile('/([0-9]+)/', re.IGNORECASE).search(url).group(1)
    filter = 'port-cover-thumb-title' if 'port-cover-thumb-title' in html else 'show-cover-thumb-title-mobile'
    showName = common.replaceHTMLCodes(common.parseDOM(html, "h3", attrs = { 'class' : filter })[0])
    image = common.parseDOM(html, "div", attrs = { 'class' : 'show-cover' }, ret = 'data-src')[0]
    
    return {
        'type' : 'show',
        'id' : int(showId),
        'parentid' : -1,
        'parentname' : '',
        'name' : showName.encode('utf8'),
        'image' : image,
        'description' : '',
        'shortdescription' : '',
        'year' : '',
        'fanart' : image
        }

def extractWebsiteSectionEpisodeData(url, html):
    import re
    
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
        year = dateAired[0].split(', ')[1]
    
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
        'dateaired' : dateAired,
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
    
    # url = '/Genre?genreId=%s'
    # subCategoryShows = callJsonApi(url % subCategoryId)
    
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
    import re
    
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
    import re

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
                'title' : t,
                'episodenumber' : int(re.compile('Ep. ([0-9]+) -', re.IGNORECASE).search(t).group(1)),
                'url' : values[i]
                }})
            i+=1
    
    data = {
        'id' : int(showId),
        'parentid' : -1,
        'parentname' : genre.encode('utf8'),
        'name' : name.encode('utf8'),
        'image' : image,
        'description' : description.encode('utf8'),
        'shortdescription' : description.encode('utf8'),
        'year' : '',
        'fanart' : banner,
        'episodes' : episodes
        }
        
    return data
    
def formatShowInfo(info):
    data = { 
        'listArts' : { 'fanart' : info['fanart'], 'banner' : info['fanart'] }, 
        'listInfos' : { 
            'video' : { 'plot' : info['description'], 'year' : info['year'] } 
            } 
        }
    return data
        
def formatVideoInfo(info):
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
            } 
        }
    return data

def getEpisodesPerPage(showId, page=1, itemsPerPage=8):
    import re
    
    data = []
    url = '/modulebuilder/getepisodes/%s/show/%s'
    html = callServiceApi(url % (showId, page))
    showDetails = sCacheFunction(getShow, showId)
    
    # if no pagination, it's a movie
    if html == '':
        url = '/show/details/%s'
        html = callServiceApi(url % showId)
        episodeUrl = common.parseDOM(html, "a", attrs = { 'class' : 'hero-image-orange-btn' }, ret = 'href')
        # If not found, probably a live channel
        if len(episodeUrl) == 0:
            episodeUrl = common.parseDOM(html, "link", attrs = { 'rel' : 'canonical' }, ret = 'href')
        episodeId = int(re.compile('/([0-9]+)/', re.IGNORECASE).search(episodeUrl[0]).group(1))
        
        data.append({
            'id' : episodeId,
            'title' : showDetails['name'],
            'show' : showDetails['name'],
            'image' : showDetails['image'],
            'episodenumber' : 0,
            'description' : showDetails['description'],
            'shortdescription' : showDetails['description'],
            'dateaired' : '',
            'year' : showDetails['year'],
            'fanart' : showDetails['fanart']
            })
    else:
        i = 0
        episodes = common.parseDOM(html, 'li', attrs = {'class' : 'og-grid-item'})
        descriptions = common.parseDOM(html, 'li', attrs = {'class' : 'og-grid-item'}, ret = 'data-show-description')
        titles = common.parseDOM(html, 'li', attrs = {'class' : 'og-grid-item'}, ret = 'data-aired')
        
        for e in episodes:
            url = common.parseDOM(e, "a", ret = 'href')[0]
            episodeId = int(re.compile('/([0-9]+)/', re.IGNORECASE).search(url).group(1))
            image = common.parseDOM(e, "div", attrs = {'class' : 'show-cover'}, ret = 'data-src')[0]
            title = titles[i]
            dateAired = title
            showTitle = showDetails['name']
            fanart = showDetails['fanart']
            year = title.split(', ').pop()
            description = descriptions[i]
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
    showData = getShow(showId)
    url = '/Episodes?showId=%s'
    showEpisodes = callJsonApi(url % showId)
    if showData and showEpisodes:
        for e in showEpisodes:
            e['show'] = showData['name']
            e['showimage'] = showData['image'].replace(' ', '%20')
            e['fanart'] = showData['banner'].replace(' ', '%20')
            e['image'] = e['ImageList']
            e['description'] = e['Synopsis']
            e['shortdescription'] = e['Description']
            e['episodenumber'] = e['EpisodeNumber']
            e['dateaired'] = e['DateAired'].split('T')[0]
            data[e['EpisodeId']] = e
    return data
      
def getEpisodeDataByShow(showId, episodeId):
    import re
    data = {}
    episodes = sCacheFunction(getShowEpisodes, showId)
    if episodes and episodeId in episodes:
        data = episodes[episodeId]
    else:
        episode = lCacheFunction(getEpisodeData, episodeId)
        if episode:
            episode['title'] = episode['dateaired']
            episode['description'] = episode['synopsis']
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
    
def getUserInfo(UID):
    data = {}
    url = '/Synapse/GetUserData?uid=%s'
    res = callJsonApi(url % UID, useCache = False)
    if res and 'data' in res:
        data = res['data']
    return data
    
def getUserEntitlements():
    data = {'data' : [], 'total': 0}

    url = '/User/Entitlements'
    htmlData = callServiceApi(url, useCache=False)
    
    sectionTable = common.parseDOM(htmlData, "table", attrs = {'class' : 'table table-striped subscription_table'})
    sectionTableBody = common.parseDOM(sectionTable, "tbody")
    entitlements = common.parseDOM(sectionTableBody, "tr")
    
    for tr in entitlements:
        column = common.parseDOM(tr, "td")
        entitlement = {}
        entitlement['EntitlementId'] = column[0]
        entitlement['Content'] = column[1]
        entitlement['ExpiryDate'] = column[2]
        data['data'].append(entitlement)
        data['total'] += 1
    
    return data
    
def getUserTransactions():
    data = {}
    url = '/Synapse/MyTransactions'
    res = callJsonApi(url, useCache = False)
    if res:
        data = res        
    return data
    
def getUserSession():
    userSession = None
    email = setting('emailAddress')
    password = setting('password')
    hash = hashlib.sha1(email + password).hexdigest()
    for i in range(int(setting('loginRetries')) + 1):
        res = shortCache.get('userSession_' + hash)
        if res:
            userSession = json.loads(res)
            if userSession:
                return userSession
        loginToWebservice()
    return userSession
    
def getUserUID():
    uid = None
    userSession = getUserSession()
    if userSession and 'data' in userSession:
        uid = userSession['data']['uid']
    return uid
    
def getUserCookie():
    cookie = None
    userSession = getUserSession()
    if userSession and 'info' in userSession:
        userSession['info']
    return cookie
    
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
                
    if savedHash != hash:
        accountChanged = True
        logout()
        logged = True
        # (signedIntoWebsite, signedIntoWebservice) = login()
        # if signedIntoWebsite == True and signedIntoWebservice == True:
            # loginSuccess
    elif not isLoggedIn():
        log('Not logged in')
        logged = True
    
    if logged:
        loginSuccess = login()
        if loginSuccess == True and os.path.exists(xbmc.translatePath(addonInfo('profile'))):
            with open(hashFile, 'w') as f:
                f.write(hash)
        elif os.path.exists(hashFile)==True: 
            os.unlink(hashFile)
        
    return (accountChanged, loginSuccess)
    
def login(quiet=False):
    # signedIntoWebservice = loginToWebservice(quiet)
    # signedIntoWebservice = True
    signedIntoWebsite = loginToWebsite(quiet)
    # return (signedIntoWebsite, signedIntoWebservice)
    return signedIntoWebsite
    
def isLoggedIn():
    html = callServiceApi('', base_url = websiteSecuredUrl, useCache = False)
    return False if 'CTA_Login' in html else True
    
def loginToWebservice(quiet=False):
    email = setting('emailAddress')
    password = setting('password')
    param = {'email' : email, 'pw' : password}
    userSession = callJsonApi("/.auth/login", params = param, headers = [('Referer', webserviceUrl+'/user/login')], base_url = webserviceUrl, useCache = False)
    if userSession:
        if 'errorCode' in userSession and userSession['errorCode'] == 0:
            hash = hashlib.sha1(email + password).hexdigest()
            shortCache.set('userSession_' + hash, json.dumps(userSession))
            return True
        elif 'errorMessage' in userSession and quiet == False:
            showNotification(userSession['errorMessage'].encode('utf8'), lang(50204))
    return False
    
def loginToWebsite(quiet=False):
    login_page = callServiceApi("/user/login", useCache=False)
    form_login = common.parseDOM(login_page, "form", attrs = {'id' : 'form1'})
    if len(form_login) > 0:
        request_verification_token = common.parseDOM(form_login[0], "input", attrs = {'name' : '__RequestVerificationToken'}, ret = 'value')
        emailAddress = addon.getSetting('emailAddress')
        password = addon.getSetting('password')
        formdata = { "EMail" : emailAddress, "Password": password, '__RequestVerificationToken' : request_verification_token[0] }
        html = callServiceApi("/user/login", formdata, headers = [('Referer', websiteSecuredUrl+'/user/login')], base_url = websiteSecuredUrl, useCache = False)
        if 'CTA_Login' in html and quiet == False:
            showNotification(lang(50205), lang(50204))
            return False
    return True

def logout():
    # callServiceApi("/logout", headers = [('Referer', webserviceUrl+'/')], base_url = webserviceUrl, useCache = False)
    callServiceApi("/logout", headers = [('Referer', websiteUrl+'/')], base_url = websiteUrl, useCache = False)
    cookieJar.clear()

def callServiceApi(path, params = {}, headers = [], base_url = websiteUrl, useCache = True):
    import hashlib
    global cacheActive, cookieJar
    
    res = ''
    cached = False
    toCache = False
    
    key = hashlib.md5(base_url + path + urllib.urlencode(params)).hexdigest()
    log('Key %s : %s - %s' % (key, base_url + path, params))
    
    if cacheActive == 'true' and useCache == True:
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
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))
        userAgent = userAgents[base_url] if base_url in userAgents else userAgents['default']
        headers.append(('User-Agent', userAgent))
        opener.addheaders = headers
        log('%s - %s' % (base_url + path, params))
        requestTimeOut = int(setting('requestTimeOut')) if setting('requestTimeOut') != '' else 20
        response = None
        
        try:
            if params:
                data_encoded = urllib.urlencode(params)
                response = opener.open(base_url + path, data_encoded, timeout = requestTimeOut)
            else:
                response = opener.open(base_url + path, timeout = requestTimeOut)
        except (urllib2.URLError, ssl.SSLError) as e:
            message = "Connection timeout : " + base_url + path
            log(message)
            showNotification(message)
            
        res = response.read() if response else ''
        log(res)
        
        if toCache == True and res:
            if cacheActive == 'true':
                shortCache.set(key, res)
                log('Stored in cache (%s) : %s' % (key, res))
            else:
                sessionCache[key] = res
                log('Stored in session cache (%s) : %s' % (key, res))
    
    return res

def callJsonApi(path, params = {}, headers = [('X-Requested-With', 'XMLHttpRequest')], base_url = webserviceUrl, useCache = True):
    res = callServiceApi(path, params = params, headers = headers, base_url = base_url, useCache = useCache)
    data = json.loads(res) if res != '' else []
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
    u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name) + "&page=" + str(page) + "&thumbnail=" + urllib.quote_plus(thumbnail)
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
    return xbmcplugin.addDirectoryItem(handle = thisPlugin, url = u,listitem = liz, isFolder = isFolder)

def showMessage(message, title = lang(50001)):
    if not message:
        return
    xbmc.executebuiltin("ActivateWindow(%d)" % 10147)
    win = xbmcgui.Window(10147)
    xbmc.sleep(100)
    win.getControl(1).setLabel(title)
    win.getControl(5).setText(message)
    
def showNotification(message, title = lang(50001)):
    xbmc.executebuiltin('Notification(%s, %s)' % (title, message))
    
def log(mixed, level=0):
    if common.dbg and common.dbglevel > level:
        common.log(mixed)

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
xbmcplugin.setPluginFanart(thisPlugin, 'fanart.jpg')

userAgents = { 
    webserviceUrl : 'Mozilla/5.0 (iPad; CPU OS 5_0 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9A334 Safari/7534.48.3',
    websiteUrl : 'Mozilla/5.0 (iPad; CPU OS 5_0 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9A334 Safari/7534.48.3',
    'default' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586'
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
    showMyEntitlements()
elif mode == 15:
    showMyTransactions()
elif mode == 16:
    logout()
elif mode == 50:
    showTools()
elif mode == 51:
    reloadCatalogCache()
elif mode == 52:
    cleanCookies()
elif mode == 99:
    cookieJar.clear()
    # callServiceApi(url)
# elif mode == xx:
    # showSubscribedCategories(url)
# elif mode == xx:
    # showSubscribedShows(url)
    
if cookieJarType == 'LWPCookieJar':
    cookieJar.save()

if setting('announcement') != addonInfo('version'):
    messages = {
        '0.0.56': 'Your TFC.tv plugin has been updated.\n\nTFC.tv has undergone a lot of changes and the plugin needs to be updated to adjust to those changes.\n\nIf you encounter anything that you think is a bug, please report it to the TFC.tv Kodi Forum thread (https://forum.kodi.tv/showthread.php?tid=155870) or to the plugin website (https://github.com/cmik/cmik.xbmc/issues).',
        '0.0.59': 'Your TFC.tv plugin has been updated.\n\nNow using TFC website (no more API because of timeouts).\n\nIf you encounter anything that you think is a bug, please report it to the TFC.tv Kodi Forum thread (https://forum.kodi.tv/showthread.php?tid=155870) or to the plugin website (https://github.com/cmik/cmik.xbmc/issues).'
        }
    if addonInfo('version') in messages:
        showMessage(messages[addonInfo('version')], lang(50106))
        xbmcaddon.Addon().setSetting('announcement', addonInfo('version'))

