# -*- coding: utf-8 -*-

'''
    GMA.tv Add-on
    Copyright (C) 2020 cmik
'''

from resources.lib.models import model
from resources.lib.libraries import control

logger = control.logger

class ShowCast(model.Model):
    
    idFormat = '%d-%d'

    def _getStructure(self, data):
        logger.logDebug(len(data))
        logger.logDebug(data)
        if len(data) == 8:
            return {
                'id' : data[0],
                'showid' : int(data[1]),
                'actorid' : int(data[2]),
                'name' : data[3],
                'role' : data[4],
                'thumbnail' : data[5],
                'order' : data[6],
                'castUrl' : data[7]
                }
        return {}
    
    def _search(self, search, limit):
        dbcur = self.getCursor()
        where = ["%s LIKE '%%%s%%'" % (str(k), str(v)) for k,v in search.iteritems()]
        first = 'LIMIT %d' % int(limit) if limit != False else ''
        dbcur.execute(logger.logDebug("SELECT ID, \
            SHOWID, \
            ACTORID, \
            NAME, \
            ROLE, \
            THUMBNAIL, \
            ORDR, \
            URL \
            FROM SHOW_CAST \
            WHERE %s %s" % (' AND '.join(where), first)))
        return logger.logDebug(dbcur.fetchall())

    def _retrieveAll(self):
        dbcur = self.getCursor()
        dbcur.execute(logger.logDebug("SELECT ID, \
            SHOWID, \
            ACTORID, \
            NAME, \
            ROLE, \
            THUMBNAIL, \
            ORDR, \
            URL \
            FROM SHOW_CAST"))
        return logger.logDebug(dbcur.fetchall())
         
    def _retrieve(self, mixed, key):
        dbcur = self.getCursor()
        dbcur.execute(logger.logDebug("SELECT ID, \
            SHOWID, \
            ACTORID, \
            NAME, \
            ROLE, \
            THUMBNAIL, \
            ORDR, \
            URL \
            FROM SHOW_CAST \
            WHERE %s IN (%s)" % (key, ','.join(str(v) for v in mixed))))
        return logger.logDebug(dbcur.fetchall())

    def _save(self, mixed):
        logger.logDebug(mixed)
        self.checkIfTableExists()
        for data in mixed:
            if 'id' in data or ('showid' in data and 'castid' in data):
                dbcur = self.getCursor()
                dbcur.execute('PRAGMA encoding="UTF-8";')
                for k, e in data.iteritems():
                    query = "UPDATE SHOW_CAST SET "
                    query += "SHOWID = %d, " % data.get('showid') if data.get('showid', False) else "SHOWID = SHOWID, "
                    query += "ACTORID = %d, " % data.get('castid') if data.get('castid', False) else "ACTORID = ACTORID, "
                    query += "NAME = '%s', " % data.get('name') if data.get('name', False) else "NAME = NAME, "
                    query += "ROLE = '%s', " % data.get('role') if data.get('role', False) else "ROLE = ROLE, "
                    query += "THUMBNAIL = '%s', " % data.get('thumbnail') if data.get('thumbnail', False) else "THUMBNAIL = THUMBNAIL, "
                    query += "ORDR = %d, " % data.get('order') if data.get('order', False) else "ORDR = ORDR, "
                    query += "URL = '%s', " % data.get('url') if data.get('url', False) else "URL = URL "
                    query += "WHERE ID = '%s'" % data.get('id', self.idFormat % (data.get('showid'), data.get('castid')))
                    dbcur.execute(logger.logDebug(query))
        self._dbcon.commit()
        return True

    def _replace(self, mixed):
        logger.logDebug(mixed)
        ids = [str(data.get('id', self.idFormat % (data.get('showid'), data.get('castid')))) for data in mixed if 'id' in data or ('showid' in data and 'castid' in data)]
        if len(ids) > 0:
            self.checkIfTableExists()
            dbcur = self.getCursor()
            dbcur.execute('PRAGMA encoding="UTF-8";')
            dbcur.execute(logger.logDebug("DELETE FROM SHOW_CAST WHERE ID in ('%s')" % "','".join(ids)))
            for data in mixed:
                dbcur.execute(logger.logDebug("INSERT INTO SHOW_CAST VALUES ('%s', %d, %d, '%s', '%s', '%s', %d, '%s')" % (
                    data.get('id', self.idFormat % (data.get('showid'), data.get('castid'))), 
                    data.get('showid'), 
                    data.get('castid'), 
                    data.get('name').replace('\'', '\'\''), 
                    data.get('role').replace('\'', '\'\''), 
                    data.get('thumbnail').replace('&#39;', '\'\''), 
                    data.get('order'), 
                    data.get('url'))))
            self._dbcon.commit()
            return True
        return False

    def _remove(self, mixed):
        logger.logDebug(mixed)
        ids = [str(data.get('id', self.idFormat % (data.get('showid'), data.get('castid')))) for data in mixed if 'id' in data or ('showid' in data and 'castid' in data)]
        if len(ids) > 0:
            dbcur = self.getCursor()
            try: 
                dbcur.execute(logger.logDebug("DELETE FROM SHOW_CAST WHERE ID in ('%s')" % "','".join(ids)))
                self._dbcon.commit()
                return True
            except: pass
        return False

    def _drop(self):
        dbcur = self.getCursor()
        try: 
            dbcur.execute(logger.logDebug("DROP TABLE SHOW_CAST"))
            self._dbcon.commit()
            return True
        except: 
            return False

    def getByShow(self, mixed, limit=100):
        return self.get(mixed, 'SHOWID')

    def searchByActorName(self, name, limit=100):
        return self.search({'NAME' : name})

    def checkIfTableExists(self):
        dbcur = self.getCursor()
        dbcur.execute(logger.logDebug("CREATE TABLE IF NOT EXISTS SHOW_CAST (\
            ID TEXT PRIMARY KEY, \
            SHOWID INTEGER, \
            ACTORID INTEGER, \
            NAME TEXT, \
            ROLE TEXT, \
            THUMBNAIL TEXT, \
            ORDR INTEGER, \
            URL TEXT)"))
        return self._dbcon.commit()
            
    def getStatistics(self):
        stats = {}
        dbcur = self.getCursor()
        dbcur.execute(logger.logDebug("SELECT COUNT(*) FROM SHOW_CAST"))
        stats['count'] = dbcur.fetchone()
        return stats