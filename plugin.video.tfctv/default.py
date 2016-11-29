import sys, urllib, urllib2, json, cookielib, time, os.path, hashlib
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
from operator import itemgetter

import CommonFunctions
common = CommonFunctions
thisAddon = xbmcaddon.Addon()
common.plugin = thisAddon.getAddonInfo('name')
baseUrl = 'http://tfc.tv'

# common.dbg = True # Default
# common.dbglevel = 3 # Default

def showCategories():
    checkAccountChange()
    categories = getCategories()
    url = '/Synapse/getsitemenu/%s'
    for c in categories:
        addDir(c['name'], url % c['id'], 1, 'icon.png')
    addDir('Celebrities', '/Synapse/GetAllCelebrities', 6, 'icon.png')
    addDir('My account', '', 12, 'icon.png')
    xbmcplugin.endOfDirectory(thisPlugin)

def getCategories():
    url = '/Synapse/getsitemenu'
    data = callJsonApi(url)
    return data
    
def showSubCategories(url):
    addDir('Most loved shows', '/Synapse/GetMostLovedShows', 5, 'icon.png')
    data = callJsonApi(url)
    subCatList = extractSubCategory(data, url)
    for s in subCatList:
        addDir(s[0].encode('utf8'), '%s' % s[1], 2, 'menu_logo.png')
    xbmcplugin.endOfDirectory(thisPlugin)
        
def extractSubCategory(categories, url):
    subcat = {}
    for c in categories:
        if str(c['id']) in url:
           subcat = c['menu']
           break
    subCategories = []
    urlShow = '/Synapse/GetShows/%s'
    for s in subcat:
        title = s['name']
        url = urlShow % s['id']
        if title and url:
            subCategories.append((title, url))
    return subCategories

def showMostLovedShows(url):
    data = getMostLovedShowsData(url)
    if len(data) == 0:
        xbmcplugin.endOfDirectory(thisPlugin)
        return
    showShows(data)

def getMostLovedShowsData(url):
    showListData = {}
    data = callJsonApi(url)
    if data and len(data) > 0:
        showListData = extractMostLovedShowListData(data)
    return showListData
    
def extractMostLovedShowListData(data):
    showListData = {}
    for d in data:
        thumbnail = d['image'].replace(' ', '%20')
        title = d['categoryName']
        showData = extractShowData(d)
        showID = d['categoryId']
        showListData[showID] = (title.encode('utf8'), thumbnail, showData)			
    return showListData
    
def showCategoryShows(url):
    data = getShowListData(url)
    if len(data) == 0:
        xbmcplugin.endOfDirectory(thisPlugin)
        return
    showShows(data)

def showShows(showListData):
    listSubscribedFirst = True if thisAddon.getSetting('listSubscribedFirst') == 'true' else False
    italiciseUnsubscribed = True if thisAddon.getSetting('italiciseUnsubscribed') == 'true' else False
    listSubscribedFirst = False
    italiciseUnsubscribed = False
    subscribedShowIds = []
    if listSubscribedFirst or italiciseUnsubscribed: 
        # make an API call only if we're checking against subscribed shows
        subscribedShowIds = getSubscribedShowIds()
    if listSubscribedFirst:
        unsubscribedShows = []
        # try to minimize loops
        sortedShowInfos = []
        sortedUnsubscibed = []
        for showId, (showName, thumbnail, kwargs) in showListData.iteritems():
            if showId in subscribedShowIds:
                sortedShowInfos.append((showName.lower(), showName, str(showId), 3, thumbnail, kwargs))
                # addDir(showName, str(showId), 3, thumbnail, True, info[5])
            else:
                showTitle = '[I]' + showName + '[/I]' if italiciseUnsubscribed else showName
                # we'll add these unsubscribed shows later
                # unsubscribedShows.append((showId, showTitle, thumbnail))
                sortedUnsubscibed.append((showName.lower(), showTitle, showId, 3, thumbnail, kwargs))
        sortedShowInfos = sorted(sortedShowInfos, key = itemgetter(0))
        sortedUnsubscibed = sorted(sortedUnsubscibed, key = itemgetter(0))
        for info in sortedShowInfos:
            addDir(info[1], info[2], info[3], info[4], isFolder = True, **info[5])
        # for showId, showTitle, thumbnail in unsubscribedShows:
        for info in sortedUnsubscibed:
            addDir(info[1], info[2], info[3], info[4], isFolder = True, **info[5])
    else:
        sortedShowInfos = []
        for showId, (showName, thumbnail, kwargs) in showListData.iteritems():
            showTitle = '[I]' + showName + '[/I]' if italiciseUnsubscribed and showId in subscribedShowIds else showName
            sortedShowInfos.append((showName.lower(), showTitle, str(showId), 3, thumbnail, kwargs))
            # addDir(showTitle, str(showId), 3, thumbnail, True, info[5])
        sortedShowInfos = sorted(sortedShowInfos, key = itemgetter(0))
        for info in sortedShowInfos:
            addDir(info[1], info[2], info[3], info[4], isFolder = True, **info[5])
    xbmcplugin.endOfDirectory(thisPlugin)
    
def getShowListData(url):
    showListData = {}
    data = callJsonApi(url)
    if data and 'shows' in data:
        showListData = extractShowListData(data['shows'])
    return showListData
	
def extractShowListData(data):
    showListData = {}
    for d in data:
        thumbnail = d['image'].replace(' ', '%20')
        title = d['name']
        showData = extractShowData(d)
        showID = d['id']
        showListData[showID] = (title.encode('utf8'), thumbnail, showData)			
    return showListData
	
def extractShowData(data):
    description = data['blurb'] if 'blurb' in data else ''
    dateAired = data['dateairedstr'] if 'dateairedstr' in data else ''
    # nbEpisodes = len(data['episodes']) if data['episodes'] is None else data['episodes']
    banner = data['banner'].replace(' ', '%20') if 'banner' in data else ''
    # showData = { 'listArts' : { 'poster' : poster }, 'listInfos' : { 'video' : { 'plot' : description, 'aired' : dateAired, 'status' : nbEpisodes } } }
    showData = { 'listArts' : { 'fanart' : banner, 'banner' : banner }, 'listInfos' : { 'video' : { 'plot' : description, 'year' : dateAired } } }
    return showData
    
def showEpisodes(showId):
    url = '/Synapse/getshowdetails/%s'
    showData = callJsonApi(url % showId)
    episodesData = {}
    for e in showData['episodes']:
        episodesData[e['id']] = e
    itemsPerPage = int(thisAddon.getSetting('itemsPerPage'))
    url = '/Show/GetMoreEpisodes/%s/?page=%s&pageSize=%s' % (showId, page, itemsPerPage)
    episodes_html = callServiceApi(url)
    episode_data = common.parseDOM(episodes_html, "div")
    episodes_returned = 0
    for e in episode_data:
        episodes_returned = episodes_returned + 1
        episode_hrefs = common.parseDOM(e, "a", ret = 'href') # there will be at least 2 hrefs but they are all duplicates
        episode_id = episode_hrefs[0].replace('/Episode/Details/', '').split('|')[0]
        image_url = common.parseDOM(e, "img", ret = 'src')[0].replace(' ', '%20')
        title_div = common.parseDOM(e, "div", attrs = { 'class' : 'e-title' })[0]
        shortDescription = common.parseDOM(e, "div", attrs = { 'class' : 'e-desc' })[0]
        title_tag = common.parseDOM(title_div, "a")[0]
        id = int(episode_id.split('/')[0])
        showTitle = showData['name']
        fanart = showData['banner'].replace(' ', '%20')
        dateAired = ''
        description = ''
        episodeNumber = 1
        if id in episodesData:
            eData = episodesData[id]
            dateAired = eData['dateaired']
            description = eData['synopsis']
            episodeNumber = eData['episodenumber']
        kwargs = { 'listArts' : { 'fanart' : fanart, 'banner' : fanart }, 'listProperties' : { 'IsPlayable' : 'true' } , 'listInfos' : { 'video' : { 'tvshowtitle' : showTitle, 'episode' : episodeNumber, 'tracknumber' : episodeNumber, 'plot' : description, 'aired' : dateAired, 'year' : dateAired } } }
        addDir(title_tag.split('-')[-1].strip().encode('utf8'), episode_id, 4, image_url, isFolder = False, **kwargs)
    if episodes_returned == itemsPerPage:
        addDir("Next >>",  showId, 3, '', page + 1)
    xbmcplugin.endOfDirectory(thisPlugin)
        
def playEpisode(url):
    errorCode = -1
    episodeDetails = {}
    episode = url.split('/')[0]
    for i in range(int(thisAddon.getSetting('loginRetries')) + 1):
        episodeDetails = get_media_info(episode)
        if episodeDetails and episodeDetails.has_key('errorCode') and episodeDetails['errorCode'] == 0:
            break
        else:
            login()
    if episodeDetails and episodeDetails.has_key('errorCode') and episodeDetails['errorCode'] == 0:
        url = episodeDetails['data']['Url']
        liz=xbmcgui.ListItem(name, iconImage = "DefaultVideo.png", thumbnailImage = thumbnail, path = url)
        liz.setInfo( type="Video", infoLabels = { "Title": name } )
        liz.setProperty('IsPlayable', 'true')
        return xbmcplugin.setResolvedUrl(thisPlugin, True, liz)
    else:
        if (not episodeDetails) or (episodeDetails and episodeDetails.has_key('errorCode') and episodeDetails['errorCode'] != 0):
            xbmc.executebuiltin('Notification(%s, %s)' % (xbmcaddon.Addon().getLocalizedString(57000), xbmcaddon.Addon().getLocalizedString(57001)))
    return False
    
def get_media_info(episode):
    media_info = callJsonApi('/Synapse/GetVideo/%s' % episode)
    return media_info
    
def showCelebrities(url):
    data = callJsonApi(url)
    for d in data:
        image = d['ImageUrl'].encode('utf8').replace(' ', '%20')
        lastName = d['LastName'].encode('utf8') if d['LastName'] else ''
        firstName = d['FirstName'].encode('utf8') if d['FirstName'] else ''
        addDir('%s %s' % (lastName, firstName), '/Synapse/GetCelebrityDetails/%s' % d['CelebrityId'], 7, image, isFolder = False)
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
        message = xbmcaddon.Addon().getLocalizedString(57002)
    showMessage(message, name)
    
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
                for i in range(int(thisAddon.getSetting('loginRetries')) + 1):
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
    showThumbnails = True if thisAddon.getSetting('showSubscribedShowsThumbnails') == 'true' else False
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
    
def getEntitlementsData(url):
    htmlData = callServiceApi(url)
    data = extractEntitlementData(htmlData)
    return data
    
def extractEntitlementData(htmlData):
    data = {'data' : [], 'total': 0}
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
    
def showMyAccount():
    categories = [
        { 'name' : 'My info', 'url' : '/Synapse/GetUserData?uid=%s', 'mode' : 13 },
        { 'name' : 'Entitlements', 'url' : '/User/Entitlements', 'mode' : 14 },
        { 'name' : 'Transactions', 'url' : '/Synapse/MyTransactions', 'mode' : 15 }
    ]
    for c in categories:
        addDir(c['name'], c['url'], c['mode'], 'icon.png')
    xbmcplugin.endOfDirectory(thisPlugin)
    
def showMyInfo(url):
    global UID
    if UID is None:
        login()
    data = callJsonApi(url % UID)
    d = data['data']
    message = 'Email: %s\nFirst name: %s\nLast name: %s\nCountry: %s\nState: %s\nCity: %s\n\n' % (d['Email'].encode('utf8'), d['FirstName'].encode('utf8'), d['LastName'].encode('utf8'), d['CountryCode'].encode('utf8'), d['State'].encode('utf8'), d['City'].encode('utf8'))
    showMessage(message, xbmcaddon.Addon().getLocalizedString(56001))

def showMyEntitlements(url):
    data = getEntitlementsData(url)
    message = ''
    for entitlement in data['data']:
        entitlementEntry = 'Package Name: %s\n    EID: %s\n    Expiry Date: %s\n\n' % (entitlement['Content'], entitlement['EntitlementId'], entitlement['ExpiryDate'])
        message += entitlementEntry
    showMessage(message, xbmcaddon.Addon().getLocalizedString(56002))
    
def showMyTransactions(url):
    transactions = callJsonApi(url)
    if len(transactions) > 0:
        message = ''
        for t in transactions:
            expiryUnixTime = (int(t['TransactionDate'].replace('/Date(','').replace(')/', ''))) / 1000
            message += 'TID: %s\nProduct: %s\nDate: %s\nAmount: %.2f\nCurrency: %s\nType: %s\nMode: %s\nReference: %s\n\n' % (t['TransactionId'], t['ProductName'].encode('utf8'), time.strftime('%B %d, %Y %X %Z', time.localtime(expiryUnixTime)), t['Amount'], t['Currency'].encode('utf8'), t['TransactionType'].encode('utf8'), t['Method'].encode('utf8'), t['Reference'].encode('utf8'))
        showMessage(message, xbmcaddon.Addon().getLocalizedString(56003))
    else:
        login()
    
def callServiceApi(path, params = {}, headers = [], base_url = baseUrl):
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))
    headers.append(('User-Agent', userAgent))
    opener.addheaders = headers
    # common.log(base_url + path)
    if params:
        data_encoded = urllib.urlencode(params)
        response = opener.open(base_url + path, data_encoded)
    else:
        response = opener.open(base_url + path)
    return response.read()

def callJsonApi(url, params = {}, headers = [('X-Requested-With', 'XMLHttpRequest')], base_url = baseUrl):
    res = callServiceApi(url, params = params, headers = headers, base_url = base_url)
    data = json.loads(res)
    return data
    
def login():
    global UID
    cookieJar.clear()
    emailAddress = thisAddon.getSetting('emailAddress')
    password = thisAddon.getSetting('password')
    param = {'email' : emailAddress, 'pw' : password}
    jsonData = callJsonApi("/Synapse/Login", params = param, base_url = 'https://tfc.tv')
    UID = jsonData['data']['uid']
    
def checkAccountChange():
    emailAddress = thisAddon.getSetting('emailAddress')
    password = thisAddon.getSetting('password')
    hash = hashlib.sha1(emailAddress + password).hexdigest()
    hashFile = os.path.join(xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile')), 'a.tmp')
    savedHash = ''
    accountChanged = False
    if os.path.exists(hashFile):
        with open(hashFile) as f:
            savedHash = f.read()
    if savedHash != hash:
        login()
        accountChanged = True
    if os.path.exists(xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))):
        with open(hashFile, 'w') as f:
            f.write(hash)
    return accountChanged
    
def getParams():
    param={}
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
            params=sys.argv[2]
            cleanedparams=params.replace('?','')
            if (params[len(params)-1]=='/'):
                    params=params[0:len(params)-2]
            pairsofparams=cleanedparams.split('&')
            param={}
            for i in range(len(pairsofparams)):
                    splitparams={}
                    splitparams=pairsofparams[i].split('=')
                    if (len(splitparams))==2:
                            param[splitparams[0]]=splitparams[1]
    return param

def addDir(name, url, mode, thumbnail, page = 0, isFolder = True, **kwargs):
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&page="+str(page)+"&thumbnail="+urllib.quote_plus(thumbnail)
    liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=thumbnail)
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
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
    return xbmcplugin.addDirectoryItem(handle=thisPlugin,url=u,listitem=liz,isFolder=isFolder)

def showMessage(message, title = xbmcaddon.Addon().getLocalizedString(50107)):
    if not message:
        return
    xbmc.executebuiltin("ActivateWindow(%d)" % (10147, ))
    win = xbmcgui.Window(10147)
    xbmc.sleep(100)
    win.getControl(1).setLabel(title)
    win.getControl(5).setText(message)

thisPlugin = int(sys.argv[1])
xbmcplugin.setPluginFanart(thisPlugin, 'fanart.jpg')
userAgent = 'Mozilla/5.0(iPad; U; CPU OS 4_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8F191 Safari/6533.18.5'
cookieJar = cookielib.CookieJar()
cookieFile = ''
cookieJarType = ''
if os.path.exists(xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))):
    cookieFile = os.path.join(xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile')), 'tfctv.cookie')
    cookieJar = cookielib.LWPCookieJar(cookieFile)
    cookieJarType = 'LWPCookieJar'
if cookieJarType == 'LWPCookieJar':
    try:
        cookieJar.load()
    except:
        login()

params=getParams()
url=None
name=None
mode=None
page=0
thumbnail = ''
onlinePremierUrl = '/Category/List/1962'
UID=None


try:
    url=urllib.unquote_plus(params["url"])
except:
    pass
try:
    name=urllib.unquote_plus(params["name"])
except:
    pass
try:
    mode=int(params["mode"])
except:
    pass
try:
    page=int(params["page"])
except:
    pass
try:
    thumbnail=urllib.unquote_plus(params["thumbnail"])
except:
    pass
    
if (mode != 12) and ((mode == None) or (url == None) or (len(url) < 1)):
    showCategories()
elif mode == 1:
    showSubCategories(url)
elif mode == 2:
    showCategoryShows(url)
elif mode == 3:
    showEpisodes(url)
elif mode == 4:
    playEpisode(url)
elif mode == 5:
    showMostLovedShows(url)
elif mode == 6:
    showCelebrities(url)
elif mode == 7:
    showCelebrityInfo(url)
elif mode == 10:
    showSubscribedCategories(url)
elif mode == 11:
    showSubscribedShows(url)
elif mode == 12:
    showMyAccount()
elif mode == 13:
    showMyInfo(url)
elif mode == 14:
    showMyEntitlements(url)
elif mode == 15:
    showMyTransactions(url)
    
if cookieJarType == 'LWPCookieJar':
    cookieJar.save()

if thisAddon.getSetting('announcement') != thisAddon.getAddonInfo('version'):
    messages = {
        '0.0.38': 'Your TFC.tv plugin has been updated.\n\nTFC.tv has undergone a lot of changes and the plugin needs to be updated to adjust to those changes.\n\nIf you encounter anything that you think is a bug, please report it to the TFC.tv XBMC Forum thread (http://forum.xbmc.org/showthread.php?tid=155870) or to the plugin website (https://code.google.com/p/todits-xbmc/).'
        }
    if thisAddon.getAddonInfo('version') in messages:
        showMessage(messages[thisAddon.getAddonInfo('version')], xbmcaddon.Addon().getLocalizedString(50106))
        xbmcaddon.Addon().setSetting('announcement', thisAddon.getAddonInfo('version'))
