# -*- coding: utf-8 -*-

'''
    Tfc.tv Add-on
    Copyright (C) 2018 cmik
'''

import os,sys,re,urllib,urllib2,ssl,cookielib,json,time,hashlib
from operator import itemgetter
from resources import config
from resources.lib.libraries import control
from resources.lib.libraries import cache
from resources.lib.models import episodes
from resources.lib.models import shows

common = control.common
logger = control.logger
episodeDB = episodes.Episode(control.episodesFile)
showDB = shows.Show(control.showsFile)

#---------------------- FUNCTIONS ----------------------------------------                  

def playEpisode(url, name, thumbnail):    
    errorCode = -1
    episodeDetails = {}
    episode = url.split('/')[0]
    
    if checkProxy() == True:
        # Check if logged in
        if isLoggedIn() == False:
            control.showNotification(control.lang(57012), control.lang(50002))
            login()
            
        # for i in range(int(control.setting('loginRetries')) + 1):
            # episodeDetails = getMediaInfo(episode, name, thumbnail)
            # if episodeDetails and 'errorCode' in episodeDetails and episodeDetails['errorCode'] == 0 and 'data' in episodeDetails:
                # break
            # else:
                # login()
                
        episodeDetails = getMediaInfo(episode, name, thumbnail)
        if episodeDetails and 'errorCode' in episodeDetails and episodeDetails['errorCode'] == 0 and 'data' in episodeDetails:
            if 'preview' in episodeDetails['data'] and episodeDetails['data']['preview'] == True:
                control.showNotification(control.lang(57025), control.lang(50002))
            else:
                if 'StatusMessage' in episodeDetails and episodeDetails['StatusMessage'] != '':
                    control.showNotification(episodeDetails['StatusMessage'], control.lang(50009))
            url = control.setting('proxyStreamingUrl') % (control.setting('proxyHost'), control.setting('proxyPort'), urllib.quote(episodeDetails['data']['uri'])) if (control.setting('useProxy') == 'true') else episodeDetails['data']['uri']
            plot = episodeDetails['data']['plot']
            fanart = episodeDetails['data']['fanart']
            liz = control.item(name, path=url, thumbnailImage=thumbnail, iconImage="DefaultVideo.png")
            liz.setInfo(type='Video', infoLabels={'Title': name, 'Plot': plot})
            liz.setProperty('fanart_image', fanart)
            liz.setProperty('IsPlayable', 'true')
            try: 
                return control.resolve(thisPlugin, True, liz)
            except: 
                control.showNotification(control.lang(57020), control.lang(50004))
        else:
            if (not episodeDetails) or (episodeDetails and 'errorCode' in episodeDetails and episodeDetails['errorCode'] != 0):
                if 'StatusMessage' in episodeDetails:
                    control.showNotification(episodeDetails['StatusMessage'])
                else:
                    control.showNotification(control.lang(57001), control.lang(50009))
    return False
    
def getMediaInfo(episodeId, title, thumbnail):
    logger.logInfo('called function')
    mediaInfo = getMediaInfoFromWebsite(episodeId)
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
            'episodenumber' : 1,
            'url' : mediaInfo['data']['url'],
            'description' : mediaInfo['data']['plot'],
            'shortdescription' : mediaInfo['data']['plot'],
            'dateaired' : mediaInfo['data']['dateaired'],
            'year' : mediaInfo['data']['year'],
            'parentalAdvisory' : mediaInfo['data']['parentalAdvisory']
            }
        episodeDB.set(e)
        
    return mediaInfo
    
def getMediaInfoFromWebsite(episodeId):
    logger.logInfo('called function with param (%s)' % (str(episodeId)))
    
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
        
        # Parental advisory
        mediaInfo['data']['parentalAdvisory'] = 'false'
        if re.compile('var dfp_c = ".*2900.*";', re.IGNORECASE).search(html):
            mediaInfo['data']['parentalAdvisory'] = 'true'
            if control.setting('parentalAdvisoryCheck') == 'true':
                alert(control.lang(57011),title=control.lang(50003))
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
            episodeDetails = callJsonApi(config.uri.get('mediaFetch'), params, headers=callHeaders, base_url=config.websiteSecuredUrl, useCache=False, jsonData=True)
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
                    if control.setting('streamServerModification') == 'true' and control.setting('streamServer') != '':
                        episodeDetails['media']['uri'] = episodeDetails['media']['uri'].replace('https://o2-i.', control.setting('streamServer'))                
                    
                    # choose best stream quality
                    if (control.setting('chooseBestStream') == 'true'):
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
                    
                    show = getShow(mediaInfo['data']['showid'])
                    mediaInfo['data'].update(episodeDetails['media'])
                    mediaInfo['data']['show'] = show.get('name')
                    mediaInfo['data']['plot'] = episodeData.get('description')
                    mediaInfo['data']['fanart'] = show.get('fanart')
                    mediaInfo['data']['type'] = episodeData.get('@type').lower()
                    mediaInfo['data']['dateaired'] = episodeData.get('datePublished')
                    mediaInfo['data']['year'] = episodeData.get('datePublished').split('-')[0]
                    mediaInfo['data']['episodenumber'] = 0
                    if mediaInfo['data']['type'] == 'movie':
                        mediaInfo['data']['episodenumber'] = 1
                    
                if 'StatusMessage' in episodeDetails and episodeDetails['StatusMessage'] != '' and episodeDetails['StatusMessage'] != 'OK':
                    mediaInfo['StatusMessage'] = episodeDetails['StatusMessage']
                
    return mediaInfo
        
def reloadCatalogCache():
    logger.logInfo('called function')
    res = updateCatalogCache()
    if res is True:
        control.showNotification(control.lang(57003), control.lang(50001))
    else:
        control.showNotification(control.lang(57027), control.lang(50004))
    
def updateCatalogCache():
    logger.logInfo('called function')
    control.showNotification(control.lang(57015), control.lang(50005))
    cache.longCache.cacheClean(True)
    cache.shortCache.cacheClean(True)
    
    # checkElaps = lambda x, y: x = time.time()-x if (time.time()-x) > y else x
    # elaps = start = time.time()
    
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
        # nbCat = len(categories)
        # t = i = j = k = 0
        for cat in categories:
            # subCategories = cache.lCacheFunction(getSubCategories, cat['id'])
            subCategories = getSubCategories(cat['id'])
            # nbSubCat = len(subCategories)
            for sub in subCategories:
                # shows = cache.sCacheFunction(getShows, sub['id'])
                shows = getShows(sub['id'])
                # nbShow = len(shows)
                for s in shows:
                    # show = cache.lCacheFunction(getShow, s['id'])
                    show = getShow(s['id'])
                    # if checkElaps(elaps, 10):
                        # total = nbShow
                        # loaded = k
                        # percent = min((100 / (nbSubCat-j) / (nbCat-i) / (nbShow)) * loaded / total)
                        # logger.showNotification('Updating catalog... %s' % (str(percent)+'%'), title=control.lang(50005), time=10000)
                    # if show:
                        # episodes = cache.sCacheFunction(getShowEpisodes, show['id'])
                    # k++
                # j++
            # i++
    except:
        return False
        
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
    html = callServiceApi(url)
    return extractListCategories(html)
    
def getMylistCategoryItems(id):
    logger.logInfo('called function')
    url = config.uri.get('myList')
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
            'id' : int(showId),
            'parentid' : -1,
            'parentname' : '',
            'name' : common.replaceHTMLCodes(showName).encode('utf8'),
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
                'CONTINUE WATCHING', 
                'MY LIST', 
                'IWANT ORIGINALS - EXCLUSIVE FOR PREMIUM'
                ]
            if sectionName not in exceptSections:
                data.append({'id' : str(i), 'name' : sectionName}) #, 'url' : '/', 'fanart' : ''})
        i += 1
    return data
    
def getWebsiteSectionContent(sectionId, page=1, itemsPerPage=8):
    logger.logInfo('called function')
    page -= 1
    data = []
    
    html = getWebsiteHomeHtml()
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
    # episodeDB.get([d.get('id') for d in data])
    return data
    
def extractWebsiteSectionShowData(url, html):
    logger.logInfo('called function')
    
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
            'id' : int(showId),
            'parentid' : -1,
            'parentname' : '',
            'name' : common.replaceHTMLCodes(showName).encode('utf8'),
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
    logger.logInfo('called function')
    episodeId = re.compile('/([0-9]+)/', re.IGNORECASE).search(url).group(1)
    res = episodeDB.get(episodeId)
    if len(res) == 1:
        return res[0]
    else:
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
                    data.append(res[0])
                else:
                    data.append({
                        'id' : int(d['id']),
                        'name' : d['name'],
                        'parentid' : d['parentid'],
                        'parentname' : d['parentname'],
                        'logo' : d['image'].replace(' ', '%20'),
                        'image' : d['image'].replace(' ', '%20'),
                        'fanart' : d['image'].replace(' ', '%20'),
                        'banner' : d['image'].replace(' ', '%20'),
                        'url' : d['url'],
                        'description' : d['description'],
                        'shortdescription' : d['shortdescription'],
                        'year' : dateAired
                        })
                
    return data
    
def extractShows(html):
    logger.logInfo('called function')
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
            'dateairedstr' : aired.replace('AIRED: ', '')
            })
            
    return data

def getShow(showId):
    logger.logInfo('called function with param %s' % (showId))
    data = {}
    
    html = callServiceApi(config.uri.get('showDetails') % showId)
    err = checkIfError(html)
    if err.get('error') == False:
        images = common.parseDOM(html, "div", attrs = { 'class' : 'hero-image-logo' })
        t = common.parseDOM(html, "link", attrs = { 'rel' : 'image_src' }, ret = 'href')
        image = t[0] if len(t) > 0 else ''
        if len(images) == 0:
            logo = image
        else:
            logo = common.parseDOM(images, "img", ret = "src")[0]
            
        url = common.parseDOM(html, "link", attrs = { 'rel' : 'canonical' }, ret = 'href')[0]
        
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
            'name' : common.replaceHTMLCodes(name),
            'parentid' : -1,
            'parentname' : common.replaceHTMLCodes(genre),
            'logo' : logo,
            'image' : image,
            'fanart' : banner,
            'banner' : banner,
            'url' : url,
            'description' : common.replaceHTMLCodes(description),
            'shortdescription' : common.replaceHTMLCodes(description),
            'year' : '',
            'episodes' : episodes,
            'type': 'show'
            }
        showDB.set(data)
    else:
        logger.logWarning('Error on show %s: %s' % (showId, get('message')))
    return data

def getEpisodesPerPage(showId, page=1, itemsPerPage=8):
    logger.logInfo('called function')
    data = []
    
    # max nb items per page that TFC website can provide
    websiteNbItemsPerPage = 8
    # Calculating page index and needed pages to request for building next page to display
    firstPage = 1 if page == 1 else ((itemsPerPage / websiteNbItemsPerPage) * (page - 1) + 1)
    lastPage = itemsPerPage / websiteNbItemsPerPage * page
    
    paginationURL = config.uri.get('episodePagination')
    # showDetails = cache.sCacheFunction(getShow, showId)
    showDetails = getShow(showId)
    if showDetails:
        for page in range(firstPage, lastPage+1, 1):
            html = callServiceApi(paginationURL % (showId, page))
        
            # if page does not exist
            if page > 1 and html == '':
                break
            # if no pagination, it's a movie or special
            elif page == 1 and html == '':
                showDetailURL = config.uri.get('showDetails')
                html = callServiceApi(showDetailURL % showId)
                episodeId = int(re.compile('var dfp_e = "(.+)";', re.IGNORECASE).search(html).group(1))
                data.append({
                    'id' : episodeId,
                    'title' : showDetails.get('name'),
                    'show' : showDetails.get('name'),
                    'image' : showDetails.get('image'),
                    'episodenumber' : 1,
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
                    res = episodeDB.get(episodeId)
                    if len(res) == 1:
                        data.append(res[0])
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
                        
                        episodeData = showDetails.get('episodes').get(episodeId)
                        if episodeData:
                            title = episodeData.get('title')
                            episodeNumber = episodeData.get('episodenumber')
                        
                        e = {
                            'id' : episodeId,
                            'title' : title.encode('utf8'),
                            'parentid' : int(showId),
                            'show' : showTitle,
                            'image' : image,
                            'fanart' : fanart,
                            'episodenumber' : episodeNumber,
                            'url' : image,
                            'description' : description.encode('utf8'),
                            'shortdescription' : shortDescription.encode('utf8'),
                            'dateaired' : dateAired,
                            'year' : year,
                            'parentalAdvisory' : ''
                            }
                        episodeDB.set(e)
                        data.append(e)
                        
                    i += 1
            
    # return sorted(data, key=lambda episode: episode['title'], reverse=True)
    return data
      
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
      
# def getEpisodeDataByShow(showId, episodeId):
    # data = {}
    # episodes = cache.sCacheFunction(getShowEpisodes, showId)
    # if episodes and episodeId in episodes:
        # data = episodes[episodeId]
    # else:
        # episode = cache.lCacheFunction(getEpisodeData, episodeId)
        # if episode:
            # episode['title'] = episode.get('dateaired')
            # episode['description'] = episode.get('synopsis')
            # data = episode
    # return data
    
# def getEpisodeData(episodeId):
    # logger.logInfo('called function')
    # html = callServiceApi(config.uri.get('episodeDetails') % episodeId, base_url = config.websiteUrl, useCache=False)
    # body = common.parseDOM(html, 'body')
    # episodeData = json.loads(re.compile('var ldj = (\{.+\})', re.IGNORECASE).search(html).group(1))
    # if 'statusCode' in res and res['statusCode'] == 1:
        # data = res['episode']
        # data['title'] = data['streamInfo']['streamTitle']
        # data['url'] = data['streamInfo']['streamURL']
        # data['dateaired'] = data['dateAired'].split('T')[1]
        # data['year'] = data['dateAired'].split('-')[0]
        # data['description'] = data['synopsis']
        # data['image'] = data['image']['video']
    # return data
    
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
        'name' : name.encode('utf8'),
        'firstName' : user.get('firstName', '').encode('utf8'),
        'lastName' : user.get('lastName', '').encode('utf8'),
        'email' : user.get('email', '').encode('utf8'),
        'state' : state.encode('utf8'),
        'country' : user.get('country', '').encode('utf8'),
        'memberSince' : memberSince.replace('MEMBER SINCE ', '').encode('utf8')
    }
    
def getUserSubscription():
    logger.logInfo('called function')
    url = config.uri.get('profileDetails')
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
    logger.logInfo('called function')
    logger.logDebug(url)
    control.showNotification(control.lang(57026))
    # url = config.uri.get('addToList')
    # data = callJsonApi(url, params = {'CategoryId': 4894, 'EpisodeId': 167895, 'type': 'episode'}, useCache=False)

def removeFromMyList(url, name, type):
    logger.logInfo('called function')
    logger.logDebug(url)
    control.showNotification(control.lang(57026))
    # url = config.uri.get('removeFromList')
    # data = callJsonApi(url, params = {'CategoryId': 4894, 'EpisodeId': 167895, 'type': 'episode'}, useCache=False)
    
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
    html = callServiceApi(config.uri.get('profile'), headers=[('Referer', config.websiteSecuredUrl+'/')    ], base_url=config.websiteSecuredUrl, useCache=False)
    return False if 'TfcTvId' not in html else True
    
def loginToWebsite(quiet=False): 
    from random import randint
    import time
    global cookieJar
    
    logged = False
    
    if quiet == False:
        control.showNotification(control.lang(57019), control.lang(50005))
    
    emailAddress = control.setting('emailAddress')
    password = control.setting('password')
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
        base_url = config.websiteSSOUrl, 
        useCache = False
    )
    
    # Login into kapamilya-accounts
    data = callJsonApi(config.uri.get('login'), authData, base_url=config.websiteSSOUrl, useCache = False, jsonData=True)
    if (not data or ('errorCode' in data and data.get('errorCode') != 0) or ('errorMessage' in data)) and quiet == False:
        if 'errorMessage' in data:
            control.showNotification(data.get('errorMessage'), control.lang(50006))
        else:
            control.showNotification(control.lang(57024), control.lang(50006))
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
            config.uri.get('gigyaJS') + '?' + urllib.urlencode(params), 
            base_url = config.gigyaCDNUrl, 
            useCache = False
        )
        gigyaVersion = re.compile('"version":?"([\d.]+)",').search(gigyaHtml).group(1)
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
        
        # Retrieve authorization code from cookie
        gacCookie = getFromCookieByName('gac_', startWith=True)
        gacToken = gacCookie.value

        # Retrieve needed cookies
        params = {
            'apiKey' : apikey, 
            'pageURL' : config.websiteSSOUrl + config.uri.get('signin'), 
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
        
        # Retrieve the login token
        params = {
            'sessionExpiration' : -2, 
            'authCode' : gacToken, 
            'APIKey': apikey, 
            'sdk' : 'js_' + gigyaVersion,
            'authMode' : 'cookie',
            'pageURL' : config.websiteSSOUrl + config.uri.get('welcome'),
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
                'pageURL' : config.websiteSSOUrl + config.uri.get('checksession'),
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
                    'pageURL' : config.websiteSSOUrl + config.uri.get('welcome'),
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
                    redirectURL = config.websiteSSOUrl + config.uri.get('authCallback') + '?' + urllib.urlencode(redirectParams)
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
                            ('Origin', config.websiteSSOUrl),
                            ('Referer', config.websiteSSOUrl + config.uri.get('welcome')),
                            ('Content-Type', 'application/x-www-form-urlencoded')
                            ], 
                        base_url = config.gigyaSocializeUrl,
                        useCache = False
                        )
                    UUID = re.compile('UUID=([a-zA-Z0-9.]+)";').search(SSOGateway).group(1)
                    
                    # gltAPIToken = urllib.urlencode({ 'glt_' + apikey : loginToken + '|UUID=' + UUID })
                    cookieJar.set_cookie(cookielib.Cookie(version=0, name='glt_' + apikey, value=loginToken + '|UUID=' + UUID, port=None, port_specified=False, domain='.tfc.tv', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False))
                    gltSSOToken = urllib.urlencode({ 'glt_' + ssoKey : loginToken + '|UUID=' + UUID })
                    
                    cookie = getCookieContent(exceptFilter=[gacCookie.name]) 
                    cookie.append(apiDomainCookie)
                    cookie.append(gltSSOToken)
                    
                    # Authorize callback URL
                    callServiceApi(
                        config.uri.get('authCallback') + '?' + urllib.urlencode(redirectParams),
                        headers = [
                            ('Cookie', '; '.join(cookie))
                        ], 
                        base_url = config.websiteSSOUrl, 
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
                control.setSetting('accountJSON', json.dumps(accountJSON))
                control.showNotification(control.lang(57009) % accountJSON.get('profile').get('firstName'), control.lang(50007))
            else:
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
        control.execute("XBMC.Container.Update(path,replace)")

def checkIfError(html):
    error = False
    message = ''
    if html == '':
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
    logger.logInfo('called function')
    global cookieJar
    
    res = {}
    cached = False
    toCache = False
    
    # No cache if full response required
    if returnMessage == False:
        useCache = False
    
    key = cache.generateHashKey(base_url + path + urllib.urlencode(params))
    logger.logDebug('Key %s : %s - %s' % (key, base_url + path, params))
    
    if useCache == True:
        if cache.shortCache.get(key) == '':
            toCache = True
            logger.logInfo('No cache for (%s)' % key)
        else:
            cached = True
            res['message'] = cache.shortCache.get(key)
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
            logger.logError(message)
            control.showNotification(message)
            toCache = False
        
        if toCache == True and res:
            cache.shortCache.set(key, repr(res.get('message')))
            logger.logDebug('Stored in cache (%s) : %s' % (key, res))
    
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


