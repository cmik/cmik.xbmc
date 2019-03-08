# -*- coding: utf-8 -*-

'''
    Tfc.tv Add-on
    Copyright (C) 2018 cmik
'''

from resources import config
from resources.lib.libraries import control
from resources.lib.libraries import tools
from resources.lib.models import episodes
from resources.lib.models import shows
from resources.lib.models import library

logger = control.logger

def upgradeDB():

    # Load DB

    # DB upgrades per version
    if control.setting('lastVersion') == '1.0.0-beta' and control.addonInfo('version') == '1.0.0':
        episodeDB = episodes.Episode(control.episodesFile)
        showDB = shows.Show(control.showsFile)
        libraryDB = library.Library(control.libraryFile)

        control.showNotification('Upgrading databases...', control.lang(50002))
        logger.logDebug(episodeDB.upgrade([
            'ALTER TABLE `EPISODE` ADD COLUMN `TYPE` TEXT',
            'UPDATE `EPISODE` SET TYPE = \'episode\' WHERE TYPE IS NULL']))
        logger.logDebug(showDB.upgrade([
            'ALTER TABLE `SHOW` ADD COLUMN `TYPE` TEXT',
            'UPDATE `SHOW` SET TYPE = \'show\' WHERE TYPE IS NULL']))

    elif control.setting('lastVersion') in ('1.0.0', '1.0.1') and control.addonInfo('version') == '1.1.0':
        # Check if installation is complete
        logger.logNotice('Checking installation')
        tools.checkInstallDB(True)