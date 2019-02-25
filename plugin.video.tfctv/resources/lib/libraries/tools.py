# -*- coding: utf-8 -*-

'''
    Tfc.tv Add-on
    Copyright (C) 2018 cmik
'''

import xbmcvfs
from resources.lib.libraries import control

common = control.common
logger = control.logger

def importShowDB():
    import xbmcvfs
    fileSource = logger.logInfo(control.browse(1, 'Select your shows DB file', 'files', '.db'))
    if (fileSource != ''):
        logger.logInfo(xbmcvfs.copy(fileSource, control.showsFile))
        control.showNotification(control.lang(57040), control.lang(50010))

def importEpisodeDB():
    import xbmcvfs
    fileSource = logger.logInfo(control.browse(1, 'Select your episodes DB file', 'files', '.db'))
    if (fileSource != ''):
        logger.logInfo(xbmcvfs.copy(fileSource, control.episodesFile))
        control.showNotification(control.lang(57040), control.lang(50010))

def importDBFiles():
    import xbmcvfs
    status = True
    try:
        dBImportURL = control.setting('databaseImportURL')
        # Show DB file
        fileSource = dBImportURL + 'shows.db' 
        status = True if status is True and logger.logInfo(xbmcvfs.copy(fileSource, control.episodesFile)) != 0 else False
        fileSource = dBImportURL + 'episodes.db' 
        status = True if status is True and logger.logInfo(xbmcvfs.copy(fileSource, control.episodesFile)) != 0 else False
    except:
        status = False
    if status is True:
        control.setSetting('showUpdateCatalog', 'false')
        control.showNotification(control.lang(57003), control.lang(50010))
    else:
        control.showNotification(control.lang(57027), control.lang(50004))
    return status
