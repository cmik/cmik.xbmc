# -*- coding: utf-8 -*-

'''
    Tfc.tv Add-on
    Copyright (C) 2018 cmik
'''

from resources.lib.models import model
from resources.lib.libraries import control
from datetime import datetime
import time

logger = control.logger

class Episode(model.Model):
    
    def _getStructure(self, data):
        logger.logDebug(len(data))
        logger.logDebug(data)
        if len(data) == 18:
            try:
                dateaired = datetime.strptime(data[10], '%Y-%m-%d')
            except TypeError:
                dateaired = datetime(*(time.strptime(data[10], '%Y-%m-%d')[0:6]))
            return {
                'id' : int(data[0]), 
                'title' : data[1], 
                'parentid' : int(data[2]),
                'parentname' : data[3],
                'show' : data[3], 
                'image' : data[4], 
                'fanart' : data[5],
                'episodenumber' : data[6],
                'url' : data[7], 
                'description' : data[8],
                'shortdescription' : data[9],
                'dateaired' : dateaired.strftime('%b %d, %Y'),
                'date' : data[10],
                'year' : data[11],
                'parentalAdvisory' : data[12],
                'ltype' : data[13],
                'duration' : int(data[14]),
                'views' : int(data[15]),
                'rating' : int(data[16]),
                'votes' : int(data[17]),
                'type' : 'episode'
                }
        return {}
         
    def _retrieveAll(self):
        dbcur = self.getCursor()
        dbcur.execute(logger.logDebug("SELECT ID, \
            TITLE, \
            SHOWID, \
            SHOWNAME, \
            THUMBNAIL, \
            FANART, \
            EPISODENUMBER, \
            URL, \
            DESCRIPTION, \
            SHORTDESCRIPTION, \
            DATEAIRED, \
            YEAR, \
            PARENTALADVISORY, \
            TYPE, \
            DURATION, \
            VIEWS, \
            RATING, \
            VOTES \
            FROM EPISODE"))
        return logger.logDebug(dbcur.fetchall())
         
    def _retrieve(self, mixed):
        dbcur = self.getCursor()
        dbcur.execute(logger.logDebug("SELECT ID, \
            TITLE, \
            SHOWID, \
            SHOWNAME, \
            THUMBNAIL, \
            FANART, \
            EPISODENUMBER, \
            URL, \
            DESCRIPTION, \
            SHORTDESCRIPTION, \
            DATEAIRED, \
            YEAR, \
            PARENTALADVISORY, \
            TYPE, \
            DURATION, \
            VIEWS, \
            RATING, \
            VOTES \
            FROM EPISODE \
            WHERE ID IN (%s)" % ','.join(str(v) for v in mixed)))
        return logger.logDebug(dbcur.fetchall())

        
    def _save(self, mixed):
        ids = []
        for data in mixed:
            if 'id' in data:
                ids.append(str(data.get('id')))
        if len(ids) > 0:
            self.checkIfTableExists()
            dbcur = self.getCursor()
            dbcur.execute('PRAGMA encoding="UTF-8";')
            dbcur.execute(logger.logDebug("DELETE FROM EPISODE WHERE ID in (%s)" % ','.join(ids)))
            for data in mixed:
                dbcur.execute(logger.logDebug("INSERT INTO EPISODE VALUES (%d, '%s', %d, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', %d, %d, %d, %d)" % (
                    data.get('id'), 
                    data.get('title').replace('\'', '\'\''), 
                    data.get('parentid'), 
                    data.get('show').replace('\'', '\'\''), 
                    data.get('image'), 
                    data.get('fanart'), 
                    data.get('episodenumber'), 
                    data.get('url'), 
                    data.get('description').replace('\'', '\'\''), 
                    data.get('shortdescription').replace('\'', '\'\''), 
                    data.get('date'), 
                    data.get('year'), 
                    data.get('parentalAdvisory'), 
                    data.get('ltype'), 
                    data.get('duration', 0), 
                    data.get('views', 0), 
                    data.get('rating', 0), 
                    data.get('votes', 0))))
            return self._dbcon.commit()
        return False
        
    def _replace(self, mixed):
        ids = []
        for data in mixed:
            if 'id' in data:
                ids.append(str(data.get('id')))
        if len(ids) > 0:
            self.checkIfTableExists()
            dbcur = self.getCursor()
            dbcur.execute('PRAGMA encoding="UTF-8";')
            dbcur.execute(logger.logDebug("DELETE FROM EPISODE WHERE ID in (%s)" % ','.join(ids)))
            for data in mixed:
                dbcur.execute(logger.logDebug("INSERT INTO EPISODE VALUES (%d, '%s', %d, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', %d, %d, %d, %d)" % (
                    data.get('id'), 
                    data.get('title').replace('\'', '\'\''), 
                    data.get('parentid'), 
                    data.get('show').replace('\'', '\'\''), 
                    data.get('image'), 
                    data.get('fanart'), 
                    data.get('episodenumber'), 
                    data.get('url'), 
                    data.get('description').replace('\'', '\'\''), 
                    data.get('shortdescription').replace('\'', '\'\''), 
                    data.get('date'), 
                    data.get('year'), 
                    data.get('parentalAdvisory'), 
                    data.get('ltype'), 
                    data.get('duration', 0), 
                    data.get('views', 0), 
                    data.get('rating', 0), 
                    data.get('votes', 0))))
            return self._dbcon.commit()
        return False

    def _remove(self, mixed):
        ids = []
        logger.logDebug(mixed)
        for data in mixed:
            if 'id' in data:
                ids.append(str(data.get('id')))
        if len(ids) > 0:
            dbcur = self.getCursor()
            try: 
                dbcur.execute(logger.logDebug("DELETE FROM EPISODE WHERE ID in (%s)" % ','.join(ids)))
                return self._dbcon.commit()
            except: 
                return False

    def _drop(self):
        dbcur = self.getCursor()
        try: 
            dbcur.execute(logger.logDebug("DROP TABLE EPISODE"))
            return self._dbcon.commit()
        except: 
            return False

    def checkIfTableExists(self):
        dbcur = self.getCursor()
        dbcur.execute(logger.logDebug("CREATE TABLE IF NOT EXISTS EPISODE (\
            ID INTEGER PRIMARY KEY, \
            TITLE TEXT, \
            SHOWID INTEGER, \
            SHOWNAME TEXT, \
            THUMBNAIL TEXT, \
            FANART TEXT, \
            EPISODENUMBER TEXT, \
            URL TEXT, \
            DESCRIPTION TEXT, \
            SHORTDESCRIPTION TEXT, \
            DATEAIRED TEXT, \
            YEAR TEXT, \
            PARENTALADVISORY TEXT, \
            TYPE TEXT \
            DURATION INTEGER NOT NULL DEFAULT 0, \
            VIEWS INTEGER NOT NULL DEFAULT 0, \
            RATING INTEGER NOT NULL DEFAULT 0, \
            VOTES INTEGER NOT NULL DEFAULT 0)"))
        return self._dbcon.commit()
    

    def getStatistics(self):
        stats = {}
        dbcur = self.getCursor()
        dbcur.execute(logger.logDebug("SELECT COUNT(*) FROM EPISODE"))
        stats['count'] = dbcur.fetchone()
        return stats

