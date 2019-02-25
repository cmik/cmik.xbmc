# -*- coding: utf-8 -*-

'''
    Tfc.tv Add-on
    Copyright (C) 2018 cmik

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


import os,sys,urlparse,urllib,xbmc,time
from resources import config
from resources.lib.libraries import control
from resources.lib.libraries import cache
from resources.lib.sources import tfctv
from operator import itemgetter

artPath = control.artPath()
addonFanart = control.addonFanart()
logger = control.logger

try: 
    action = dict(urlparse.parse_qsl(sys.argv[2].replace('?','')))['action']
except:
    action = None

sysaddon = sys.argv[0]
thisPlugin = int(sys.argv[1])

class navigator:

    def root(self):
        if control.setting('useProxy') == 'true':
            tfctv.checkProxy()
            
        if control.setting('addonNewInstall') == 'true':
            self.firstInstall()
        else:
            self.showMainMenu()
    
    def showMainMenu(self):
        # if not logged in, ask to log in
        if control.setting('emailAddress') != '':
            tfctv.checkAccountChange()
            if tfctv.isLoggedIn() == False:
                if (control.confirm(control.lang(57007), line1=control.lang(57008) % control.setting('emailAddress'))):
                    (account, logged) = tfctv.checkAccountChange(True)            
            elif control.setting('displayMyList') == 'true':
                self.addDirectoryItem(control.lang(50200), '/', config.MYLIST, control.addonFolderIcon(control.lang(50200)), isFolder=True, **self.formatMenu())
        
        if control.setting('displayWebsiteSections') == 'true':
            self.addDirectoryItem(control.lang(50201), '/', config.CATEGORIES, control.addonFolderIcon(control.lang(50201)), isFolder=True, **self.formatMenu())
        else:
            self.showCategories()
            
        if control.setting('displayWebsiteSections') == 'true':
            control.showNotification(control.lang(57020), control.lang(50008))
            # sections = cache.sCacheFunction(tfctv.getWebsiteHomeSections)
            sections = tfctv.getWebsiteHomeSections()
            for s in sections:
                self.addDirectoryItem(s['name'].title(), str(s['id']), config.SECTIONCONTENT, control.addonFolderIcon(s['name'].title()), isFolder=True, **self.formatMenu())
            
        if control.setting('displayMyAccountMenu') == 'true' and control.setting('emailAddress') != '':
            self.addDirectoryItem(control.lang(50202), '/', config.MYACCOUNT, control.addonFolderIcon(control.lang(50202)), isFolder=True, **self.formatMenu())
        
        if control.setting('displayTools') == 'true':
            self.addDirectoryItem(control.lang(50203), '/', config.TOOLS, control.addonFolderIcon(control.lang(50203)))
            
        self.endDirectory()
        
        if tfctv.isLoggedIn() == False:
            control.infoDialog(control.lang(57017), control.lang(50002), time=8000)
            
    def showMyList(self):   
        categories = tfctv.getMyListCategories()
        for c in categories:
            self.addDirectoryItem(c.get('name'), str(c.get('id')), config.LISTCATEGORY, control.addonFolderIcon(c.get('name')), **self.formatMenu())
        self.endDirectory()

    def showMyListCategory(self, url):   
        items = tfctv.getMylistCategoryItems(url)
        for e in items:
            if e['type'] == 'show':
                image = e.get('logo') if control.setting('useShowLogo') == 'true' else e.get('image')
                self.addDirectoryItem(e.get('name'), str(e.get('id')), config.SHOWEPISODES, image, isFolder=True, query='parentid='+str(e.get('parentid'))+'&year='+e.get('year'), **self.formatShowInfo(e, addToList=False))
            elif e['type'] == 'episode':
                title = '%s - %s' % (e.get('show'), e.get('dateaired')) # if e.get('type') == 'movie' else '%s - Ep.%s - %s' % (e.get('show'), e.get('episodenumber'), e.get('dateaired'))
                self.addDirectoryItem(title, str(e.get('id')), config.PLAY, e.get('image'), isFolder = False, **self.formatVideoInfo(e, addToList=False))
        self.endDirectory()
            
    def showCategories(self):   
        # categories = cache.lCacheFunction(tfctv.getCategories)
        categories = tfctv.getCategories()
        for c in categories:
            self.addDirectoryItem(c.get('name'), str(c.get('id')), config.SUBCATEGORIES, control.addonFolderIcon(c.get('name')), isFolder=True, **self.formatMenu())
            
        if control.setting('displayWebsiteSections') == 'true':
            self.endDirectory()
          
    def showSubCategories(self, categoryId):
        # subCategories = cache.lCacheFunction(tfctv.getSubCategories, categoryId)
        subCategories = tfctv.getSubCategories(categoryId)
        for s in subCategories:
            self.addDirectoryItem(s.get('name'), str(s.get('id')), config.SUBCATEGORYSHOWS, control.addonFolderIcon(s.get('name')), isFolder=True, **self.formatMenu())
        self.endDirectory()
       
    def showSubCategoryShows(self, subCategoryId):
        # shows = cache.sCacheFunction(tfctv.getShows, subCategoryId)
        shows = tfctv.getShows(subCategoryId)
        if len(shows) > 0:
            self.displayShows(shows)
        else:
            self.endDirectory()
        
    def showWebsiteSectionContent(self, section, page=1):
        itemsPerPage = int(control.setting('itemsPerPage'))
        content = tfctv.getWebsiteSectionContent(section, page, itemsPerPage)
        for e in content:
            if e['type'] == 'show':
                image = e.get('logo') if control.setting('useShowLogo') == 'true' else e.get('image')
                self.addDirectoryItem(e.get('name'), str(e.get('id')), config.SHOWEPISODES, image, isFolder=True, **self.formatShowInfo(e))
            elif e['type'] == 'episode':
                title = '%s - %s' % (e.get('show'), e.get('dateaired')) # if e.get('type') == 'movie' else '%s - Ep.%s - %s' % (e.get('show'), e.get('episodenumber'), e.get('dateaired'))
                self.addDirectoryItem(title, str(e.get('id')), config.PLAY, e.get('image'), isFolder = False, **self.formatVideoInfo(e))
        if len(content) == itemsPerPage:
            self.addDirectoryItem(control.lang(56008), section, config.SECTIONCONTENT, '', page + 1)
        self.endDirectory()

    def displayShows(self, shows):
        sortedShowInfos = []
        for show in shows:
            image = show['logo'] if control.setting('useShowLogo') == 'true' else show['image']
            sortedShowInfos.append((show.get('name').lower(), show.get('name'), str(show.get('id')), config.SHOWEPISODES, image, 'parentid='+str(show.get('parentid'))+'&year='+show.get('year'), self.formatShowInfo(show)))
        
        sortedShowInfos = sorted(sortedShowInfos, key = itemgetter(0))
        for info in sortedShowInfos:
            self.addDirectoryItem(info[1], info[2], info[3], info[4], isFolder=True, query=info[5], **info[6])
                
        self.endDirectory()
        
    def showEpisodes(self, showId, page=1, parentId=-1, year=''):
        itemsPerPage = int(control.setting('itemsPerPage'))
        # episodes = cache.sCacheFunction(tfctv.getEpisodesPerPage, showId, page, itemsPerPage)
        episodes = tfctv.getEpisodesPerPage(showId, parentId, year, page, itemsPerPage)
        for e in episodes:
            self.addDirectoryItem(e.get('title'), str(e.get('id')), config.PLAY, e.get('image'), isFolder = False, **self.formatVideoInfo(e))
        if len(episodes) == itemsPerPage:
            self.addDirectoryItem(control.lang(56008), showId, config.SHOWEPISODES, '', page + 1)
        self.endDirectory()
            
    def showMyAccount(self):
        tfctv.checkAccountChange(False)
        categories = [
            { 'name' : control.lang(56004), 'url' : config.uri.get('profile'), 'mode' : config.MYINFO },
            { 'name' : control.lang(56005), 'url' : config.uri.get('base'), 'mode' : config.MYSUBSCRIPTIONS },
            { 'name' : control.lang(56006), 'url' : config.uri.get('base'), 'mode' : config.MYTRANSACTIONS }
        ]
        for c in categories:
            self.addDirectoryItem(c.get('name'), c.get('url'), c.get('mode'), control.addonFolderIcon(c.get('name')))
        self.addDirectoryItem(control.lang(56007), config.uri.get('base'), config.LOGOUT, control.addonFolderIcon('Logout'), isFolder = False)    
        self.endDirectory()
    
    def showMyInfo(self):
        loggedIn = tfctv.isLoggedIn()
        message = control.lang(57002)
        if loggedIn == True:
            try:
                user = tfctv.getUserInfo()
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
        control.showMessage(message, control.lang(56001))
    
    def showMySubscription(self):
        sub = tfctv.getUserSubscription()
        message = ''
        if sub:
            message += '%s' % (sub.get('details'))
        else:
            message = control.lang(57002)
        control.showMessage(message, control.lang(56002))
        
    def showMyTransactions(self):
        transactions = tfctv.getUserTransactions()
        message = ''
        if len(transactions) > 0:
            for t in transactions:
                message += t + "\n"
        else:
            message = control.lang(57002)
        control.showMessage(message, control.lang(56003))
            
    def showTools(self):
        self.addDirectoryItem(control.lang(56009), config.uri.get('base'), config.RELOADCATALOG, control.addonFolderIcon(control.lang(56009)))
        self.addDirectoryItem(control.lang(56018), config.uri.get('base'), config.RESETCATALOG, control.addonFolderIcon(control.lang(56018)))
        self.addDirectoryItem(control.lang(56019), config.uri.get('base'), config.IMPORTSHOWDB, control.addonFolderIcon(control.lang(56019)))
        self.addDirectoryItem(control.lang(56020), config.uri.get('base'), config.IMPORTEPISODEDB, control.addonFolderIcon(control.lang(56020)))
        self.addDirectoryItem(control.lang(56017), config.uri.get('base'), config.CHECKLIBRARYUPDATES, control.addonFolderIcon(control.lang(56017)))
        self.addDirectoryItem(control.lang(56010), config.uri.get('base'), config.CLEANCOOKIES, control.addonFolderIcon(control.lang(56010)))
        self.addDirectoryItem('Quick setup', config.uri.get('base'), config.FIRSTINSTALL, control.addonFolderIcon('Quick setup'))
        self.endDirectory()
            
    def firstInstall(self):
        control.run(config.IMPORTALLDB, 'install')
        self.addDirectoryItem(control.lang(56011) % (' ' if control.setting('showEnterCredentials') == 'true' else 'x'), config.uri.get('base'), config.ENTERCREDENTIALS, control.addonFolderIcon(control.lang(56011)))
        self.addDirectoryItem(control.lang(56012) % (' ' if control.setting('showPersonalize') == 'true' else 'x'), config.uri.get('base'), config.PERSONALIZESETTINGS, control.addonFolderIcon(control.lang(56012)))
        # self.addDirectoryItem(control.lang(56013) % (' ' if control.setting('showUpdateCatalog') == 'true' else 'x'), config.uri.get('base'), config.IMPORTALLDB, control.addonFolderIcon(control.lang(56013)))
        self.addDirectoryItem(control.lang(56014) % (control.lang(56015) if control.setting('showEnterCredentials') == 'true' or control.setting('showPersonalize') == 'true' else control.lang(56016)), config.uri.get('base'), config.ENDSETUP, control.addonFolderIcon('Skip'))
        self.endDirectory()
        if control.setting('showWelcomeMessage') == 'true':
            control.showMessage(control.lang(57016), control.lang(57018))
            control.setSetting('showWelcomeMessage', 'false')
        
    def enterCredentials(self):
        tfctv.enterCredentials()
        control.setSetting('showEnterCredentials', 'false')
        control.refresh()
        
    def optimizeLibrary(self):
        tfctv.reloadCatalogCache()
        control.setSetting('showUpdateCatalog', 'false')
        control.refresh()
        
    def personalizeSettings(self):
        control.openSettings()
        control.setSetting('showPersonalize', 'false')
        control.refresh()
        
    def endSetup(self):
        control.setSetting('addonNewInstall', 'false')
        control.refresh()
        
    def formatMenu(self, bgImage=''):
        if bgImage == '': bgImage = control.setting('defaultBG')
        data = { 
            'listArts' : { 'fanart' : bgImage, 'banner' : bgImage }
            }
        return data
        
    def formatShowInfo(self, info, addToList=True, options = {}):
        contextMenu = {}
        add = { control.lang(50300) : 'XBMC.Container.Update(%s)' % self.generateActionUrl(str(info.get('id')), config.ADDTOLIST, info.get('name'), query='ltype=%s&type=%s' % (info.get('ltype'), info.get('type'))) } 
        remove = { control.lang(50301) : 'XBMC.Container.Update(%s)' % self.generateActionUrl(str(info.get('id')), config.REMOVEFROMLIST, info.get('name'), query='ltype=%s&type=%s' % (info.get('ltype'), info.get('type'))) } 
        if addToList == True: 
            contextMenu.update(add)
        else:
            contextMenu.update(remove)
        
        if control.setting('exportToLibrary') == 'true':
            addToLibrary = { control.lang(50302) : 'XBMC.Container.Update(%s)' % self.generateActionUrl(str(info.get('id')), config.ADDTOLIBRARY, info.get('name'), query='parentid=%s&year=%s&ltype=%s&type=%s' % (str(info.get('parentid')), info.get('year'), info.get('ltype'), info.get('type'))) }
            contextMenu.update(addToLibrary)
        
        data = { 
            'listArts' : { 'clearlogo' : info.get('logo'), 'fanart' : info.get('fanart'), 'banner' : info.get('banner') }, 
            'listInfos' : { 
                'video' : { 
                    'sorttitle': info.get('name'),
                    'plot' : info.get('description'), 
                    'year' : info.get('year'),
                    'mediatype' : 'tvshow' 
                    } 
                },
            'contextMenu' : contextMenu
            }
        
        if info.get('casts', False):    
            data['listCasts'] = info.get('casts')
            
        return data
            
    def formatVideoInfo(self, info, addToList=True, options = {}):
        add = { control.lang(50300) : 'XBMC.Container.Update(%s)' % self.generateActionUrl(str(info.get('id')), config.ADDTOLIST, info.get('title'), query='type=%s' % (info.get('ltype',))) } 
        remove = { control.lang(50301) : 'XBMC.Container.Update(%s)' % self.generateActionUrl(str(info.get('id')), config.REMOVEFROMLIST, info.get('title'), query='type=%s' % (info.get('ltype'))) } 
        contextMenu = add if addToList == True else remove

        data = { 
            'listArts' : { 'fanart' : info.get('fanart'), 'banner' : info.get('fanart') }, 
            'listProperties' : { 'IsPlayable' : 'true' } , 
            'listInfos' : { 
                'video' : { 
                    'sorttitle' : info.get('dateaired'), 
                    'tvshowtitle' : info.get('show'), 
                    'episode' : info.get('episodenumber'), 
                    'tracknumber' : info.get('episodenumber'), 
                    'plot' : info.get('description'), 
                    'aired' : info.get('dateaired'), 
                    'year' : info.get('year'), 
                    'mediatype' : info.get('type') 
                    } 
                },
            'contextMenu' : contextMenu
            }

        if info.get('showObj', False) and info.get('showObj').get('casts', False):    
            data['listCasts'] = info.get('showObj').get('casts')

        return data
            
            
    # def addDirectoryItem(self, name, query, thumb, icon, context=None, isAction=True, isFolder=True):
        # try: name = control.lang(name).encode('utf-8')
        # except: pass
        # url = '%s?action=%s' % (sysaddon, query) if isAction == True else query
        # thumb = os.path.join(artPath, thumb) if not artPath == None else icon
        # cm = []
        # if not context == None: cm.append((control.lang(context[0]).encode('utf-8'), 'RunPlugin(%s?action=%s)' % (sysaddon, context[1])))
        # item = control.item(label=name, iconImage=thumb, thumbnailImage=thumb)
        # item.addContextMenuItems(cm, replaceItems=False)
        # if not addonFanart == None: item.setProperty('Fanart_Image', addonFanart)
        # control.addItem(handle=int(sys.argv[1]), url=url, listitem=item, isFolder=isFolder)
            
    def addDirectoryItem(self, name, url, mode, thumbnail, page=1, isFolder=True, query='', **kwargs):
        u = self.generateActionUrl(url, mode, name, thumbnail, page, query)
        liz = control.item(label=name, iconImage="DefaultFolder.png", thumbnailImage=thumbnail)
        liz.setInfo(type="Video", infoLabels={"Title": name})
        for k, v in kwargs.iteritems():
            if k == 'listProperties':
                for listPropertyKey, listPropertyValue in v.iteritems():
                    liz.setProperty(listPropertyKey, listPropertyValue)
            if k == 'listInfos':
                for listInfoKey, listInfoValue in v.iteritems():
                    liz.setInfo(listInfoKey, listInfoValue)
            if k == 'listArts':
                liz.setArt(v)
            if k == 'listCasts':
                try:liz.setCast(v)
                except:pass
            if k == 'contextMenu':
                menuItems = []
                for label, action in v.iteritems():
                    menuItems.append((label, action))
                if len(menuItems) > 0: liz.addContextMenuItems(menuItems)
        return control.addItem(handle=thisPlugin, url=u, listitem=liz, isFolder=isFolder)

    def generateActionUrl(self, url, mode, name=None, thumbnail='', page=1, query=''):
        url = '%s?url=%s&mode=%s' % (sysaddon, urllib.quote_plus(url), str(mode))
        try: 
            if name != None: url += '&name=%s' % urllib.quote_plus(name)
        except: 
            pass
        try: 
            if int(page) >= 0: url += '&page=%s' % str(page)
        except: 
            pass
        try: 
            if thumbnail != '': url += '&thumbnail=%s' % urllib.quote_plus(thumbnail)
        except: 
            pass    
        try: 
            if query != '': url += "&" + query
        except: 
            pass
        return logger.logDebug(url)

    def endDirectory(self, cacheToDisc=True):
        control.directory(int(sys.argv[1]), cacheToDisc=cacheToDisc)


