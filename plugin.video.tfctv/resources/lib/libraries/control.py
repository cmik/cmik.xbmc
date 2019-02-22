# -*- coding: utf-8 -*-

'''
    Tfc.tv Add-on
    Copyright (C) 2016 cmik

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


import os,xbmc,xbmcaddon,xbmcplugin,xbmcgui,xbmcvfs
import CommonFunctions as common
from resources.lib.libraries import logger

lang = xbmcaddon.Addon().getLocalizedString

setting = xbmcaddon.Addon().getSetting

setSetting = xbmcaddon.Addon().setSetting

addon = xbmcaddon.Addon

addItem = xbmcplugin.addDirectoryItem

item = xbmcgui.ListItem

directory = xbmcplugin.endOfDirectory

content = xbmcplugin.setContent

property = xbmcplugin.setProperty

addonInfo = xbmcaddon.Addon().getAddonInfo

logger.plugin = addonInfo('name')

infoLabel = xbmc.getInfoLabel

condVisibility = xbmc.getCondVisibility

jsonrpc = xbmc.executeJSONRPC

window = xbmcgui.Window(10000)

dialog = xbmcgui.Dialog()

progressDialog = xbmcgui.DialogProgress()

windowDialog = xbmcgui.WindowDialog()

button = xbmcgui.ControlButton

image = xbmcgui.ControlImage

keyboard = xbmc.Keyboard

sleep = xbmc.sleep

execute = xbmc.executebuiltin

skin = xbmc.getSkinDir()

player = xbmc.Player()

playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)

resolve = xbmcplugin.setResolvedUrl

openFile = xbmcvfs.File

makeFile = xbmcvfs.mkdir

makePath = xbmcvfs.mkdirs

deleteFile = xbmcvfs.delete

listDir = xbmcvfs.listdir

transPath = xbmc.translatePath

skinPath = xbmc.translatePath('special://skin/')

addonPath = xbmc.translatePath(addonInfo('path'))

dataPath = xbmc.translatePath(addonInfo('profile')).decode('utf-8')

homePath = xbmc.translatePath('special://home')

settingsFile = os.path.join(dataPath, 'settings.xml')

libraryFile = os.path.join(dataPath, 'library.db')

categoriesFile = os.path.join(dataPath, 'categories.db')

showsFile = os.path.join(dataPath, 'shows.db')

episodesFile = os.path.join(dataPath, 'episodes.db')

celebritiesFile = os.path.join(dataPath, 'celebrities.db')

favouritesFile = os.path.join(dataPath, 'favourites.db')

sourcescacheFile = os.path.join(dataPath, 'sources.db')

libcacheFile = os.path.join(dataPath, 'library.db')

if setting('exportLibraryPath') != '' and os.path.exists(setting('exportLibraryPath')): 
    libraryPath = setting('exportLibraryPath')
else: 
    libraryPath = os.path.join(dataPath, 'library')

showsLibPath = os.path.join(libraryPath, 'shows')

moviesLibPath = os.path.join(libraryPath, 'movies')


def addonFolderIcon(text):
    appearance = setting('appearance').lower()
    if appearance in ['-', '']: return addonInfo('icon')
    else: return os.path.join(addonPath, 'resources', 'media', appearance, 'icon_%s.jpg' % (text.lower()[:1]))
    
            
def addonIcon():
    appearance = setting('appearance').lower()
    if appearance in ['-', '']: return addonInfo('icon')
    else: return os.path.join(addonPath, 'resources', 'media', appearance, 'icon.png')


def addonPoster():
    appearance = setting('appearance').lower()
    if appearance in ['-', '']: return 'DefaultVideo.png'
    else: return os.path.join(addonPath, 'resources', 'media', appearance, 'poster.png')


def addonBanner():
    appearance = setting('appearance').lower()
    if appearance in ['-', '']: return 'DefaultVideo.png'
    else: return os.path.join(addonPath, 'resources', 'media', appearance, 'banner.png')


def addonThumb():
    appearance = setting('appearance').lower()
    if appearance == '-': return 'DefaultFolder.png'
    elif appearance == '': return addonInfo('icon')
    else: return os.path.join(addonPath, 'resources', 'media', appearance, 'icon.png')


def addonFanart():
    appearance = setting('appearance').lower()
    if appearance == '-': return None
    elif appearance == '': return addonInfo('fanart')
    else: return os.path.join(addonPath, 'resources', 'media', appearance, 'fanart.jpg')


def addonNext():
    appearance = setting('appearance').lower()
    if appearance in ['-', '']: return 'DefaultFolderBack.png'
    else: return os.path.join(addonPath, 'resources', 'media', appearance, 'next.jpg')


def artPath():
    appearance = setting('appearance').lower()
    if appearance in ['-', '']: return None
    else: return os.path.join(addonPath, 'resources', 'media', appearance)


def infoDialog(message, heading=addonInfo('name'), icon=addonIcon(), time=3000):
    try: dialog.notification(heading, message, icon, time, sound=False)
    except: execute("Notification(%s, %s, %s, %s)" % (heading, message, time, icon))


def yesnoDialog(line1, line2, line3, heading=addonInfo('name'), nolabel='', yeslabel=''):
    return dialog.yesno(heading, line1, line2, line3, nolabel, yeslabel)


def selectDialog(list, heading=addonInfo('name')):
    return dialog.select(heading, list)

    
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
    return yesnoDialog(message, line1, line2, title)  
    
def numpad(message, default=''):
    if not message:
        return
    return dialog.numeric(0, message, default)
    
def alert(message, line1='', line2='', title=lang(50001)):
    if not message:
        return
    return dialog.ok(title, message, line1, line2)
    
def browse(type, title, shares='files', mask='', useThumbs=False, treatAsFolder=False, defaultt='', enableMultiple=False):
    return dialog.browse(type, title, shares, mask, useThumbs, treatAsFolder, defaultt, enableMultiple)

def inputText(title, defaultValue=''):
    return dialog.input(title, defaultValue, xbmcgui.INPUT_ALPHANUM)
    
def inputPassword(title, defaultValue=''):
    return dialog.input(title, defaultValue, xbmcgui.INPUT_ALPHANUM, xbmcgui.ALPHANUM_HIDE_INPUT)
    
def showNotification(message, title=lang(50001), time=3000):
    infoDialog(message, title, addonIcon(), time)
    # xbmc.executebuiltin('Notification(%s, %s)' % (title, message))

def version():
    num = ''
    try: version = addon('xbmc.addon').getAddonInfo('version')
    except: version = '999'
    for i in version:
        if i.isdigit(): num += i
        else: break
    return int(num)


def run(mode, caller='addon'):
    return execute('RunPlugin(plugin://%s/?mode=%s&caller=%s)' % (addonInfo('id'), mode, caller))

def exit():
    return execute("XBMC.Container.Update(path,replace)")

def refresh():
    return execute('Container.Refresh')

def loading():
    return execute("ActivateWindow(busydialog)")
    
def idle():
    return execute('Dialog.Close(busydialog)')

def queueItem():
    return execute('Action(Queue)')

def openPlaylist():
    return execute('ActivateWindow(VideoPlaylist)')

def openSettings(query=None, id=addonInfo('id')):
    try:
        idle()
        execute('Addon.OpenSettings(%s)' % id)
        if query == None: raise Exception()
        c, f = query.split('.')
        execute('SetFocus(%i)' % (int(c) + 100))
        execute('SetFocus(%i)' % (int(f) + 200))
    except:
        return
    
def readFile(filePath):
    if os.path.exists(filePath):
        with open(filePath) as f:
            content = f.read()
            f.close()
            return content
    return False
    
def writeFile(filePath, content):
    with open(filePath, 'w') as f:
        f.write(content)
        f.close()
    if os.path.exists(filePath):
        return True
    return False
