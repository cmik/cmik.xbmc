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
        logger.logDebug(episodeDB.executeUpdate([
            'ALTER TABLE `EPISODE` ADD COLUMN `TYPE` TEXT',
            'UPDATE `EPISODE` SET TYPE = \'episode\' WHERE TYPE IS NULL']))
        logger.logDebug(showDB.executeUpdate([
            'ALTER TABLE `SHOW` ADD COLUMN `TYPE` TEXT',
            'UPDATE `SHOW` SET TYPE = \'show\' WHERE TYPE IS NULL']))

    elif control.setting('lastVersion') in ('1.0.0', '1.0.1', '1.1.0', '1.2.0') and control.addonInfo('version') == '1.2.1':
        # Check if installation is complete
        logger.logNotice('Checking installation')
        tools.checkInstallDB(True)
    elif control.addonInfo('version') == '1.2.3':
        logger.logNotice('Updating version 1.2.3')
        episodeDB = episodes.Episode(control.episodesFile)
        showDB = shows.Show(control.showsFile)
        showViews = logger.logInfo(episodeDB.execute(['select showid, sum(views) from EPISODE where views > 0 group by showid']))
        updateQueries = []
        for data in showViews[0]:
            updateQueries.append('UPDATE SHOW SET VIEWS = %d WHERE ID = %d' % (int(data[1]), int(data[0])))
        showDB.executeUpdate(logger.logInfo(updateQueries))


        