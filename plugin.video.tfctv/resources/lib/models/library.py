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

class Library(model.Model):
    
    def _getStructure(self, data):
        logger.logDebug(len(data))
        logger.logDebug(data)
        if len(data) == 6:
            try:
                date = datetime.strptime(data[4], '%Y-%m-%d')
            except TypeError:
                date = datetime(*(time.strptime(data[4], '%Y-%m-%d')[0:6]))
            try:
                lastCheck = datetime.strptime(data[5], '%Y-%m-%d %H:%M:%S')
            except TypeError:
                lastCheck = datetime(*(time.strptime(data[5], '%Y-%m-%d %H:%M:%S')[0:6]))
            return {
                'id' : int(data[0]), 
                'name' : data[1], 
                'parentid' : int(data[2]),
                'year' : data[3],
                'date' : date,
                'lastCheck' : lastCheck
                }
        return {}
      
    def _retrieveAll(self):
        dbcur = self.getCursor()
        dbcur.execute(logger.logDebug("SELECT ID, \
            NAME, \
            PARENTID, \
            YEAR, \
            DATE, \
            LASTCHECK \
            FROM LIBRARY_SHOW"))
        return logger.logDebug(dbcur.fetchall())
      
    def _retrieve(self, mixed):
        dbcur = self.getCursor()
        dbcur.execute(logger.logDebug("SELECT ID, \
            NAME, \
            PARENTID, \
            YEAR, \
            DATE, \
            LASTCHECK \
            FROM LIBRARY_SHOW \
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
            dbcur.execute(logger.logDebug("DELETE FROM LIBRARY_SHOW WHERE ID in (%s)" % ','.join(ids)))
            for data in mixed:
                dbcur.execute(logger.logDebug("INSERT INTO LIBRARY_SHOW VALUES (%d, '%s', %d, '%s', '%s', '%s')" % (
                    data.get('id'), 
                    data.get('name').replace('\'', '\'\''), 
                    data.get('parentid'),
                    data.get('year'), 
                    data.get('date'), 
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))
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
            dbcur.execute(logger.logDebug("DELETE FROM LIBRARY_SHOW WHERE ID in (%s)" % ','.join(ids)))
            for data in mixed:
                dbcur.execute(logger.logDebug("INSERT INTO LIBRARY_SHOW VALUES (%d, '%s', %d, '%s', '%s', '%s')" % (
                    data.get('id'), 
                    data.get('name').replace('\'', '\'\''), 
                    data.get('parentid'),
                    data.get('year'), 
                    data.get('date'), 
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))
            return self._dbcon.commit()
        return False

    def _remove(self, mixed):
        dbcur = self.getCursor()
        try: 
            dbcur.execute("DELETE FROM LIBRARY_SHOW WHERE id = '%s'" % (content, meta['imdb']))
            return self._dbcon.commit()
        except: 
            return False

    def _drop(self):
        dbcur = self.getCursor()
        try: 
            dbcur.execute(logger.logDebug("DROP TABLE LIBRARY_SHOW"))
            return self._dbcon.commit()
        except: 
            return False

    def checkIfTableExists(self):
        dbcur = self.getCursor()
        dbcur.execute(logger.logDebug("CREATE TABLE IF NOT EXISTS LIBRARY_SHOW (\
            ID INTEGER PRIMARY KEY, \
            NAME TEXT, \
            PARENTID INTEGER, \
            YEAR TEXT, \
            DATE TEXT, \
            LASTCHECK TEXT)"))
        return self._dbcon.commit()

    def getStatistics(self):
        stats = {}
        dbcur = self.getCursor()
        dbcur.execute(logger.logDebug("SELECT COUNT(*) FROM LIBRARY_SHOW"))
        stats['count'] = dbcur.fetchone()
        return stats

