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

    logger.logNotice('Updating from version %s to %s' % (control.setting('lastVersion'), control.addonInfo('version')))

    if control.setting('lastVersion') in ('', '0.1.0', '0.2.0'):
        # Check if installation is complete
        logger.logNotice('Checking installation')
        tools.checkInstallDB(True)

    tools.checkInstallDB()
    episodeDB = episodes.Episode(control.episodesFile)
    showDB = shows.Show(control.showsFile)
    showViews = logger.logInfo(episodeDB.execute(['select showid, sum(views) from EPISODE where views > 0 group by showid']))
    updateQueries = []
    if (showViews and len(showViews) > 0):
        for data in showViews[0]:
            updateQueries.append('UPDATE SHOW SET VIEWS = %d WHERE ID = %d' % (int(data[1]), int(data[0])))
        showDB.executeUpdate(logger.logInfo(updateQueries))
        