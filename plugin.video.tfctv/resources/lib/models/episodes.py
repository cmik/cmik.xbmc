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
    
    def _search(self, search, limit):
        dbcur = self.getCursor()
        where = ["%s LIKE '%%%s%%'" % (str(k), str(v)) for k,v in search.iteritems()]
        first = 'LIMIT %d' % int(limit) if limit != False else ''
        dbcur.execute(logger.logInfo("SELECT ID, \
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
            WHERE %s %s" % (' AND '.join(where), first)))
        return logger.logDebug(dbcur.fetchall())

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
         
    def _retrieve(self, mixed, key):
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
            WHERE %s IN (%s)" % (key, ','.join(str(v) for v in mixed))))
        return logger.logDebug(dbcur.fetchall())

        
    def _save(self, mixed):
        logger.logDebug(mixed)
        self.checkIfTableExists()
        for data in mixed:
            if 'id' in data:
                dbcur = self.getCursor()
                dbcur.execute('PRAGMA encoding="UTF-8";')
                for k, e in data.iteritems():
                    query = "UPDATE EPISODE SET "
                    query += "TITLE = '%s', " % data.get('name') if data.get('name', False) else "TITLE = TITLE, "
                    query += "SHOWID = '%s', " % data.get('parentid') if data.get('parentid', False) else "SHOWID = SHOWID, "
                    query += "SHOWNAME = '%s', " % data.get('show') if data.get('show', False) else "SHOWNAME = SHOWNAME, "
                    query += "THUMBNAIL = '%s', " % data.get('image') if data.get('image', False) else "THUMBNAIL = THUMBNAIL, "
                    query += "FANART = '%s', " % data.get('fanart') if data.get('fanart', False) else "FANART = FANART, "
                    query += "EPISODENUMBER = '%s', " % data.get('episodenumber') if data.get('episodenumber', False) else "EPISODENUMBER = EPISODENUMBER, "
                    query += "URL = '%s', " % data.get('url') if data.get('url', False) else "URL = URL, "
                    query += "DESCRIPTION = '%s', " % data.get('description') if data.get('description', False) else "DESCRIPTION = DESCRIPTION, "
                    query += "SHORTDESCRIPTION = '%s', " % data.get('shortdescription') if data.get('shortdescription', False) else "SHORTDESCRIPTION = SHORTDESCRIPTION, "
                    query += "DATEAIRED = '%s', " % data.get('date') if data.get('date', False) else "DATEAIRED = DATEAIRED, "
                    query += "YEAR = '%s', " % data.get('year') if data.get('year', False) else "YEAR = YEAR, "
                    query += "PARENTALADVISORY = '%s', " % data.get('parentalAdvisory') if data.get('parentalAdvisory', False) else "PARENTALADVISORY = PARENTALADVISORY, "
                    query += "TYPE = '%s', " % data.get('ltype') if data.get('ltype', False) else "TYPE = TYPE, "
                    query += "DURATION = %d, " % data.get('duration') if data.get('duration', False) else "DURATION = DURATION, "
                    query += "VIEWS = %d, " % data.get('views') if data.get('views', False) else "VIEWS = VIEWS, "
                    query += "RATING = %d, " % data.get('rating') if data.get('rating', False) else "RATING = RATING, "
                    query += "VOTES = %d " % data.get('votes') if data.get('votes', False) else "VOTES = VOTES "
                    query += "WHERE ID = %d" % data.get('id')
                    dbcur.execute(logger.logDebug(query))
        self._dbcon.commit()
        return True
        
    def _replace(self, mixed):
        ids = [str(data['id']) for data in mixed if 'id' in data]
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
                    data.get('image').replace('&#39;', '\'\''), 
                    data.get('fanart').replace('&#39;', '\'\''), 
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
            self._dbcon.commit()
            return True
        return False

    def _remove(self, mixed):
        logger.logDebug(mixed)
        ids = [str(data['id']) for data in mixed if 'id' in data]
        if len(ids) > 0:
            dbcur = self.getCursor()
            try: 
                dbcur.execute(logger.logDebug("DELETE FROM EPISODE WHERE ID in (%s)" % ','.join(ids)))
                self._dbcon.commit()
                return True
            except: pass
        return False

    def _drop(self):
        dbcur = self.getCursor()
        try: 
            dbcur.execute(logger.logDebug("DROP TABLE EPISODE"))
            self._dbcon.commit()
            return True
        except: 
            return False

    def searchByTitle(self, title, limit=100):
        return self.search({'TITLE' : title}, limit)

    def searchByDate(self, date, limit=100):
        return self.search({'DATEAIRED' : date}, limit)

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
        self._dbcon.commit()
        return True
    

    def getStatistics(self):
        stats = {}
        dbcur = self.getCursor()
        dbcur.execute(logger.logDebug("SELECT COUNT(*) FROM EPISODE"))
        stats['count'] = dbcur.fetchone()
        return stats

