# -*- coding: utf-8 -*-

'''
    Tfc.tv Add-on
    Copyright (C) 2018 cmik
'''

import os,xbmcvfs
from resources import config
from resources.lib.libraries import control

common = control.common
logger = control.logger

def importShowDB():
    fileSource = logger.logInfo(control.browse(1, 'Select your shows DB file', 'files', '.db'))
    if (fileSource != ''):
        logger.logInfo(xbmcvfs.copy(fileSource, control.showsFile))
        control.showNotification(control.lang(57040), control.lang(50010))

def importEpisodeDB():
    fileSource = logger.logInfo(control.browse(1, 'Select your episodes DB file', 'files', '.db'))
    if (fileSource != ''):
        logger.logInfo(xbmcvfs.copy(fileSource, control.episodesFile))
        control.showNotification(control.lang(57040), control.lang(50010))

def importDBFiles():
    status = True
    try:
        dBImportURL = control.setting('databaseImportURL')
        
        # Shows DB file
        fileSource = dBImportURL + 'shows.db' 
        logger.logInfo('Copying %s to %s' % (fileSource, control.showsFile))
        status = True if status is True and logger.logInfo(xbmcvfs.copy(fileSource, control.showsFile)) != 0 else False

        # Episodes DB file
        fileSource = dBImportURL + 'episodes.db' 
        logger.logInfo('Copying %s to %s' % (fileSource, control.episodesFile))
        status = True if status is True and logger.logInfo(xbmcvfs.copy(fileSource, control.episodesFile)) != 0 else False
    except:
        status = False
        pass
    if status is True:
        control.setSetting('showUpdateCatalog', 'false')
        control.showNotification(control.lang(57003), control.lang(50010))
    else:
        control.showNotification(control.lang(57027), control.lang(50004))
    return status

def deleteDBFiles():
    status = True
    try:
        logger.logInfo('Deleting %s' % control.showsFile)
        status = True if status is True and logger.logInfo(xbmcvfs.delete(control.showsFile)) != 0 else False

        logger.logInfo('Deleting %s' % control.episodesFile)
        status = True if status is True and logger.logInfo(xbmcvfs.delete(control.episodesFile)) != 0 else False
    except:
        status = False
        pass
    return status

def checkInstallDB(refresh=False):
    control.showNotification(control.lang(50005))
    isInstalled = isDBInstalled()
    
    if refresh == True and isInstalled == True:
        deleteDBFiles()
    
    if refresh == True or isInstalled == False:
        # control.run(config.IMPORTALLDB, 'install')
        importDBFiles()

def isDBInstalled():
    if control.setting('showUpdateCatalog') == 'false' and os.path.exists(control.episodesFile) and os.path.exists(control.showsFile):
        return True
    return False
