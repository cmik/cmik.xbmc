# -*- coding: utf-8 -*-

'''
    Tfc.tv Add-on
    Copyright (C) 2018 cmik
'''

import os,sys,re,urllib,urllib2,ssl,cookielib,json,datetime,time,hashlib
from operator import itemgetter
from resources import config
from resources.lib.libraries import control
from resources.lib.libraries import cache
from resources.lib.models import episodes
from resources.lib.models import shows
from resources.lib.models import library
from resources.lib.models import showcast

common = control.common
logger = control.logger

# Load DB
episodeDB = episodes.Episode(control.episodesFile)
showDB = shows.Show(control.showsFile)
libraryDB = library.Library(control.libraryFile)
castDB = showcast.ShowCast(control.celebritiesFile)

Logged = False

#---------------------- FUNCTIONS ----------------------------------------                  

def playEpisode(url, name, thumbnail, bandwidth=False):
    logger.logInfo('called function')
    errorCode = -1
    episodeDetails = {}
    episode = url.split('/')[0]
    
    if checkProxy() == True:
        # Check if logged in
        if control.setting('emailAddress') != '' and isLoggedIn() == False:
            control.showNotification(control.lang(57012), control.lang(50002))
            login()
            
        # for i in range(int(control.setting('loginRetries')) + 1):
            # episodeDetails = getMediaInfo(episode, name, thumbnail)
            # if episodeDetails and 'errorCode' in episodeDetails and episodeDetails['errorCode'] == 0 and 'data' in episodeDetails:
                # break
            # else:
                # login()
                
        episodeDetails = getMediaInfo(episode, name, thumbnail, bandwidth)
        logger.logInfo(episodeDetails)
        if episodeDetails and 'errorCode' in episodeDetails and episodeDetails['errorCode'] == 0 and 'data' in episodeDetails:
            if 'preview' in episodeDetails['data'] and episodeDetails['data']['preview'] == True:
                control.infoDialog(control.lang(57025), control.lang(50002), time=5000)
            elif 'StatusMessage' in episodeDetails and episodeDetails['StatusMessage'] != '':
                control.showNotification(episodeDetails['StatusMessage'], control.lang(50009))
            url = control.setting('proxyStreamingUrl') % (control.setting('proxyHost'), control.setting('proxyPort'), urllib.quote(episodeDetails['data']['uri'])) if not episodeDetails.get('useDash', False) and (control.setting('useProxy') == 'true') else episodeDetails['data']['uri']
            liz = control.item(name, path=url, thumbnailImage=thumbnail, iconImage="DefaultVideo.png")
            liz.setInfo(type='video', infoLabels={
                'title': name, 
                'sorttitle' : episodeDetails['data']['dateaired'],
                'tvshowtitle' : episodeDetails['data']['show'],
                'genre' : episodeDetails['data']['parentname'],
                'episode' : episodeDetails['data']['episodenumber'],
                'tracknumber' : episodeDetails['data']['episodenumber'],
                'plot' : episodeDetails['data']['plot'],
                'aired' : episodeDetails['data']['dateaired'],
                'year' : episodeDetails['data']['year'],
                'mediatype' : episodeDetails['data']['ltype'] 
                })

            # Add eventual subtitles
            if 'track' in episodeDetails['data'] and len(episodeDetails['data']['track']) and 'src' in episodeDetails['data']['track'][0]:
                try: 
                    liz.setSubtitles([episodeDetails['data']['track'][0]['src']])
                    if 'srclang' in episodeDetails['data']['track'][0]: liz.addStreamInfo('subtitle', {'language' : episodeDetails['data']['track'][0]['srclang']})
                except: pass

            if episodeDetails.get('useDash', False):
                logger.logInfo(episodeDetails['dash'])
                liz.setProperty('inputstreamaddon', 'inputstream.adaptive')
                liz.setProperty('inputstream.adaptive.manifest_type', 'mpd')
                liz.setProperty('inputstream.adaptive.license_type', episodeDetails['dash']['type'])
                liz.setProperty('inputstream.adaptive.stream_headers', episodeDetails['dash']['headers'])
                liz.setProperty('inputstream.adaptive.license_key', 
                    '%s|%s|%s|%s' % (episodeDetails['dash']['key'], episodeDetails['dash']['headers'], 'b{SSM}', 'R'))
                liz.setMimeType(episodeDetails['data']['type'])
                # liz.setContentLookup(False)
            
            liz.setProperty('fanart_image', episodeDetails['data']['fanart'])
            liz.setProperty('IsPlayable', 'true')
            try: 
                return control.resolve(thisPlugin, True, liz)
            except: 
                control.showNotification(control.lang(57032), control.lang(50004))
        elif (not episodeDetails) or (episodeDetails and 'errorCode' in episodeDetails and episodeDetails['errorCode'] != 0):
            logger.logNotice(episodeDetails['StatusMessage'])
            if 'StatusMessage' in episodeDetails:
                control.showNotification(episodeDetails['StatusMessage'], control.lang(50004))
            else:
                control.showNotification(control.lang(57001), control.lang(50009))
    return False
    
def getMediaInfo(episodeId, title, thumbnail, bandwidth=False):
    logger.logInfo('called function')
    mediaInfo = getMediaInfoFromWebsite(episodeId, bandwidth)
    if mediaInfo['errorCode'] == 1:
        mediaInfo['errorCode'] = 0
    
    if mediaInfo['errorCode'] == 0:
        e = {
            'id' : int(episodeId),
            'title' : title,
            'parentid' : int(mediaInfo['data']['showid']),
            'show' : mediaInfo['data']['show'],
            'image' : thumbnail,
            'fanart' : mediaInfo['data']['fanart'],
            'episodenumber' : mediaInfo['data']['episodenumber'],
            'url' : mediaInfo['data']['url'],
            'description' : mediaInfo['data']['plot'],
            'shortdescription' : mediaInfo['data']['plot'],
            'dateaired' : mediaInfo['data']['dateaired'],
            'date' : mediaInfo['data']['date'],
            'year' : mediaInfo['data']['year'],
            'parentalAdvisory' : mediaInfo['data']['parentalAdvisory'],
            'ltype' : mediaInfo['data']['ltype'],
            'type' : 'episode',
            'duration' : mediaInfo['data']['duration'],
            'views' : mediaInfo['data']['views'] + 1,
            'rating' : mediaInfo['data']['rating'],
            'votes' : mediaInfo['data']['votes']
            }
        episodeDB.set(e)

        s = mediaInfo['data']['showObj']
        showDB.update({'id' : s.get('id'), 'views' : s.get('views', 0) + 1})
        
    return mediaInfo

def getEpisodeBandwidthList(episodeId, title, thumbnail):
    logger.logInfo('called function')
    mediaInfo = getMediaInfoFromWebsite(episodeId)
    data = []
    if mediaInfo['errorCode'] <= 1:
        for (bandwidth, resolution) in mediaInfo['data']['bandwidth'].iteritems():
            data.append({
            'id' : int(episodeId),
            'title' : title,
            'parentid' : int(mediaInfo['data']['showid']),
            'show' : mediaInfo['data']['show'],
            'image' : thumbnail,
            'fanart' : mediaInfo['data']['fanart'],
            'episodenumber' : mediaInfo['data']['episodenumber'],
            'url' : mediaInfo['data']['url'],
            'description' : mediaInfo['data']['plot'],
            'shortdescription' : mediaInfo['data']['plot'],
            'dateaired' : mediaInfo['data']['dateaired'],
            'date' : mediaInfo['data']['date'],
            'year' : mediaInfo['data']['year'],
            'parentalAdvisory' : mediaInfo['data']['parentalAdvisory'],
            'ltype' : mediaInfo['data']['ltype'],
            'type' : 'episode',
            'duration' : mediaInfo['data']['duration'],
            'views' : mediaInfo['data']['views'],
            'rating' : mediaInfo['data']['rating'],
            'votes' : mediaInfo['data']['votes'],
            'showObj' : mediaInfo['data']['showObj'],
            'bandwidth' : int(bandwidth), 
            'resolution' : resolution})
    return data

def getMediaInfoFromWebsite(episodeId, bandwidth=False):
    logger.logInfo('called function with param (%s, %s)' % (str(episodeId), bandwidth))
    
    mediaInfo = {}
    html = callServiceApi(config.uri.get('episodeDetails') % episodeId, base_url = config.websiteUrl, useCache=False)

    err = checkIfError(html)
    if err.get('error') == True:
        mediaInfo['StatusMessage'] = err.get('message')
        mediaInfo['errorCode'] = 2
    else :    
        mediaInfo['data'] = {}
        mediaInfo['data']['url'] = common.parseDOM(html, "link", attrs = { 'rel' : 'canonical' }, ret = 'href')[0]
        
        episodeData = json.loads(re.compile('var ldj = (\{.+\})', re.IGNORECASE).search(html).group(1))
        logger.logInfo(episodeData)

        # Parental advisory
        mediaInfo['data']['parentalAdvisory'] = 'false'
        if re.compile('var dfp_c = ".*2900.*";', re.IGNORECASE).search(html):
            mediaInfo['data']['parentalAdvisory'] = 'true'
            if control.setting('parentalAdvisoryCheck') == 'true':
                control.alert(control.lang(57011),title=control.lang(50003))
            if control.setting('parentalControl') == 'true':
                code = control.numpad(control.lang(57021))
                if code != control.setting('parentalCode'):
                    mediaInfo['StatusMessage'] = control.lang(57022)
                    mediaInfo['errorCode'] = 3
                    mediaInfo['data'] = {}
                    return mediaInfo
                
        sid = None
        sidmatch = re.compile('(media/fetch.+sid: (\d+),)', re.IGNORECASE).search(html)
        if sidmatch:
            sid = sidmatch.group(2)
                
        if sid:
            mediaInfo['data']['showid'] = sid
            cookie = getCookieContent() 
            if control.setting('generateNewFingerprintID') == 'true':
                generateNewFingerprintID()
            
            cookie.append('cc_fingerprintid='+control.setting('fingerprintID'))
            if control.setting('previousFingerprintID') != '':
                cookie.append('cc_prevfingerprintid='+control.setting('previousFingerprintID'))
            
            callHeaders = [
                ('Accept', 'application/json, text/javascript, */*; q=0.01'), 
                ('X-Requested-With', 'XMLHttpRequest'),
                ('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8'),
                ('Cookie', '; '.join(cookie)),
                ('Host', 'tfc.tv'),
                ('Origin', config.websiteUrl),
                ('Referer', config.websiteUrl+'/')
                ]
            params = {
                'eid': episodeId, 
                'pv': 'false', 
                'sid' : sid
                }
            episodeDetails = callJsonApi(config.uri.get('mediaFetch'), params, callHeaders, base_url=config.websiteSecuredUrl, useCache=False, jsonData=True)
            logger.logDebug(episodeDetails)
            if episodeDetails and 'StatusCode' in episodeDetails:
                mediaInfo['errorCode'] = episodeDetails['StatusCode']
                if 'media' in episodeDetails and 'source' in episodeDetails['media'] and 'src' in episodeDetails['media']['source'][0] :
                    episodeDetails['media']['uri'] = episodeDetails['media']['source'][0]['src']
                    # DVR Window 
                    # episodeDetails['media']['uri'] += '&dw=30&n10'
                    # limit by bitrate
                    # episodeDetails['media']['uri'] += '&b=700-1800'
                    # prefered bitrate
                    # episodeDetails['media']['uri'] += '&_b_=1800'
                    if 'type' in episodeDetails['media']['source'][0]:
                        episodeDetails['media']['type'] = episodeDetails['media']['source'][0]['type']

                    if control.setting('streamServerModification') == 'true' and control.setting('streamServer') != '':
                        episodeDetails['media']['uri'] = episodeDetails['media']['uri'].replace('https://o2-i.', control.setting('streamServer'))                
                    
                    # check if amssabscbn.akamaized.net to use inputstream.adaptive
                    if 'amssabscbn.akamaized.net' in episodeDetails['media']['uri']:
                        mediaInfo['StatusMessage'] = control.lang(57038)
                        mediaInfo['errorCode'] = 5

                        mediaInfo['useDash'] = True
                        headers = 'Origin=%s&Referer=%s' % (config.websiteUrl, config.websiteUrl)
                        if len(episodeDetails['media']['keys']['com.widevine.alpha']['httpRequestHeaders']) > 0:
                            headers += '&' + '&'.join("%s=%s" % (key,val) for (key,val) in episodeDetails['media']['keys']['com.widevine.alpha']['httpRequestHeaders'].iteritems())
                        if 'com.widevine.alpha' in episodeDetails['media']['keys']:
                            mediaInfo['dash'] = {
                                'type': 'com.widevine.alpha',
                                'headers': headers,
                                'key': episodeDetails['media']['keys']['com.widevine.alpha']['serverURL']
                                }
                        elif 'com.microsoft.playready' in episodeDetails['media']['keys']:
                            mediaInfo['dash'] = {
                                'type': 'com.microsoft.playready',
                                'headers': headers,
                                'key': episodeDetails['media']['keys']['com.microsoft.playready']['serverURL']
                                }
                        # elif 'com.apple.fps.1_0' in episodeDetails['media']['keys']:
                            # mediaInfo['dash'] = {
                                # 'header': episodeDetails['media']['keys']['com.widevine.alpha']['httpRequestHeaders'],
                                # 'key': episodeDetails['media']['keys']['com.widevine.alpha']['httpRequestHeaders']
                                # }
                    else: 
                        # choose best stream quality
                        mediaInfo['data']['bandwidth'] = {}
                        m3u8 = callServiceApi(episodeDetails['media']['uri'], base_url = '', headers=[])
                        if m3u8:
                            lines = m3u8.split('\n')
                            i = 0
                            bestBandwidth = 0
                            choosedStream = ''
                            for l in lines:
                                bw_match = re.compile('BANDWIDTH=([0-9]+)', re.IGNORECASE).search(lines[i])
                                if bw_match :
                                    currentBandwidth = int(bw_match.group(1))
                                    res_match = re.compile('RESOLUTION=([0-9]+x[0-9]+)', re.IGNORECASE).search(lines[i])
                                    if res_match :
                                        mediaInfo['data']['bandwidth'][str(currentBandwidth)] = res_match.group(1)
                                    if bandwidth != False and currentBandwidth == int(bandwidth):
                                        choosedStream = lines[i+1]
                                        break
                                    elif currentBandwidth > bestBandwidth:
                                        bestBandwidth = currentBandwidth
                                        choosedStream = lines[i+1]
                                    i+=2
                                else:
                                    i+=1

                                if i >= len(lines):
                                    break

                            if control.setting('chooseBestStream') == 'true' or bandwidth != False: 
                                logger.logInfo(choosedStream)
                                episodeDetails['media']['uri'] = choosedStream
                        else:
                            mediaInfo['StatusMessage'] = control.lang(57032)
                            mediaInfo['errorCode'] = 9
                        
                    res = showDB.get(sid)
                    show = res[0] if len(res) == 1 else {}

                    res = episodeDB.get(int(episodeId))
                    episode = res[0] if len(res) == 1 else {}
                    
                    mediaInfo['data'].update(episodeDetails['media'])
                    mediaInfo['data']['preview'] = episodeDetails['mediainfo']['preview']
                    mediaInfo['data']['show'] = show.get('name', episodeData.get('name'))
                    mediaInfo['data']['parentname'] = show.get('parentname', episodeData.get('genre', ''))
                    mediaInfo['data']['rating'] = show.get('rating', episodeData.get('aggregateRating' , {}).get('ratingValue', 0))
                    if mediaInfo['data']['rating'] == None: mediaInfo['data']['rating'] = 0
                    mediaInfo['data']['votes'] = show.get('votes', episodeData.get('aggregateRating' , {}).get('reviewCount', 0))
                    if mediaInfo['data']['votes'] == None: mediaInfo['data']['votes'] = 0
                    mediaInfo['data']['plot'] = episodeData.get('description')
                    mediaInfo['data']['image'] = episodeData.get('thumbnailUrl')
                    mediaInfo['data']['fanart'] = show.get('fanart', episodeData.get('image'))
                    mediaInfo['data']['ltype'] = 'episode' if episodeData.get('@type', 'episode').lower() not in ('episode','movie') else episodeData.get('@type', 'episode').lower()
                    try:
                        datePublished = datetime.datetime.strptime(episodeData.get('datePublished'), '%Y-%m-%d')
                    except TypeError:
                        datePublished = datetime.datetime(*(time.strptime(episodeData.get('datePublished'), '%Y-%m-%d')[0:6]))
                    mediaInfo['data']['dateaired'] = datePublished.strftime('%b %d, %Y')
                    mediaInfo['data']['date'] = datePublished.strftime('%Y-%m-%d')
                    mediaInfo['data']['year'] = datePublished.strftime('%Y')
                    mediaInfo['data']['episodenumber'] = 1 if type == 'movie' else episodeData.get('episodeNumber')
                    mediaInfo['data']['duration'] = 0
                    duration = re.compile('^([0-9]+)h([0-9]*)[m]?|([0-9]+)m$', re.IGNORECASE).search(episodeData.get('duration', episodeData.get('timeRequired', 0)))
                    if duration: 
                        if duration.group(1) != None:
                            if duration.group(2) != '': mediaInfo['data']['duration'] = int(duration.group(2))
                            mediaInfo['data']['duration'] += int(duration.group(1)) * 60
                        elif duration.group(3) != None: 
                            mediaInfo['data']['duration'] = int(duration.group(3))
                    mediaInfo['data']['views'] = episode.get('views', 0)
                    mediaInfo['data']['showObj'] = show
                
                logger.logDebug(mediaInfo)
                    
                if 'StatusMessage' in episodeDetails and episodeDetails['StatusMessage'] != '' and episodeDetails['StatusMessage'] != 'OK':
                    mediaInfo['StatusMessage'] = episodeDetails['StatusMessage']
    
    return mediaInfo

def resetCatalogCache():
    logger.logInfo('called function')
    episodeDB.drop()
    showDB.drop()
    control.showNotification(control.lang(57039), control.lang(50010))
    reloadCatalogCache()

def reloadCatalogCache():
    logger.logInfo('called function')
    updateEpisodes = False
    if (control.confirm(control.lang(57035), line1=control.lang(57036), title=control.lang(50402))):
        updateEpisodes = True
    if updateCatalogCache(updateEpisodes) is True:
        control.showNotification(control.lang(57003), control.lang(50010))
    else:
        control.showNotification(control.lang(57027), control.lang(50004))
    
def updateCatalogCache(loadEpisodes=False):
    logger.logInfo('called function')
    control.showNotification(control.lang(57015), control.lang(50005))
    cache.longCache.cacheClean(True) 
    cache.shortCache.cacheClean(True)
    
    # checkElaps = lambda x, y: x = time.time()-x if (time.time()-x) > y else x
    elaps = start = time.time()
    
    try:
        # update sections cache
        # if control.setting('displayWebsiteSections') == 'true':
            # control.showNotification(control.lang(57013))
            # sections = cache.sCacheFunction(getWebsiteHomeSections)
            # for section in sections:
                # cache.sCacheFunction(getWebsiteSectionContent, section['id'])
        
        # update categories cache
        control.showNotification(control.lang(57014), control.lang(50005))
        # categories = cache.lCacheFunction(getCategories)
        categories = getCategories()
        nbCat = len(categories)
        i = 0
    except Exception as e:
        logger.logError('Can\'t update the catalog : %s' % (str(e)))
        return False
        
    for cat in categories:
        nbSubCat = 0
        try: 
            subCategories = getSubCategories(cat['id'])
            nbSubCat = len(subCategories)
        except Exception as ce:
            logger.logError('Can\'t update category %s : %s' % (cat['id'], str(ce)))
            continue
        j = 0
        for sub in subCategories:
            nbShow = 0
            try: 
                shows = getShows(sub['id'])
                nbShow = len(shows)
            except Exception as sce: 
                logger.logError('Can\'t update subcategory %s : %s' % (sub['id'], str(sce)))
                j+=1
                continue
            k = 0
            for s in shows:
                try: 
                    if loadEpisodes: episodes = getEpisodesPerPage(s['id'], sub['id'], s['year'], 1)
                    else: show = getShow(s['id'], sub['id'], s['year'])
                except Exception as se: 
                    logger.logError('Can\'t update show %s : %s' % (s['id'], str(se)))
                    k+=1
                    continue
                k+=1
                
                elaps = time.time()-start 
                if elaps > 5:
                    start = time.time()
                    catpercent = 100 * i / nbCat
                    cat1percent = 100 * 1 / nbCat
                    subcatpercent = 100 * j / nbSubCat
                    subcat1percent = 100 * 1 / nbSubCat
                    showpercent = 100 * k / nbShow
                    percent = catpercent + (cat1percent * (subcatpercent + (cat1percent * showpercent / 100)) / 100)
                    logger.logNotice('Updating catalog... %s' % (str(percent)+'%'))
                    logger.logNotice(str(percent)+'%')
                    control.infoDialog('Updating catalog... %s' % (str(percent)+'%'), heading=control.lang(50005), icon=control.addonIcon(), time=10000)
            j+=1
        i+=1
        
    return True
    
def getSiteMenu():
    logger.logInfo('called function')
    data = []
    
    html = callServiceApi(config.uri.get('base'), base_url = config.websiteUrl)
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
    logger.logInfo('called function')
    data = getSiteMenu()
    return data
    
def getSubCategories(categoryId):
    logger.logInfo('called function')
    data = []
    categoryData = getSiteMenu()
    for c in categoryData:
        if str(c['id']) == categoryId:
           data = c['subcat']
           break
    return data
    
def getMyListCategories():
    logger.logInfo('called function')
    url = config.uri.get('myList')
    html = callServiceApi(url, useCache=False)
    return extractListCategories(html)
    
def getMylistCategoryItems(id):
    logger.logInfo('called function')
    url = config.uri.get('myList')
    html = callServiceApi(url, useCache=False)
    return extractListCategoryItems(html, id)

def extractListCategoryItems(html, id):   
    logger.logInfo('called function')
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
    
    return sorted(data, key=lambda item: item['title'] if 'title' in item else item['name'], reverse=False)
    
def extractMyListShowData(url, html):
    logger.logInfo('called function')
    showId = re.compile('/([0-9]+)/', re.IGNORECASE).search(url).group(1)
    res = showDB.get(int(showId))
    if len(res) == 1:
        return res[0]
    else:
        showName = common.replaceHTMLCodes(common.parseDOM(html, "div", attrs = { 'class' : 'show-cover-thumb-title-mobile sub-category' })[0])
        image = common.parseDOM(html, "img", ret = 'src')[0]
        
        return {
            'type' : 'show',
            'ltype' : 'show',
            'id' : int(showId),
            'parentid' : -1,
            'parentname' : '',
            'name' : common.replaceHTMLCodes(showName),
            'logo' : image,
            'image' : image,
            'fanart' : image,
            'banner' : image,
            'description' : '',
            'shortdescription' : '',
            'year' : '',
            'fanart' : image
            }

def extracMyListEpisodeData(url, html):
    logger.logInfo('called function')
    episodeId = re.compile('/([0-9]+)/', re.IGNORECASE).search(url).group(1)
    res = episodeDB.get(int(episodeId))
    if len(res) == 1:
        return res[0]
    else:
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
            
        try:
            datePublished = datetime.datetime.strptime(episodeName, '%b %d, %Y')
        except TypeError:
            datePublished = datetime.datetime(*(time.strptime(episodeName, '%b %d, %Y')[0:6]))
        
        return {
            'id' : int(episodeId), 
            'parentid' : -1,
            'parentname' : '',
            'title' : common.replaceHTMLCodes('%s - %s' % (showName, episodeName)), 
            'show' : showName, 
            'image' : image, 
            'episodenumber' : episodeNumber,
            'url' : url, 
            'description' : '',
            'shortdescription' : '',
            'dateaired' : episodeName,
            'date' : datePublished.strftime('%Y-%m-%d'),
            'year' : year,
            'fanart' : image,
            'ltype' : 'episode',
            'type' : 'episode'
            }
    
def extractListCategories(html):
    logger.logInfo('called function')
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
    
def getWebsiteHomeHtml(forceUpdate=False):
    logger.logInfo('called function')
    html = ''
    key = 'homeHTML'
    if forceUpdate:
        cache.shortCache.delete(key)
    if cache.shortCache.get(key) == '':
        html = callServiceApi(config.uri.get('home'), base_url = config.websiteUrl, useCache=False)
        cache.shortCache.set(key, repr(html))
    else:
        html = cache.shortCache.get(key).replace('\\\'', '\'')
    return html

def getWebsiteHomeSections():   
    data = []
    html = getWebsiteHomeHtml(True)
    sections = common.parseDOM(html, "div", attrs = { 'class' : 'main-container-xl main-container-xl-mobile' })
    i = 1
    for section in sections:
        header = common.parseDOM(section, "a", attrs = { 'class' : 'h2 heading-slider first' })
        if len(header):
            sectionName = common.stripTags(common.replaceHTMLCodes(header[0])).strip()
            exceptSections = [
                'CONTINUE WATCHING'
                ,'MY LIST'
                # ,'IWANT ORIGINALS - EXCLUSIVE FOR PREMIUM'
                ]
            if sectionName not in exceptSections:
                data.append({'id' : cache.generateHashKey(sectionName), 'name' : sectionName}) #, 'url' : '/', 'fanart' : ''})
        i += 1
    return data
    
def getWebsiteSectionContent(sectionId, page=1, itemsPerPage=8):
    logger.logInfo('called function')
    page -= 1
    data = []
    
    html = getWebsiteHomeHtml()
    sections = common.parseDOM(html, "div", attrs = { 'class' : 'main-container-xl main-container-xl-mobile' })
    for section in sections:
        header = common.parseDOM(section, "a", attrs = { 'class' : 'h2 heading-slider first' })
        if len(header):
            sectionName = common.stripTags(common.replaceHTMLCodes(header[0])).strip()
            if cache.generateHashKey(sectionName) == sectionId: break
    links = common.parseDOM(section, "a", attrs = { 'data-category' : 'CTA_Sections' }, ret = 'href')
    items = common.parseDOM(section, "a", attrs = { 'data-category' : 'CTA_Sections' })
    
    index = itemsPerPage * page
    containsShows = False
    i = 0
    for s in items:
        i += 1
        if i > index:
            url = links[i-1]

            if '/show/' in url:
                data.append(extractWebsiteSectionShowData(url, s))
                containsShows = True
            elif '/episode/' in url:
                data.append(extractWebsiteSectionEpisodeData(url, s))
                
        if i >= (index + itemsPerPage):
            break
   
    # episodeDB.get([d.get('id') for d in data])
    return removeDuplicates(sorted(data, key=lambda item: item['dateaired'] if item.get('type') == 'episode' else item['name'], reverse=True if containsShows == False else False))
    
def removeDuplicates(list):
    newList = []
    uniq = {}
    for d in list:
        key = '%s_%s'% (d.get('type'), str(d.get('id')))
        if key not in uniq: newList.append(d)
        uniq[key]=1
    return newList
    
def extractWebsiteSectionShowData(url, html):
    logger.logInfo('called function with param (%s)' % (url))
    
    showId = re.compile('/([0-9]+)/', re.IGNORECASE).search(url).group(1)
    filter = 'port-cover-thumb-title' if 'port-cover-thumb-title' in html else 'show-cover-thumb-title-mobile'
    showName = common.replaceHTMLCodes(common.parseDOM(html, "h3", attrs = { 'class' : filter })[0])
    image = common.parseDOM(html, "div", attrs = { 'class' : 'show-cover' }, ret = 'data-src')[0]
    
    res = showDB.get(int(showId))
    if len(res) == 1:
        return res[0]
    else:
        return {
            'type' : 'show',
            'ltype' : 'show',
            'id' : int(showId),
            'parentid' : -1,
            'parentname' : '',
            'name' : common.replaceHTMLCodes(showName),
            'logo' : image,
            'image' : image,
            'fanart' : image,
            'banner' : image,
            'url' : '',
            'description' : '',
            'shortdescription' : '',
            'year' : ''
            }

def extractWebsiteSectionEpisodeData(url, html):
    logger.logInfo('called function with param (%s, %s)' % (url, html))
    episodeId = re.compile('/([0-9]+)/', re.IGNORECASE).search(url).group(1)
    res = episodeDB.get(episodeId)
    if len(res) == 1:
        return res[0]
    else:
        showName = common.replaceHTMLCodes(common.parseDOM(html, "h3", attrs = { 'class' : 'show-cover-thumb-title-mobile' })[0])
        try:image = common.parseDOM(html, "div", attrs = { 'class' : 'show-cover' }, ret = 'data-src')[0]
        except:image = common.parseDOM(html, "div", attrs = { 'class' : 'show-cover lazy' }, ret = 'data-src')[0]
        dateAired = common.parseDOM(html, "h4", attrs = { 'class' : 'show-cover-thumb-aired-mobile' })
        
        year = ''
        episodeNumber = 0
        description = ''
        episodeName = ''
        
        if dateAired and len(dateAired) > 0:
            episodeName = dateAired[0]
            year = episodeName.split(', ')[1]

        try:
            datePublished = datetime.datetime.strptime(episodeName, '%b %d, %Y')
        except TypeError:
            datePublished = datetime.datetime(*(time.strptime(episodeName, '%b %d, %Y')[0:6]))
            
        return {
            'id' : int(episodeId), 
            'parentid' : -1,
            'parentname' : '',
            'title' : common.replaceHTMLCodes('%s - %s' % (showName, episodeName)), 
            'show' : showName, 
            'image' : image, 
            'episodenumber' : episodeNumber,
            'url' : url, 
            'description' : '',
            'shortdescription' : '',
            'dateaired' : episodeName,
            'date' : datePublished.strftime('%Y-%m-%d'),
            'year' : year,
            'fanart' : image,
            'ltype' : 'episode',
            'type' : 'episode'
            }

def getShows(subCategoryId, page = 1):
    logger.logInfo('called function with param (%s, %s)' % (subCategoryId, page))
    data = []
    subCategoryShows = []    
    
    html = callServiceApi(config.uri.get('categoryList') % subCategoryId)
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
                res = showDB.get(int(d['id']))
                if len(res) == 1:
                    show = res[0]
                    show['parentid'] = int(subCategoryId)
                    show['parentname'] = d['parentname']
                    show['year'] = d['year']
                    show['casts'] = castDB.getByShow(int(d['id']))
                    data.append(show)
                else:
                    data.append({
                        'id' : int(d['id']),
                        'name' : d['name'],
                        'parentid' : int(subCategoryId),
                        'parentname' : d['parentname'],
                        'logo' : d['image'].replace(' ', '%20'),
                        'image' : d['image'].replace(' ', '%20'),
                        'fanart' : d['image'].replace(' ', '%20'),
                        'banner' : d['image'].replace(' ', '%20'),
                        'url' : d['url'],
                        'description' : d['description'],
                        'shortdescription' : d['shortdescription'],
                        'year' : d['year'],
                        'type' : 'show',
                        'ltype' : 'show'
                        })
                
    return data
    
def extractShows(html):
    logger.logInfo('called function')
    data = []
    list = common.parseDOM(html, "ul", attrs = { 'id' : 'og-grid' })[0]
    shows = common.parseDOM(list, "li", attrs = { 'class' : 'og-grid-item-o' })
    dateaired = common.parseDOM(list, "li", attrs = { 'class' : 'og-grid-item-o' }, ret = 'data-aired')
    i = 0
    for show in shows:
        name = common.parseDOM(show, "h2")[0]
        aired = common.parseDOM(show, "h3")[0]
        image = common.parseDOM(show, "img", ret = 'src')[0]
        url = common.parseDOM(show, "a", ret = 'href')[0]
        id = re.compile('/([0-9]+)/').search(url).group(1)
        year = ''
        try: year = re.compile('^([0-9]{4})').search(dateaired[i]).group(1)
        except:
            try: year = aired.replace('AIRED: ', '').split(' ')[1]
            except: pass
        
        data.append({
            'id' : id,
            'parentid' : -1,
            'parentname' : '',
            'name' : common.replaceHTMLCodes(name),
            'url' : url,
            'image' : image,
            'description' : '',
            'shortdescription' : '',
            'dateairedstr' : aired.replace('AIRED: ', ''),
            'year' : year
            })
        i+=1    
    return data

def getShow(showId, parentId=-1, year=''):
    logger.logInfo('called function with param (%s, %s, %s)' % (showId, str(parentId), year))
    data = {}
    
    html = callServiceApi(config.uri.get('showDetails') % showId, useCache=False)
    err = checkIfError(html)
    if err.get('error') == False:
    
        res = showDB.get(int(showId))
        show = res[0] if len(res) == 1 else {}
        showData = json.loads(re.compile('var ldj = (\{.+\})', re.IGNORECASE).search(html).group(1))

        rating = showData.get('aggregateRating' , {}).get('ratingValue', show.get('rating', 0))
        if rating == None: rating = 0
        votes = showData.get('aggregateRating' , {}).get('reviewCount', show.get('votes', 0))
        if votes == None: votes = 0

        if year == '':
            try:
                datePublished = datetime.datetime.strptime(showData.get('datePublished'), '%Y-%m-%d')
            except TypeError:
                datePublished = datetime.datetime(*(time.strptime(showData.get('datePublished'), '%Y-%m-%d')[0:6]))
            year = datePublished.strftime('%Y')

        if parentId == -1: parentId = show.get('parentid', parentId)
        if year == '': year = show.get('year', year)
        
        images = common.parseDOM(html, "div", attrs = { 'class' : 'hero-image-logo' })
        t = common.parseDOM(html, "link", attrs = { 'rel' : 'image_src' }, ret = 'href')
        image = t[0] if len(t) > 0 else ''
        if len(images) == 0:
            logo = image
        else:
            logo = common.parseDOM(images, "img", ret = "src")[0]
            
        url = common.parseDOM(html, "link", attrs = { 'rel' : 'canonical' }, ret = 'href')[0]
        
        fanarts = common.parseDOM(html, "div", attrs = { 'class' : 'header-hero-image topic-page' }, ret = 'style')
        if len(fanarts) == 0:
            fanarts = common.parseDOM(html, "div", attrs = { 'class' : 'header-hero-image' }, ret = 'style')
        if len(fanarts) == 0:
            fanarts = common.parseDOM(html, "div", attrs = { 'id' : 'detail-video' }, ret = 'style')
        if fanarts:
            fanart = re.compile('url\((.+)\);', re.IGNORECASE).search(fanarts[0]).group(1)
        else:
            fanart = image

        banner = showData.get('image', fanart)
            
        name = common.parseDOM(html, "meta", attrs = { 'property' : 'og:title' }, ret = "content")[0]
        description = common.parseDOM(html, "div", attrs = { 'class' : 'celeb-desc-p' })[0]
        genres = common.parseDOM(html, "a", attrs = { 'class' : 'text-primary genre-deets' })
        genre = '' if len(genres) == 0 else genres[0]
        
        actors = []
        casts = common.parseDOM(html, "casts")
        i = 1
        for cast in casts:
            castId = common.parseDOM(cast, "cast-name", ret = "data-id")[0]
            castName = common.stripTags(cast)
            castUrl = config.websiteUrl + common.parseDOM(cast, "a", ret = "href")[0]
            castImage = common.parseDOM(cast, "img", ret = "src")[0]
            actors.append({'castid': int(castId), 'showid': int(showId), 'name': castName, 'role': '', 'thumbnail': castImage, 'order': i, 'url': castUrl})
            castDB.set(actors)
            i+=1
        
        # Check episode list
        episodes = {}
        nbEpisodes = 0
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

            nbEpisodes = int(re.compile('\(([0-9]+)\)', re.IGNORECASE).search(common.parseDOM(html, "h2", attrs = { 'class' : 'episode-list-showp' })[0]).group(1))
        
        type = 'show' if showData.get('@type' ,'show').lower() not in ('show','movie') else showData.get('@type' ,'show').lower()
        data = {
            'id' : int(showId),
            'name' : common.replaceHTMLCodes(name),
            'parentid' : int(parentId),
            'parentname' : common.replaceHTMLCodes(genre),
            'logo' : logo,
            'image' : image,
            'fanart' : fanart,
            'banner' : banner,
            'url' : url,
            'description' : common.replaceHTMLCodes(description),
            'shortdescription' : common.replaceHTMLCodes(description),
            'year' : year,
            'nbEpisodes' : nbEpisodes,
            'episodes' : episodes,
            'casts' : actors,
            'ltype' : type,
            'duration' : 0,
            'views' : 0,
            'rating' : rating,
            'votes' : votes,
            'type': 'show'
            }
        if type == 'movie':
            duration = re.compile('^([0-9]+)h([0-9]*)[m]?|([0-9]+)m$', re.IGNORECASE).search(showData.get('duration', showData.get('timeRequired', 0)))
            if duration: 
                if duration.group(1) != None: 
                    if duration.group(2) != '': data['duration'] = int(duration.group(2))
                    data['duration'] += int(duration.group(1)) * 60
                if duration.group(3) != None: 
                    data['duration'] = int(duration.group(3))
        showDB.set(data)
    else:
        logger.logWarning('Error on show %s: %s' % (showId, err.get('message')))
    return data

def getEpisodesPerPage(showId, parentId, year, page=1, itemsPerPage=8):
    logger.logInfo('called function with param (%s, %s, %s, %s, %s)' % (showId, parentId, year, page, itemsPerPage))
    data = []
    
    # max nb items per page that TFC website can provide
    websiteNbItemsPerPage = 8
    # Calculating page index and needed pages to request for building next page to display
    firstPage = 1 if page == 1 else ((itemsPerPage / websiteNbItemsPerPage) * (page - 1) + 1)
    lastPage = itemsPerPage / websiteNbItemsPerPage * page
    hasNextPage = False
    
    paginationURL = config.uri.get('episodePagination')
    # showDetails = cache.sCacheFunction(getShow, showId)
    showDetails = getShow(showId, parentId, year)
    if showDetails:
        for page in range(firstPage, lastPage+1, 1):
            # reseting value
            hasNextPage = False

            calculatedPage = page 
            if control.setting('reversePagination') == 'true' and showDetails.get('nbEpisodes') != 0:
                import math
                logger.logInfo(page)
                logger.logInfo('%s / %s' % (showDetails.get('nbEpisodes'), websiteNbItemsPerPage))
                calculatedPage = int(math.ceil(logger.logInfo(showDetails.get('nbEpisodes') / float(websiteNbItemsPerPage))) - (page - 1))
                logger.logInfo(calculatedPage)
                if calculatedPage > 1: hasNextPage = True
                logger.logInfo(hasNextPage)
                if calculatedPage < 1: break

            html = callServiceApi(paginationURL % (showId, calculatedPage), useCache=False if page == 1 else True)
        
            # if page does not exist
            if page > 1 and html == '':
                break
            # if no pagination, it's a movie or special
            elif page == 1 and html == '':
                html = callServiceApi(config.uri.get('showDetails') % showId, useCache=False)
                episodeId = int(re.compile('var dfp_e = "(.+)";', re.IGNORECASE).search(html).group(1))
                episodeData = json.loads(re.compile('var ldj = (\{.+\})', re.IGNORECASE).search(html).group(1))

                res = episodeDB.get(episodeId)
                if len(res) == 1:
                    e = res[0]
                    # Update title value with episode number
                    if episodeData:
                        e['title'] = episodeData.get('name')
                        e['episodenumber'] = episodeData.get('episodenumber')
                        e['showObj'] = showDetails
                    data.append(e)
                else:
                    try:
                        datePublished = datetime.datetime.strptime(episodeData.get('datePublished'), '%Y-%m-%d')
                    except TypeError:
                        datePublished = datetime.datetime(*(time.strptime(episodeData.get('datePublished'), '%Y-%m-%d')[0:6]))
            
                    type = 'episode' if episodeData.get('@type' ,'episode').lower() not in ('episode','movie') else episodeData.get('@type' ,'episode').lower()
                    edata = {
                        'id' : episodeId,
                        'title' : episodeData.get('name'),
                        'show' : showDetails.get('name', episodeData.get('name')),
                        'image' : episodeData.get('thumbnailUrl',  episodeData.get('image')),
                        'episodenumber' : 1,
                        'description' : episodeData.get('description'),
                        'shortdescription' : episodeData.get('description'),
                        'dateaired' : datePublished.strftime('%b %d, %Y'),
                        'date' : datePublished.strftime('%Y-%m-%d'),
                        'year' : datePublished.strftime('%Y'),
                        'fanart' : showDetails.get('fanart'),
                        'showObj' : showDetails,
                        'ltype' : type,
                        'duration' : 0,
                        'views' : 0,
                        'rating' : episodeData.get('aggregateRating' , {}).get('ratingValue', 0),
                        'votes' : episodeData.get('aggregateRating' , {}).get('reviewCount', 0),
                        'type' : 'episode'
                        }
                    if edata['rating'] == None: edata['rating'] = 0
                    if edata['votes'] == None: edata['votes'] = 0
                    duration = re.compile('^([0-9]+)h([0-9]*)[m]?|([0-9]+)m$', re.IGNORECASE).search(episodeData.get('duration', episodeData.get('timeRequired', 0)))
                    if duration: 
                        if duration.group(1) != None: 
                            if duration.group(2) != '': edata['duration'] = int(duration.group(2))
                            edata['duration'] += int(duration.group(1)) * 60
                        elif duration.group(3) != None: 
                            edata['duration'] = int(duration.group(3))
                    data.append(edata)
                break
            else:
                i = 0
                episodes = common.parseDOM(html, 'li', attrs = {'class' : 'og-grid-item'})
                if len(episodes) > 0:
                
                    descriptions = common.parseDOM(html, 'li', attrs = {'class' : 'og-grid-item'}, ret = 'data-show-description')
                    titles = common.parseDOM(html, 'li', attrs = {'class' : 'og-grid-item'}, ret = 'data-aired')
                        
                    for e in episodes:
                        url = common.parseDOM(e, "a", ret = 'href')[0]
                        episodeId = int(re.compile('/([0-9]+)/', re.IGNORECASE).search(url).group(1))
                        episodeData = showDetails.get('episodes').get(episodeId)
                        res = episodeDB.get(episodeId)
                        if len(res) == 1:
                            e = res[0]
                            # Update title value with episode number
                            if episodeData:
                                e['title'] = episodeData.get('title')
                                e['episodenumber'] = episodeData.get('episodenumber')
                                e['showObj'] = showDetails
                            data.append(e)
                        else:
                            image = common.parseDOM(e, "div", attrs = {'class' : 'show-cover'}, ret = 'data-src')[0]
                            title = common.replaceHTMLCodes(titles[i])
                            dateAired = title
                            showTitle = showDetails.get('name')
                            fanart = showDetails.get('fanart')
                            year = title.split(', ').pop()
                            description = common.replaceHTMLCodes(descriptions[i])
                            shortDescription = description
                            episodeNumber = 0
                            
                            if episodeData:
                                title = episodeData.get('title')
                                episodeNumber = episodeData.get('episodenumber')
                            
                            try:
                                datePublished = datetime.datetime.strptime(dateAired, '%b %d, %Y')
                            except TypeError:
                                datePublished = datetime.datetime(*(time.strptime(dateAired, '%b %d, %Y')[0:6]))
                            
                            e = {
                                'id' : episodeId,
                                'title' : title,
                                'parentid' : int(showId),
                                'show' : showTitle,
                                'image' : image,
                                'fanart' : fanart,
                                'episodenumber' : episodeNumber,
                                'url' : image,
                                'description' : description,
                                'shortdescription' : shortDescription,
                                'dateaired' : dateAired,
                                'date' : datePublished.strftime('%Y-%m-%d'),
                                'year' : year,
                                'parentalAdvisory' : '',
                                'showObj' : showDetails,
                                'ltype' : showDetails.get('ltype'),
                                'type' : 'episode'
                                }
                            episodeDB.set(e)
                            data.append(e)
                            
                        i += 1
                else: 
                    break
    # return sorted(data, key=lambda episode: episode['title'], reverse=True)
    return (data, hasNextPage)
      
# def getShowEpisodes(showId):
    # data = {}
    # showData = cache.sCacheFunction(getShow, showId)
    # showEpisodes = callJsonApi(config.uri.get('showEpisodes') % showId)
    # if showData and showEpisodes:
        # for e in showEpisodes:
            # e['show'] = showData.get('name')
            # e['showimage'] = showData.get('image').replace(' ', '%20')
            # e['fanart'] = showData.get('banner').replace(' ', '%20')
            # e['image'] = e.get('ImageList')
            # e['description'] = e.get('Synopsis')
            # e['shortdescription'] = e.get('Description')
            # e['episodenumber'] = e.get('EpisodeNumber')
            # e['dateaired'] = e.get('DateAired').split('T')[0]
            # data[e.get('EpisodeId')] = e
    # return data
          
def getEpisode(episodeId):
    logger.logInfo('called function with param (%s)' % episodeId)
    data = {}
    
    html = callServiceApi(config.uri.get('episodeDetails') % episodeId, base_url = config.websiteUrl, useCache=False)
    err = checkIfError(html)
    if err.get('error') == False:
        url = common.parseDOM(html, "link", attrs = { 'rel' : 'canonical' }, ret = 'href')[0] 
        episodeData = json.loads(re.compile('var ldj = (\{.+\})', re.IGNORECASE).search(html).group(1))
        showId = re.compile('media/fetch.+sid: (\d+),', re.IGNORECASE).search(html).group(1)
        res = showDB.get(showId)
        show = res[0] if len(res) == 1 else {}
        parentalAdvisory = 'true' if re.compile('var dfp_c = ".*2900.*";', re.IGNORECASE).search(html) else 'false'
        plot = episodeData.get('description')
        showName = show.get('name', episodeData.get('name'))
        thumbnail = episodeData.get('thumbnailUrl')
        fanart = show.get('fanart', episodeData.get('image'))
        type = 'episode' if episodeData.get('@type' ,'episode').lower() not in ('episode','movie') else episodeData.get('@type' ,'episode').lower()
        try:
            datePublished = datetime.datetime.strptime(episodeData.get('datePublished'), '%Y-%m-%d')
        except TypeError:
            datePublished = datetime.datetime(*(time.strptime(episodeData.get('datePublished'), '%Y-%m-%d')[0:6]))
        dateAired = datePublished.strftime('%b %d, %Y')
        year = datePublished.strftime('%Y')
        episodeNumber = 1 if type == 'movie' else episodeData.get('episodeNumber')
                
        data = {
            'id' : int(episodeId),
            'title' : 'Ep. %s - %s' %(episodeNumber, dateAired),
            'parentid' : showId,
            'show' : showName,
            'image' : thumbnail,
            'fanart' : fanart,
            'episodenumber' : episodeNumber,
            'url' : url,
            'description' : plot,
            'shortdescription' : plot,
            'dateaired' : dateAired,
            'date' : datePublished.strftime('%Y-%m-%d'),
            'year' : year,
            'parentalAdvisory' : parentalAdvisory,
            'ltype' : type,
            'type' : 'episode'
            }
                
    return data
    
# def getEpisodeVideo(episodeId):
    # data = {}
    # url = '/Media?episodeId=%s&isPv=false'
    # res = callJsonApi(url % episodeId, useCache = False)
    # if res and 'statusCode' in res:
        # data = res
        # data['errorCode'] = 1 if res['statusCode'] == 0 else 0
            
    # return data
    
def getUserInfo():
    logger.logInfo('called function')
    url = config.uri.get('profile')
    html = callServiceApi(url, useCache = False)
    
    # Retrieve info from website
    profileHeader = common.parseDOM(html, 'div', attrs = {'class' : 'profile_header'})
    name = common.parseDOM(profileHeader, 'div', attrs = {'class' : 'name'})[0]
    state = common.parseDOM(profileHeader, 'div', attrs = {'class' : 'name'})[0]
    memberSince = common.parseDOM(profileHeader, 'div', attrs = {'class' : 'date'})[0]    
    
    # Retrieve info from account JSON string
    user = json.loads(control.setting('accountJSON')).get('profile')
    
    return {
        'name' : name,
        'firstName' : user.get('firstName', ''),
        'lastName' : user.get('lastName', ''),
        'email' : user.get('email', ''),
        'state' : state,
        'country' : user.get('country', ''),
        'memberSince' : memberSince.replace('MEMBER SINCE ', '')
    }
    
def getUserSubscription():
    logger.logInfo('called function')
    url = config.uri.get('profileDetails')
    subscription = callJsonApi(url, useCache=False)
    logger.logInfo(subscription)
    first_cap_re = re.compile('(.)([A-Z][a-z]+)')
        
    subKeys = ['Type', 'SubscriptionName', 'SubscriptionStatus', 'ActivationDate', 'ExpirationDate', 'BillingPeriod', 'AutoRenewal']
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
            'details' : details
        }
    
def getUserTransactions():
    logger.logInfo('called function')
    TAG_HTML = re.compile('<[^>]+>')

    data = []
    url = config.uri.get('profile')
    html = callServiceApi(url, useCache = False)
    
    transactionsHtml = common.parseDOM(html, 'div', attrs = {'id' : 'transactions'})
    transactions = common.parseDOM(common.parseDOM(transactionsHtml, 'tbody'), 'tr')
    
    header = []
    headers = common.parseDOM(common.parseDOM(transactionsHtml, 'thead'), 'th')
    for h in headers:
        header.append(h)
    
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
                value = c
            t += "%s: %s\n" % (header[i], value)
            i+=1
        data.append(t)
                
    return data
    
def addToMyList(id, name, ltype, type):
    logger.logInfo('called function with param (%s, %s, %s, %s)' % (id, name, ltype, type))
    url = config.uri.get('addToList')
    logger.logDebug(url)
    res = {}
    if type == 'show':
        res = logger.logNotice(callJsonApi(url, params = {'CategoryId': id, 'type': ltype}, useCache=False))
    else:
        episodes = episodeDB.get(id)
        e = episodes[0] if len(episodes) == 1 else getEpisode(id)
        if 'parentid' in e:
            res = logger.logNotice(callJsonApi(url, params = {'CategoryId': e.get('parentid'), 'EpisodeId': id, 'type': ltype}, useCache=False))                    
    if 'StatusMessage' in res:
        control.showNotification(res.get('StatusMessage'), name)
    else:
        control.showNotification(control.lang(57026))

def removeFromMyList(id, name, ltype, type):
    logger.logInfo('called function with param (%s, %s, %s, %s)' % (id, name, ltype, type))
    url = config.uri.get('removeFromList')
    logger.logDebug(url)
    res = {}
    if type == 'show':
        res = logger.logNotice(callJsonApi(url, params = {'CategoryId': id, 'type': ltype}, useCache=False))
    else:
        episodes = episodeDB.get(id)
        e = episodes[0] if len(episodes) == 1 else getEpisode(id)
        if 'parentid' in e:
            res = logger.logNotice(callJsonApi(url, params = {'CategoryId': e.get('parentid'), 'EpisodeId': id, 'type': ltype}, useCache=False))
    if 'StatusMessage' in res:
        control.showNotification(res.get('StatusMessage'), name)
        control.refresh()
    else:
        control.showNotification(control.lang(57026))
    
def showExportedShowsToLibrary():
    data = []
    temp = {}
    exported = libraryDB.getAll()
    for d in exported:
        if 'id' in d:
            temp[d.get('id')] = d
    if len(temp) > 0:
        shows = showDB.get(temp.keys())
        for s in shows:
            temp[s.get('id')].update(s)
            data.append(temp.get(s.get('id')))
    return data

def removeFromLibrary(id, name):
    data = libraryDB.get(int(id))
    if len(data) > 0:
        if logger.logInfo(libraryDB.delete(data[0])):
            path = os.path.join(control.showsLibPath, name, '')
            logger.logInfo(path)
            if logger.logInfo(control.pathExists(path)): 
                if control.confirm(control.lang(57041), line1=control.lang(57042), title=name) == False:
                    control.deleteFolder(path, True)
            control.showNotification(control.lang(57043) % name, control.lang(50010))
        else:
            control.showNotification(control.lang(57044), control.lang(50004))
    else:
        control.showNotification(control.lang(57045), control.lang(50001))


def addToLibrary(id, name, parentId=-1, year='', updateOnly=False):
    logger.logInfo('called function with param (%s, %s, %s, %s)' % (id, name, parentId, year))
    from resources.lib.indexers import navigator
    status = True
    updated = False
    nbUpdated = 0
    episodes = getEpisodesPerPage(id, parentId, year, page=1, itemsPerPage=8)
    
    if len(episodes) > 0:
    
        path = os.path.join(control.showsLibPath, name)
        control.makePath(path)
        
        # Show NFO file
        try: 
            e = episodes[0]
            show = e.get('showObj')
            res = libraryDB.get(show.get('id'))
            lib = res[0] if len(res) == 1 else {}
            control.writeFile(logger.logNotice(os.path.join(path, 'tvshow.nfo')), generateShowNFO(show, path).encode('utf-8'))
        except Exception as err:
            logger.logError(err)
            status = False
        
        if status == True:
            
            mostRecentDate = lastDate = lib.get('date', datetime.datetime(1900, 1, 1))
            lastCheck = lib.get('lastCheck', datetime.datetime(1900, 1, 1))
            logger.logNotice('last check date : %s' % lastCheck.strftime('%Y-%m-%d %H:%M:%S'))
            for e in sorted(episodes, key=lambda item: item['date'], reverse=False):
                filePath = os.path.join(path, '%s.strm' % e.get('title'))

                logger.logNotice('episode date : %s' % e.get('date'))
                try:
                    episodeDate = datetime.datetime.strptime(e.get('date'), '%Y-%m-%d')
                except TypeError:
                    episodeDate = datetime.datetime(*(time.strptime(e.get('date'), '%Y-%m-%d')[0:6]))
                
                if lastDate.date() < episodeDate.date():
                    updated = True
                    nbUpdated += 1
                    if mostRecentDate.date() < episodeDate.date(): mostRecentDate = episodeDate
                    
                if not updateOnly or updated:
                    try:
                        # Episode STRM / NFO files
                        control.writeFile(logger.logNotice(os.path.join(path, '%s.nfo' % e.get('title'))), generateEpisodeNFO(e, path, filePath).encode('utf-8'))
                        control.writeFile(logger.logNotice(filePath), navigator.navigator().generateActionUrl(str(e.get('id')), config.PLAY, '%s - %s' % (e.get('show'), e.get('dateaired')), e.get('image')))
                    except Exception as err:
                        logger.logError(err)
                        status = False
                        break
    else: 
        status = False
            
    if status == True: 
        if not updateOnly: control.showNotification(control.lang(57034) % name, control.lang(50010))
        libraryDB.set({'id' : int(show.get('id')), 
            'name' : show.get('name'), 
            'parentid' : int(show.get('parentid')),
            'year' : show.get('year'),
            'date' : mostRecentDate.strftime('%Y-%m-%d')
            })
    else: 
        if not updateOnly: control.showNotification(control.lang(57033), control.lang(50004))
    return {'status': status, 'updated': updated, 'nb': nbUpdated}

def generateShowNFO(info, path):
    logger.logInfo('called function')
    nfoString = ''
    nfoString += '<title>%s</title>' % info.get('name')
    nfoString += '<sorttitle>%s</sorttitle>' % info.get('name')
    nfoString += '<episode>%s</episode>' % max([e.get('episodenumber') for k, e in info.get('episodes').iteritems()])
    nfoString += '<plot>%s</plot>' % info.get('description')
    nfoString += '<aired>%s</aired>' % info.get('dateaired')
    nfoString += '<year>%s</year>' % info.get('year')
    nfoString += '<thumb aspect="poster">%s</thumb>' % info.get('image')
    nfoString += '<fanart url=""><thumb dim="1280x720" colors="" preview="%s">%s</thumb></fanart>' % (info.get('fanart'), info.get('fanart'))
    nfoString += '<genre>%s</genre>' % info.get('parentname')
    nfoString += '<path>%s</path>' % path
    nfoString += '<filenameandpath></filenameandpath>'
    nfoString += '<basepath>%s</basepath>' % path
    for c in info.get('casts', []):
        nfoString += '<actor><name>%s</name><order>%d</order><thumb>%s</thumb></actor>' % (c.get('name'), c.get('order'), c.get('thumbnail'))
    
    return u'<?xml version="1.0" encoding="UTF-8" standalone="yes"?> \
<!-- created on %s - by TFC.tv addon --> \
<tvshow> \
    %s \
</tvshow>' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), nfoString)
    
def generateEpisodeNFO(info, path, filePath):
    logger.logInfo('called function')
    nfoString = ''
    nfoString += '<title>%s</title>' % info.get('title')
    nfoString += '<showtitle>%s</showtitle>' % info.get('show')
    nfoString += '<sorttitle>%s</sorttitle>' % info.get('dateaired')
    nfoString += '<episode>%s</episode>' % info.get('episodenumber')
    nfoString += '<plot>%s</plot>' % info.get('description')
    nfoString += '<aired>%s</aired>' % info.get('dateaired')
    nfoString += '<year>%s</year>' % info.get('year')
    nfoString += '<thumb>%s</thumb>' % info.get('image')
    nfoString += '<art><banner>%s</banner><fanart>%s</fanart></art>' % (info.get('fanart'), info.get('fanart'))
    nfoString += '<path>%s</path>' % path
    nfoString += '<filenameandpath>%s</filenameandpath>' % filePath
    nfoString += '<basepath>%s</basepath>' % filePath
    nfoString += '<studio>ABS-CBN</studio>'
    
    return u'<?xml version="1.0" encoding="UTF-8" standalone="yes"?> \
<!-- created on %s - by TFC.tv addon --> \
<episodedetails> \
    %s \
</episodedetails>' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), nfoString)

def checkLibraryUpdates():
    logger.logInfo('called function')
    items = libraryDB.getAll()
    for show in items:
        logger.logNotice('check for update for show %s' % show.get('name'))
        result = addToLibrary(show.get('id'), show.get('name'), show.get('parentid'), show.get('year'), updateOnly=True)
        if result.get('updated') == True:
            logger.logNotice('Updated %s episodes' % str(result.get('nb')))
            control.showNotification(control.lang(57037) % (str(result.get('nb')), show.get('name')), control.lang(50011))
        else:
            logger.logNotice('No updates for show %s' % show.get('name'))
    return True
    
def enterSearch(category, type):
    logger.logInfo('called function with params (%s, %s)' % (category, type))
    data = []
    search = control.inputText(control.lang(50204)).strip()
    if len(search) >= 3:
        if category == 'movieshow':
            if type == 'title':
                data = showDB.searchByTitle(search)
            elif type == 'category':
                data = showDB.searchByCategory(search)
            elif type == 'year':
                data = showDB.searchByYear(search)
            elif type == 'cast':
                cast = castDB.searchByActorName(search)
                data = showDB.get([c.get('showid') for c in cast])
        elif category == 'episode':
            if type == 'title':
                data = episodeDB.searchByTitle(search)
            elif type == 'date':
                data = episodeDB.searchByDate(search)
    else:
        control.showNotification(control.lang(57046), control.lang(50001))
    return data

def enterCredentials():
    logger.logInfo('called function')
    email = control.inputText(control.lang(50400), control.setting('emailAddress'))
    password = ''
    i = 1
    while i < 3 and password == '':
        password = control.inputPassword(control.lang(50401))
        i+=1
    logger.logNotice('%s - %s' % (email, password))
    control.setSetting('emailAddress', email)
    control.setSetting('password', password)
    return login()
    
def checkAccountChange(forceSignIn=False):
    logger.logInfo('called function')
    email = control.setting('emailAddress')
    password = control.setting('password')
    hash = hashlib.sha1(email + password).hexdigest()
    hashFile = os.path.join(control.dataPath, 'a.tmp')
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
        logger.logInfo('Not logged in')
        logged = True
    
    if logged:
        cleanCookies(False)
        loginSuccess = login()
        if loginSuccess == True and os.path.exists(control.dataPath):
            with open(hashFile, 'w') as f:
                f.write(hash)
                f.close()
        elif os.path.exists(hashFile)==True: 
            os.unlink(hashFile)
        
    return (accountChanged, loginSuccess)
    
def login(quiet=False):
    logger.logInfo('called function')
    signedIntoWebsite = loginToWebsite(quiet)
    return signedIntoWebsite
    
def isLoggedIn():
    logger.logInfo('called function')
    global Logged
    if Logged == False:
        html = callServiceApi(config.uri.get('profile'), headers=[('Referer', config.websiteSecuredUrl+'/')], base_url=config.websiteSecuredUrl, useCache=False)
        Logged = False if 'TfcTvId' not in html else True
    return Logged
    
def loginToWebsite(quiet=False): 
    from random import randint
    import time
    global cookieJar
    
    logged = False
    
    if quiet == False:
        control.showNotification(control.lang(57019), control.lang(50005))
    
    emailAddress = control.setting('emailAddress')
    password = control.setting('password')
    authData = {
            "siteURL": config.websiteUrl,
            "loginID": emailAddress,
            "password": password,
            "keepMeLogin": False
        }
    
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
        base_url = config.kapamilyaAccountsSSOUrl, 
        useCache = False
    )

    # retrieve ocpKey
    signin = callServiceApi(
        config.uri.get('signin'),
        base_url = config.kapamilyaAccountsSSOUrl, 
        useCache = False
    )
    ocpKey = common.parseDOM(signin, "sso-accounts", ret = 'api-key')[0]

    # Retrieve apiKey
    data = callJsonApi(config.uri.get('apiKey') % ocpKey, base_url=config.apiSSOUrl, useCache = False, jsonData=True)
    if (not data or ('apiKey' not in data)):
        control.showNotification(control.lang(57024), control.lang(50006))
    else:
    
        gigyaUrl = ''
        gigyaBuild = ''
        gigyaVersion = ''
        gigyaJSON = {}
        ssoKey = ''
        loginToken = ''
        UID = ''
        UIDSignature = ''
        
        apikey = data.get('apiKey', '')
        if apikey == '': apikey = getFromCookieByName('app_apikey').value
        
        # Retrieve Gigya version and build
        params = {'apikey' : apikey, '_': time.time()}
        gigyaHtml = callServiceApi(
            config.uri.get('gigyaJS') + '?' + urllib.urlencode(params), 
            base_url = config.gigyaCDNUrl, 
            useCache = False
        )
        gigyaVersion = re.compile('"version":?"(.+)",').search(gigyaHtml).group(1)
        gigyaBuild = re.compile('"number":([\d.]+),').search(gigyaHtml).group(1)
        
        # Retrieve Gigya ssoKey
        params = {'apiKey' : apikey, 'version': gigyaVersion}
        webSdkURI = config.uri.get('webSdkApi') + '?' + urllib.urlencode(params)
        gigyaHtml = callServiceApi(
            webSdkURI, 
            base_url = config.gigyaCDNUrl, 
            useCache = False
        )
        defaultApiDomain = re.compile('gigya.defaultApiDomain=\'([a-zA-Z.]+)\';').search(gigyaHtml).group(1)
        dataCenter = re.compile('gigya.dataCenter=\'([a-zA-Z0-9.]+)\';').search(gigyaHtml).group(1)
        ssoKey = re.compile('"ssoKey":"([a-zA-Z0-9_-]+)",').search(gigyaHtml).group(1)       
        apiDomainCookie = 'apiDomain_' + ssoKey + '=' + dataCenter + '.' + defaultApiDomain
        apiDomain = dataCenter + '.' + defaultApiDomain
        
        # Retrieve needed cookies
        params = {
            'apiKey' : apikey, 
            'pageURL' : config.kapamilyaAccountsSSOUrl + config.uri.get('signin'), 
            'format': 'json', 
            'context' : 'R' + str(randint(10000, 99999)**2)
            }
        callServiceApi(
            config.uri.get('webSdkBootstrap') + '?' + urllib.urlencode(params),
            headers = [
                ('Cookie', apiDomainCookie),
                ('Referer', config.gigyaCDNUrl + webSdkURI)
                ], 
            base_url = config.gigyaAccountUrl, 
            useCache = False
            )

        params = {
            'APIKey' : ssoKey, 
            'ssoSegment' : '', 
            'version': gigyaVersion, 
            'build' : gigyaBuild
            }
        sso = callServiceApi(
            config.uri.get('gigyaSSO') + '?' + urllib.urlencode(params),
            base_url= config.gigyaSocializeUrl, 
            useCache = False
            )
        
        cookie = getCookieContent(['hasGmid', 'gmid', 'ucid'])   
        cookie.append(apiDomainCookie)

        # Login        
        login = callJsonApi(
            config.uri.get('ssoLogin'),
            params = authData,
            headers = [
                ('Ocp-Apim-Subscription-Key', ocpKey),
                ('Origin', config.kapamilyaAccountsSSOUrl),
                ('Referer', config.kapamilyaAccountsSSOUrl + config.uri.get('signin')),
                ('SSO-Native-Origin', config.kapamilyaAccountsSSOUrl),
                ('Verification-Mode', 'LINK')
                ], 
            base_url = config.apiAzureUrl, 
            useCache = False,
            jsonData = True
            )
        if (not login or ('data' not in login and login.get('statusCode') != 203200)) and quiet == False:
            if 'message' in login:
                control.showNotification(login.get('message'), control.lang(50006))
            else:
                control.showNotification(control.lang(57024), control.lang(50006))
        else:
            # Retrieve authorization code from cookie
            sessionInfo = login.get('data').get('sessionInfo')
            gacCookie = sessionInfo.get('cookieName')
            gacToken = sessionInfo.get('cookieValue')
        
            # Retrieve the login token
            params = {
                'sessionExpiration' : -2, 
                'authCode' : gacToken, 
                'APIKey': apikey, 
                'sdk' : 'js_' + gigyaVersion,
                'authMode' : 'cookie',
                'pageURL' : config.kapamilyaAccountsSSOUrl + config.uri.get('welcome'),
                'format' : 'json',
                'context' : 'R' + str(randint(10000, 99999)**2)
                }
            gigyaJSON = callJsonApi(
                config.uri.get('gigyaNotifyLogin') + '?' + urllib.urlencode(params),
                headers = [
                    ('Cookie', '; '.join(cookie)),
                    ('Referer', config.gigyaCDNUrl + webSdkURI)
                    ], 
                base_url= config.gigyaSocializeUrl, 
                useCache = False
                )
            
            # Retrieve login token from cookie
            if 'errorMessage' in gigyaJSON:
                control.showNotification(gigyaJSON.get('errorMessage'), control.lang(50004))
                    
            if 'statusCode' in gigyaJSON and gigyaJSON.get('statusCode') == 200 and 'login_token' in gigyaJSON:
                loginToken = gigyaJSON.get('login_token').encode('utf8')
                
                # Retrieve UID, UIDSignature and signatureTimestamp
                params = {
                    'include' : 'profile,', 
                    'APIKey': apikey, 
                    'sdk' : 'js_' + gigyaVersion,
                    'login_token' : loginToken,
                    'authMode' : 'cookie',
                    'pageURL' : config.kapamilyaAccountsSSOUrl + config.uri.get('checksession'),
                    'format' : 'json',
                    'context' : 'R' + str(randint(10000, 99999)**2)
                    }
                accountJSON = callJsonApi(
                    config.uri.get('gigyaAccountInfo') + '?' + urllib.urlencode(params), 
                    headers = [
                        ('Cookie', '; '.join(cookie)),
                        ('Referer', config.gigyaCDNUrl + webSdkURI)
                        ], 
                    base_url= config.gigyaAccountUrl, 
                    useCache = False
                    )
                
                if 'errorMessage' in accountJSON:
                    control.showNotification(accountJSON.get('errorMessage'), control.lang(50004))
                
                if 'statusCode' in accountJSON and accountJSON.get('statusCode') == 200:
                    
                    # get Gmid Ticket
                    cookieJar.set_cookie(cookielib.Cookie(version=0, name='gig_hasGmid', value='ver2', port=None, port_specified=False, domain='.tfc.tv', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False))
                    cookie = getCookieContent(['hasGmid', 'gmid', 'ucid', 'gig_hasGmid'])   
                    cookie.append(apiDomainCookie)
                    params = {
                        'apiKey': apikey,
                        'expires' : 3600,
                        'pageURL' : config.kapamilyaAccountsSSOUrl + config.uri.get('welcome'),
                        'format' : 'json',
                        'context' : 'R' + str(randint(10000, 99999)**2)
                        }
                    gmidJSON = callJsonApi(
                        config.uri.get('gigyaGmidTicket') + '?' + urllib.urlencode(params),
                        headers = [
                            ('Cookie', '; '.join(cookie)),
                            ('Referer', config.gigyaCDNUrl + webSdkURI)
                            ], 
                        base_url= config.gigyaSocializeUrl, 
                        useCache = False
                        )
                    
                    if 'statusCode' in gmidJSON and gmidJSON.get('statusCode') == 200 and 'gmidTicket' in gmidJSON:
                        
                        UID = accountJSON.get('UID')
                        UIDSignature = accountJSON.get('UIDSignature')
                        signatureTimestamp = accountJSON.get('signatureTimestamp')
                        
                        control.setSetting('UID', UID)
                        control.setSetting('UIDSignature', UIDSignature)
                        control.setSetting('signatureTimestamp', signatureTimestamp)
                        
                        # Generate authorization
                        redirectParams = {
                            'client_id' : 'tfconline', 
                            'redirect_uri': config.webserviceUrl + config.uri.get('callback'), 
                            'response_type' : 'id_token token',
                            'scope' : 'openid profile offline_access',
                            'nonce' : time.time()
                            }
                        # SSOGateway
                        gmidTicket = gmidJSON.get('gmidTicket').encode('utf8')
                        redirectURL = config.kapamilyaAccountsSSOUrl + config.uri.get('authCallback') + '?' + urllib.urlencode(redirectParams)
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
                                ('Origin', config.kapamilyaAccountsSSOUrl),
                                ('Referer', config.kapamilyaAccountsSSOUrl + config.uri.get('welcome')),
                                ('Content-Type', 'application/x-www-form-urlencoded')
                                ], 
                            base_url = config.gigyaSocializeUrl,
                            useCache = False
                            )
                        UUID = re.compile('UUID=([a-zA-Z0-9.]+)[\'|"];').search(SSOGateway).group(1)
                        
                        # gltAPIToken = urllib.urlencode({ 'glt_' + apikey : loginToken + '|UUID=' + UUID })
                        cookieJar.set_cookie(cookielib.Cookie(version=0, name='glt_' + apikey, value=loginToken + '|UUID=' + UUID, port=None, port_specified=False, domain='.tfc.tv', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False))
                        gltSSOToken = urllib.urlencode({ 'glt_' + ssoKey : loginToken + '|UUID=' + UUID })
                        
                        cookie = getCookieContent(exceptFilter=gacCookie) 
                        cookie.append(apiDomainCookie)
                        cookie.append(gltSSOToken)
                        
                        # Authorize callback URL
                        callServiceApi(
                            config.uri.get('authCallback') + '?' + urllib.urlencode(redirectParams),
                            headers = [
                                ('Cookie', '; '.join(cookie))
                            ], 
                            base_url = config.kapamilyaAccountsSSOUrl, 
                            useCache = False
                            )
                            
                        # Authenticate into TFC.tv
                        params = {
                            'u' : UID, 
                            's' : UIDSignature, 
                            't' : signatureTimestamp,
                            'returnUrl' : config.uri.get('base') 
                            }
                        html = callServiceApi(
                            config.uri.get('authSSO') + '?' + urllib.urlencode(params), 
                            headers = [
                                ('Cookie', '; '.join(cookie)),
                                ('Referer', config.websiteUrl + config.uri.get('base'))
                            ], 
                            base_url = config.websiteUrl, 
                            useCache = False
                            )
                            
                        # If no error, check if connected
                        if 'TFC - Error' not in html:
                            # Check if session OK
                            params = {
                                'u' : UID, 
                                's' : UIDSignature, 
                                't' : signatureTimestamp
                                }
                            checksession = callJsonApi(
                                config.uri.get('checkSSO') + '?' + urllib.urlencode(params), 
                                headers = [
                                    ('Cookie', '; '.join(cookie)),
                                    ('Referer', config.websiteUrl + config.uri.get('base'))
                                ], 
                                base_url = config.websiteUrl, 
                                useCache = False
                                )
                        
                        if checksession and 'StatusCode' in checksession and checksession.get('StatusCode') == 0:
                            logged = True
                            generateNewFingerprintID()
                        
            if quiet == False:
                if logged == True:
                    logger.logNotice('You are now logged in')
                    control.setSetting('accountJSON', json.dumps(accountJSON))
                    control.showNotification(control.lang(57009) % accountJSON.get('profile').get('firstName'), control.lang(50007))
                else:
                    logger.logError('Authentification failed')
                    control.showNotification(control.lang(57024), control.lang(50006))
            
    return logged 
    
def getFromCookieByName(string, startWith=False):
    logger.logInfo('called function')
    global cookieJar
    cookieObj = None
    
    for c in cookieJar:
        if (startWith and c.name.startswith(string)) or (not startWith and c.name == string) :
            cookieObj = c
            break
                
    return cookieObj
    
def getCookieContent(filter=False, exceptFilter=False):
    logger.logInfo('called function')
    global cookieJar
    cookie = []
    for c in cookieJar:
        if (filter and c.name not in filter) or (exceptFilter and c.name in exceptFilter):
            continue
        cookie.append('%s=%s' % (c.name, c.value))
    return cookie

def generateNewFingerprintID(previous=False):
    logger.logInfo('called function')
    from random import randint
    if previous == False:
        control.setSetting('previousFingerprintID', control.setting('fingerprintID'))
    else:
        control.setSetting('previousFingerprintID', previous)
    control.setSetting('fingerprintID', hashlib.md5(control.setting('emailAddress')+str(randint(0, 1000000))).hexdigest())
    if control.setting('generateNewFingerprintID') == 'true':
        control.setSetting('generateNewFingerprintID', 'false')
    return True
    
def logout(quiet=True):
    logger.logInfo('called function')
    # https://kapamilya-accounts.abs-cbn.com/api/spa/SSOLogout
    if quiet == False and isLoggedIn() == False:
        control.showNotification(control.lang(57000), control.lang(50005))
    callServiceApi(config.uri.get('logout'), headers = [('Referer', config.websiteUrl + config.uri.get('base'))], base_url = config.websiteUrl, useCache = False)
    cookieJar.clear()
    if quiet == False and isLoggedIn() == False:
        control.showNotification(control.lang(57010))
        control.exit()

def checkIfError(html):
    error = False
    message = ''
    if html == '' or html == None:
        error = True
        message = control.lang(57029)
    else:
        t = common.parseDOM(html, "title")
        if len(t) > 0:
            if 'Error' in t[0]:
                error = True
                message = t[0].split(' | ')[1]
    return { 'error' : error, 'message' : message }

def callServiceApi(path, params={}, headers=[], base_url=config.websiteUrl, useCache=True, jsonData=False, returnMessage=True):
    logger.logInfo('called function with param (%s)' % (path))
    global cookieJar
    
    res = {}
    cached = False
    toCache = False
    
    # No cache if full response required
    if returnMessage == False:
        useCache = False
    
    key = config.urlCachePrefix + cache.generateHashKey(base_url + path + urllib.urlencode(params))
    logger.logDebug('Key %s : %s - %s' % (key, base_url + path, params))
    
    if useCache == True:
        tmp = cache.shortCache.getMulti(key, ['url', 'timestamp'])
        if (tmp == '') or (tmp[0] == '') or (time.time()-float(tmp[1])>int(control.setting('cacheTTL'))*60):
            toCache = True
            logger.logInfo('No cache for (%s)' % key)
        else:
            cached = True
            res['message'] = tmp[0]
            logger.logInfo('Used cache for (%s)' % key)
    
    if cached is False:
        opener = urllib2.build_opener(urllib2.HTTPRedirectHandler(), urllib2.HTTPCookieProcessor(cookieJar))
        userAgent = config.userAgents[base_url] if base_url in config.userAgents else config.userAgents['default']
        headers.append(('User-Agent', userAgent))
        opener.addheaders = headers
        logger.logDebug('### Request headers, URL & params ###')
        logger.logDebug(headers)
        logger.logDebug('%s - %s' % (base_url + path, params))
        requestTimeOut = int(control.setting('requestTimeOut')) if control.setting('requestTimeOut') != '' else 20
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
                
            logger.logDebug('### Response headers ###')
            logger.logDebug(response.geturl())
            logger.logDebug('### Response redirect URL ###')
            logger.logDebug(response.info())
            logger.logDebug('### Response ###')
            res['message'] = response.read() if response else ''
            res['status'] = int(response.getcode())
            res['headers'] = response.info()
            res['url'] = response.geturl()
            logger.logDebug(res)
        except (urllib2.URLError, ssl.SSLError) as e:
            logger.logError(e)
            message = '%s : %s' % (e, base_url + path)
            # message = "Connection timeout : " + base_url + path
            logger.logSevere(message)
            control.showNotification(message, control.lang(50004))
            # No internet connection error
            if 'Errno 11001' in message:
                logger.logError('Errno 11001 - No internet connection')
                control.showNotification(control.lang(57031), control.lang(50004), time=5000)
            toCache = False
            pass
        
        if toCache == True and res:
            cache.shortCache.setMulti(key, {'url': repr(res.get('message')), 'timestamp' : time.time()})
            logger.logDebug('Stored in cache (%s) : %s' % (key, res))
    
    # Clear headers
    headers[:] = []
    
    if returnMessage == True:
        return res.get('message')
        
    return res

def callJsonApi(path, params={}, headers=[('X-Requested-With', 'XMLHttpRequest')], base_url=config.webserviceUrl, useCache=True, jsonData=False):
    logger.logInfo('called function')
    data = {}
    res = callServiceApi(path, params, headers, base_url, useCache, jsonData)
    try:
        data = json.loads(res) if res != '' else []
    except:
        pass
    return data
    
def checkProxy():
    if (control.setting('useProxy') == 'true'):
        url = control.setting('proxyCheckUrl') % (control.setting('proxyHost'), control.setting('proxyPort'))
        response = callServiceApi(url, base_url = '', useCache=False, returnMessage=False)
        logger.logDebug(response)    
        if response.get('status', '') != 200:
            control.alert(control.lang(57028), title=control.lang(50004))
            return False
    return True
            
# This function is a workaround to fix an issue on cookies conflict between live stream and shows episodes
def cleanCookies(notify=True):
    logger.logInfo('called function')
    message = ''
    if os.path.exists(os.path.join(control.homePath, 'cache', 'cookies.dat'))==True:  
        logger.logInfo('cookies file FOUND (cache)')
        try: 
            os.unlink(os.path.join(control.homePath, 'cache', 'cookies.dat'))
            message = control.lang(57004)
        except: 
            message = control.lang(57005)
                
    elif os.path.exists(os.path.join(control.homePath, 'temp', 'cookies.dat'))==True:  
        logger.logInfo('cookies file FOUND (temp)')
        try: 
            os.unlink(os.path.join(control.homePath, 'temp', 'cookies.dat'))
            message = control.lang(57004)
        except: 
            message = control.lang(57005)
    elif os.path.exists(os.path.join(control.dataPath, config.cookieFileName))==True:  
        logger.logInfo('cookies file FOUND (profile)')
        try: 
            os.unlink(os.path.join(control.dataPath, config.cookieFileName))
            message = control.lang(57004)
        except: 
            message = control.lang(57005)
    else:
        message = control.lang(57006)
        
    if notify == True:
        control.showNotification(message)
    
#---------------------- MAIN ----------------------------------------
thisPlugin = int(sys.argv[1])
    
cookieJar = cookielib.CookieJar()
cookieFile = ''
cookieJarType = ''

if os.path.exists(control.dataPath):
    cookieFile = os.path.join(control.dataPath, config.cookieFileName)
    cookieJar = cookielib.LWPCookieJar(cookieFile)
    cookieJarType = 'LWPCookieJar'
    
if cookieJarType == 'LWPCookieJar':
    try:
        cookieJar.load()
    except:
        loginToWebsite()
    
if cookieJarType == 'LWPCookieJar':
    cookieJar.save()


