import sys, urllib, urllib2, json, cookielib, time, os.path, hashlib
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
from operator import itemgetter

import CommonFunctions

try:
   import StorageServer
except:
   from ressources.lib.dummy import storageserverdummy as StorageServer
# Short cache   
shortCache = StorageServer.StorageServer("tfctv", 1) # 1 hour cache
# Long cache
longCache = StorageServer.StorageServer("tfctv_db", 24 * 7) # 1 week cache



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
baseUrl = 'http://tfc.tv'
websiteUrl = 'http://beta.tfc.tv'

# Cache
cacheActive = setting('cacheActive')
if cacheActive == 'false': 
    sCacheFunction = lambda x, *y: x(*y)
    lCacheFunction = lambda x, *y: x(*y)

# Debug 
# common.dbg = True # Default
# common.dbglevel = 3 # Default

   
#---------------------- FUNCTIONS ----------------------------------------
def showMainMenu():
    checkAccountChange()
    
    if setting('displayWebsiteSections') == 'true':
        sections = sCacheFunction(getWebsiteHomeSections)
        for s in sections:
            addDir(s['name'].title(), str(s['id']), 11, 'icon.png')
            
    if setting('displayMostLovedShows') == 'true':
        addDir('Most Loved Shows', '/', 5, 'icon.png')
    
    if setting('displayWebsiteSections') == 'true':
        addDir('By Category', '/', 10, 'icon.png')
    else:
        showCategories()
    addDir('Celebrities', '/', 6, 'icon.png')
    addDir('My Account', '/', 12, 'icon.png')
    addDir('Reload Catalog Cache', '/', 20, 'icon.png')
    # addDir('Test', '/Synapse/getallvideosbasedonentitlements', 99, 'icon.png')
    xbmcplugin.endOfDirectory(thisPlugin)
    
def showCategories():
    categories = lCacheFunction(getCategories)
    for c in categories:
        addDir(c['name'], str(c['id']), 1, 'icon.png')
    
    if setting('displayLiveCategory') == 'true':
        addDir('Live', '/category/list/3954', 8, 'icon.png')
        
    if setting('displayWebsiteSections') == 'true':
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
    
def showWebsiteSectionShowEpisodes(section):
    episodes = sCacheFunction(getWebsiteSectionShowEpisodes, section)
    for e in episodes:
        addDir(e['title'], str(e['id']), 4, e['image'], isFolder = False, **formatVideoInfo(e))
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
    
def showEpisodes(showId, page):
    itemsPerPage = int(setting('itemsPerPage'))
    episodes = sCacheFunction(getEpisodesPerPage, showId, page, itemsPerPage)
    for e in episodes:
        addDir(e['title'], str(e['id']), 4, e['image'], isFolder = False, **formatVideoInfo(e))
    addDir("Next >>", showId, 3, '', page + 1)
    xbmcplugin.endOfDirectory(thisPlugin)
        
def playEpisode(url):
    errorCode = -1
    episodeDetails = {}
    episode = url.split('/')[0]
    for i in range(int(setting('loginRetries')) + 1):
        episodeDetails = getMediaInfo(episode)
        if episodeDetails and 'errorCode' in episodeDetails and episodeDetails['errorCode'] == 0:
            break
        else:
            login()
    if episodeDetails and 'errorCode' in episodeDetails and episodeDetails['errorCode'] == 0:
        url = episodeDetails['data']['Url']
        liz = xbmcgui.ListItem(name, iconImage = "DefaultVideo.png", thumbnailImage = thumbnail, path = url)
        liz.setInfo( type = "Video", infoLabels = { "Title": name } )
        liz.setProperty('IsPlayable', 'true')
        return xbmcplugin.setResolvedUrl(thisPlugin, True, liz)
    else:
        if (not episodeDetails) or (episodeDetails and 'errorCode' in episodeDetails and episodeDetails['errorCode'] != 0):
            xbmc.executebuiltin('Notification(%s, %s)' % (lang(57000), lang(57001)))
    return False
    
def getMediaInfo(episodeId):
    mediaInfo = getEpisodeVideo(episodeId)
    # If media info can't be retrieve from JSON webservices, then we try from website HTML page
    if mediaInfo and 'errorCode' in mediaInfo and mediaInfo['errorCode'] == -703:
        mediaInfo = getMediaInfoFromWebsite(episodeId)
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
        match = re.compile('/media/get.+', re.IGNORECASE).search(line)
        if match:
            match = re.compile('mediaToken\': \'(.+)\'', re.IGNORECASE).search(line)
            mediaToken = match.group(1).encode("ascii")
            break
    if mediaToken:
        episodeDetails = callJsonApi('/media/get', params = {'id': episodeId, 'pv': 'false'}, headers = [('X-Requested-With', 'XMLHttpRequest'), ('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8'), ('mediaToken', mediaToken), ('Host', 'tfc.tv'), ('Origin', 'http://tfc.tv'), ('Referer', 'http://tfc.tv/')])
        if episodeDetails and 'StatusCode' in episodeDetails:
            mediaInfo['errorCode'] = episodeDetails['StatusCode']
            if episodeDetails and 'StatusCode' in episodeDetails and episodeDetails['StatusCode'] == 0:
                mediaInfo['data'] = { 'Url' : episodeDetails['uri'] }
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
    categories = [
        { 'name' : 'My info', 'url' : '/', 'mode' : 13 },
        { 'name' : 'Entitlements', 'url' : '/', 'mode' : 14 },
        { 'name' : 'Transactions', 'url' : '/', 'mode' : 15 }
    ]
    for c in categories:
        addDir(c['name'], c['url'], c['mode'], 'icon.png')
    addDir('Logout', '/Logout', 99, 'icon.png', isFolder = False)    
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
                        login()
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
        showMessage(lang(57003), lang(50001))
    
def updateCatalogCache():
    # update sections cache
    if setting('displayWebsiteSections') == 'true':
        sections = sCacheFunction(getWebsiteHomeSections)
        for section in sections:
            sCacheFunction(getWebsiteSectionShowEpisodes, section['id'])
        
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
    data = {}
    url = '/Synapse/getsitemenu'
    data = callJsonApi(url)
    return data
    
def getCategories():
    data = getSiteMenu()
    return data
    
def getSubCategories(categoryId):
    data = []
    categoryData = getSiteMenu()
    subcat = {}
    for c in categoryData:
        if str(c['id']) == categoryId:
           subcat = c['menu']
           break
    for s in subcat:
        data.append({'id' : s['id'], 'name' : s['name'].encode('utf8')})
    return data
    
def getWebsiteHomeSections():
    data = []
    html = callServiceApi('', base_url = websiteUrl)
    sections = common.parseDOM(html, "div", attrs = { 'class' : 'main-container-xl' })
    i = 1
    for section in sections:
        shows = common.parseDOM(section, "div", attrs = { 'class' : 'horizontal' })
        if len(shows) > 0:
            header = common.parseDOM(section, "div")[0]
            data.append({'id' : str(i), 'name' : common.replaceHTMLCodes(header)}) #, 'url' : '/', 'fanart' : ''})
        i += 1
    return data
    
def getWebsiteSectionShowEpisodes(sectionId):
    import re
    data = []
    
    html = callServiceApi('', base_url = websiteUrl)
    sections = common.parseDOM(html, "div", attrs = { 'class' : 'main-container-xl' })
    section = sections[int(sectionId) - 1]
    shows = common.parseDOM(section, "div", attrs = { 'class' : 'horizontal' })
    
    for s in shows:
    
        showUrl = common.parseDOM(common.parseDOM(s, "div", attrs = { 'class' : 'show-cover-thumb-title' })[0], "a", ret = 'href')[0]
        showId = re.compile('/([0-9]+)/', re.IGNORECASE).search(showUrl).group(1)
        show = sCacheFunction(getShow, showId)
        if show:
            showName = show['name']
            fanart = show['banner']
        else:
            showName = common.replaceHTMLCodes(common.parseDOM(s, "div", attrs = { 'class' : 'show-cover-thumb-title-mobile' })[0])
            fanart = common.parseDOM(s, "show-cover", ret = 'data-src')[0]
        url = common.parseDOM(s, "a", attrs = { 'class' : 'show-cover-thumb-aired-watch' }, ret = 'href')[0]
        episodeId = re.compile('/([0-9]+)/', re.IGNORECASE).search(url).group(1)
        episode = sCacheFunction(getEpisodeDataByShow, showId, episodeId)
        dateAired = ''
        year = ''
        episodeNumber = 0
        description = ''
        if episode:
            episodeName = episode['title']
            dateAired = episode['dateaired']
            image = episode['image']
            description = episode['description']
            year = episode['year']
            episodeNumber = episode['episodenumber']
        else:
            episodeName = common.parseDOM(s, "div", attrs = { 'class' : 'show-cover-thumb-aired-mobile' })[0]
            images = common.parseDOM(s, "img", attrs = { 'class' : 'lazy' }, ret = 'data-src')
            image = fanart if len(images) == 0 else images[0]
        
        data.append({
            'id' : int(episodeId), 
            'parentid' : -1,
            'parentname' : '',
            'title' : common.replaceHTMLCodes('%s - %s' % (showName, episodeName)).encode('utf8'), 
            'show' : showName.encode('utf8'), 
            'image' : image, 
            'episodenumber' : episodeNumber,
            'url' : url, 
            'description' : description,
            'shortdescription' : '',
            'dateaired' : dateAired,
            'year' : year,
            'fanart' : fanart
            })
            
    return data
    
def getShows(subCategoryId):
    data = []
    url = '/Synapse/GetShows/%s'
    subCategoryShows = callJsonApi(url % subCategoryId)
    
    if subCategoryShows and 'shows' in subCategoryShows:
        for d in subCategoryShows['shows']:
            image = d['image'].replace(' ', '%20')
            description = d['blurb'] if 'blurb' in d else ''
            dateAired = d['dateairedstr'] if 'dateairedstr' in d else ''
            banner = d['banner'].replace(' ', '%20') if 'banner' in d else ''
            
            data.append({
                'id' : int(d['id']),
                'parentid' : int(subCategoryId),
                'parentname' : subCategoryShows['name'].encode('utf8'),
                'name' : d['name'].encode('utf8'),
                'image' : image,
                'description' : description.encode('utf8'),
                'shortdescription' : description.encode('utf8'),
                'year' : dateAired,
                'fanart' : banner
                })
                
    return data

def getShow(showId):
    data = {}
    url = '/Synapse/getshowdetails/%s'
    res = callJsonApi(url % showId)
    if res:
        res['name'] = res['name'].encode('utf8')
        res['description'] = res['blurb'].encode('utf8')
        res['image'] = res['image'].replace(' ', '%20')
        res['banner'] = res['banner'].replace(' ', '%20')
        data = res
    return data
    
def getMostLovedShowsData():
    data = []
    url = '/Synapse/GetMostLovedShows'
    mostLovedShows = callJsonApi(url)
    
    if mostLovedShows and len(mostLovedShows) > 0:
        for d in mostLovedShows:
            show = lCacheFunction(getShow, d['categoryId'])
            if show:
                showId = d['categoryId']
                showName = d['categoryName']
                image = d['image'].replace(' ', '%20')
                name = d['categoryName']
                description = d['blurb'] if 'blurb' in d else show['description']
                dateAired = d['dateairedstr'] if 'dateairedstr' in d else ''
                fanart = d['banner'].replace(' ', '%20') if 'banner' in d else ''
                fanart = show['banner'] if 'banner' in show else fanart
                
                data.append({
                    'id' : int(showId),
                    'parentid' : -1,
                    'parentname' : '',
                    'name' : showName.encode('utf8'),
                    'image' : image,
                    'description' : description.encode('utf8'),
                    'shortdescription' : description.encode('utf8'),
                    'year' : dateAired,
                    'fanart' : fanart
                    })
                
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

def getEpisodesPerPage(showId, page, itemsPerPage):
    import re
    data = []
    url = '/Show/GetMoreEpisodes/%s/?page=%s&pageSize=%s'
    html = callServiceApi(url % (showId, page, itemsPerPage))
    episodes = common.parseDOM(html, "div")
    showDetails = sCacheFunction(getShow, showId)
    episodesData = sCacheFunction(getShowEpisodes, showId)
    episodesReturned = 0

    for e in episodes:
        episodesReturned += 1
        url = common.parseDOM(e, "a", ret = 'href')[0]
        episodeId = int(re.compile('/([0-9]+)/', re.IGNORECASE).search(url).group(1))
        image = common.parseDOM(e, "img", ret = 'src')[0].replace(' ', '%20')
        titleDiv = common.parseDOM(e, "div", attrs = { 'class' : 'e-title' })[0]
        title = common.parseDOM(titleDiv, "a")[0]
        titles = title.split(' - ')
        showTitle = titles[0]
        title = titles[1]
        dateAired = title
        shortDescription = common.parseDOM(e, "div", attrs = { 'class' : 'e-desc' })[0]
        showTitle = showDetails['name']
        fanart = showDetails['banner'].replace(' ', '%20')
        description = ''
        episodeNumber = 1
        
        if episodeId in episodesData:
            eData = episodesData[episodeId]
            year = eData['dateaired']
            description = eData['description']
            episodeNumber = eData['episodenumber']
            
        data.append({
            'id' : episodeId,
            'title' : title.encode('utf8'),
            'show' : showTitle.encode('utf8'),
            'image' : image,
            'episodenumber' : episodeNumber,
            'description' : description.encode('utf8'),
            'shortdescription' : shortDescription.encode('utf8'),
            'dateaired' : dateAired,
            'year' : year,
            'fanart' : fanart
            })
            
        if episodesReturned == itemsPerPage:
            break
        
    return data
      
def getShowEpisodes(showId):
    data = {}
    showData = getShow(showId)
    if showData:
        for e in showData['episodes']:
            e['show'] = showData['name']
            e['showimage'] = showData['image'].replace(' ', '%20')
            e['fanart'] = showData['banner'].replace(' ', '%20')
            e['description'] = e['synopsis']
            data[e['id']] = e
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
            episode['year'] = re.compile(', (.+)', re.IGNORECASE).search(episode['dateaired']).group(1)
            episode['description'] = episode['synopsis']
            data = episode
    return data
    
def getEpisodeData(episodeId):
    data = {}
    url = '/Synapse/getepisodedetails/%s'
    data = callJsonApi(url % episodeId)
    return data
    
def getEpisodeVideo(episodeId):
    data = {}
    url = '/Synapse/GetVideo/%s'
    data = callJsonApi(url % episodeId, useCache = False)
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
    for i in range(int(setting('loginRetries')) + 1):
        res = shortCache.get('userSession')
        if res:
            userSession = json.loads(res)
            if userSession:
                return userSession
        login()
    return userSession
    
def getUserUID():
    uid = None
    userSession = getUserSession()
    if userSession and 'data' in userSession:
        uid = userSession['data']['uid']
    log(uid)
    return uid
    
def getUserCookie():
    cookie = None
    userSession = getUserSession()
    if userSession and 'info' in userSession:
        userSession['info']
    return cookie
    
def checkAccountChange():
    email = setting('emailAddress')
    password = setting('password')
    hash = hashlib.sha1(email + password).hexdigest()
    hashFile = os.path.join(xbmc.translatePath(addonInfo('profile')), 'a.tmp')
    savedHash = ''
    accountChanged = False
    if os.path.exists(hashFile):
        with open(hashFile) as f:
            savedHash = f.read()
    if savedHash != hash:
        login()
        accountChanged = True
    if os.path.exists(xbmc.translatePath(addonInfo('profile'))):
        with open(hashFile, 'w') as f:
            f.write(hash)
    return accountChanged
    
def login():
    cookieJar.clear()
    email = setting('emailAddress')
    password = setting('password')
    param = {'email' : email, 'pw' : password}
    userSession = callJsonApi("/Synapse/Login", params = param, base_url = 'https://tfc.tv', useCache = False)
    log(userSession)
    if userSession:
        if 'errorCode' in userSession and userSession['errorCode'] == 0:
            shortCache.set('userSession', json.dumps(userSession))
            return True
        elif 'errorMessage' in userSession:
            showMessage(message, userSession['errorMessage'].encode('utf8'))
    return False
    
    
    
def callServiceApi(path, params = {}, headers = [], base_url = baseUrl, useCache = True):
    import md5
    global cacheActive
    
    res = ''
    cached = False
    toCache = False
    
    key = md5.new(base_url + path + urllib.urlencode(params)).hexdigest()
    log('Key %s : %s - %s' % (key, base_url + path, params))
    
    if cacheActive == 'true' and useCache is True:
        if shortCache.get(key):
            cached = True
            res = shortCache.get(key)
            log('Used cache for (%s)' % key)
        else:
            toCache = True
            log('No cache for (%s)' % key)
    
    if cached is False:
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))
        headers.append(('User-Agent', userAgent))
        opener.addheaders = headers
        log('%s - %s' % (base_url + path, params))
        
        if params:
            data_encoded = urllib.urlencode(params)
            response = opener.open(base_url + path, data_encoded)
        else:
            response = opener.open(base_url + path)
            
        res = response.read()
        log(res)
        
        if toCache is True and res:
            log('Stored in cache (%s) : %s' % (key, res))
            shortCache.set(key, res) 
    
    return res

def callJsonApi(path, params = {}, headers = [('X-Requested-With', 'XMLHttpRequest')], base_url = baseUrl, useCache = True):
    res = callServiceApi(path, params = params, headers = headers, base_url = base_url, useCache = useCache)
    data = json.loads(res)
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

def showMessage(message, title = lang(50107)):
    if not message:
        return
    xbmc.executebuiltin("ActivateWindow(%d)" % (10147, ))
    win = xbmcgui.Window(10147)
    xbmc.sleep(100)
    win.getControl(1).setLabel(title)
    win.getControl(5).setText(message)
    
def log(mixed, level=0):
    if common.dbg and common.dbglevel > level:
        common.log(mixed)

    
#---------------------- MAIN ----------------------------------------
thisPlugin = int(sys.argv[1])
xbmcplugin.setPluginFanart(thisPlugin, 'fanart.jpg')
userAgent = 'Mozilla/5.0(iPad; U; CPU OS 4_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8F191 Safari/6533.18.5'
cookieJar = cookielib.CookieJar()
cookieFile = ''
cookieJarType = ''
if os.path.exists(xbmc.translatePath(addonInfo('profile'))):
    cookieFile = os.path.join(xbmc.translatePath(addonInfo('profile')), 'tfctv.cookie')
    cookieJar = cookielib.LWPCookieJar(cookieFile)
    cookieJarType = 'LWPCookieJar'
if cookieJarType == 'LWPCookieJar':
    try:
        cookieJar.load()
    except:
        login()

params = getParams()
url = None
name = None
mode = None
page = 0
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
elif mode == 5:
    showMostLovedShows()
elif mode == 6:
    showCelebrities()
elif mode == 7:
    showCelebrityInfo(url)
elif mode == 8:
    showLiveStreams(url)
elif mode == 10:
    showCategories()
elif mode == 11:
    showWebsiteSectionShowEpisodes(url)
elif mode == 12:
    showMyAccount()
elif mode == 13:
    showMyInfo()
elif mode == 14:
    showMyEntitlements()
elif mode == 15:
    showMyTransactions()
elif mode == 20:
    reloadCatalogCache()
elif mode == 99:
    callServiceApi(url)
# elif mode == xx:
    # showSubscribedCategories(url)
# elif mode == xx:
    # showSubscribedShows(url)
    
if cookieJarType == 'LWPCookieJar':
    cookieJar.save()

if setting('announcement') != addonInfo('version'):
    messages = {
        '0.0.38': 'Your TFC.tv plugin has been updated.\n\nTFC.tv has undergone a lot of changes and the plugin needs to be updated to adjust to those changes.\n\nIf you encounter anything that you think is a bug, please report it to the TFC.tv XBMC Forum thread (http://forum.xbmc.org/showthread.php?tid=155870) or to the plugin website (https://code.google.com/p/todits-xbmc/).'
        }
    if addonInfo('version') in messages:
        showMessage(messages[addonInfo('version')], lang(50106))
        xbmcaddon.Addon().setSetting('announcement', addonInfo('version'))

