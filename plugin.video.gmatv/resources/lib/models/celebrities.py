# -*- coding: utf-8 -*-

'''
    GMA.tv Add-on
    Copyright (C) 2020 cmik
'''

from resources.lib.models import model
from resources.lib.libraries import control

logger = control.logger

class Actor(model.Model):
    
    def _getStructure(self, data):
        logger.logDebug(len(data))
        logger.logDebug(data)
        if len(data) == 13:
            return {
                'id' : int(data[0]),
                'name' : data[1],
                'thumbnail' : data[2],
                'fanart' : data[3],
                'banner' : data[4],
                'url' : data[5],
                'description' : data[6],
                'birthday' : data[7],
                'birthplace' : data[8]
                }
        return {}
         
    def _retrieveAll(self):
        dbcur = self.getCursor()
        dbcur.execute(logger.logDebug("SELECT ID, \
            NAME, \
            THUMBNAIL, \
            FANART, \
            BANNER, \
            URL, \
            DESCRIPTION, \
            BIRTHDAY, \
            BIRTHPLACE \
            FROM ACTOR"))
        return logger.logDebug(dbcur.fetchall())
         
    def _retrieve(self, mixed, key):
        dbcur = self.getCursor()
        dbcur.execute(logger.logDebug("SELECT ID, \
            NAME, \
            THUMBNAIL, \
            FANART, \
            BANNER, \
            URL, \
            DESCRIPTION, \
            BIRTHDAY, \
            BIRTHPLACE \
            FROM ACTOR \
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
                    query = "UPDATE ACTOR SET "
                    query += "NAME = '%s', " % data.get('name') if data.get('name', False) else "NAME = NAME, "
                    query += "THUMBNAIL = '%s', " % data.get('logo') if data.get('logo', False) else "THUMBNAIL = THUMBNAIL, "
                    query += "FANART = '%s', " % data.get('image') if data.get('image', False) else "FANART = FANART, "
                    query += "BANNER = '%s', " % data.get('banner') if data.get('banner', False) else "BANNER = BANNER, "
                    query += "URL = '%s', " % data.get('url') if data.get('url', False) else "URL = URL, "
                    query += "DESCRIPTION = '%s', " % data.get('description') if data.get('description', False) else "DESCRIPTION = DESCRIPTION, "
                    query += "BIRTHDAY = '%s', " % data.get('birthday') if data.get('birthday', False) else "BIRTHDAY = BIRTHDAY, "
                    query += "BIRTHPLACE = '%s', " % data.get('birthplace') if data.get('birthplace', False) else "BIRTHPLACE = BIRTHPLACE "
                    query += "WHERE ID = %d" % data.get('id')
                    dbcur.execute(logger.logDebug(query))
        self._dbcon.commit()
        return True

    def _replace(self, mixed):
        logger.logDebug(mixed)
        ids = [str(data['id']) for data in mixed if 'id' in data]
        if len(ids) > 0:
            self.checkIfTableExists()
            dbcur = self.getCursor()
            dbcur.execute('PRAGMA encoding="UTF-8";')
            dbcur.execute(logger.logDebug("DELETE FROM ACTOR WHERE ID in (%s)" % ','.join(ids)))
            for data in mixed:
                dbcur.execute(logger.logDebug("INSERT INTO ACTOR VALUES (%d, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (
                    data.get('id'), 
                    data.get('name').replace('\'', '\'\''), 
                    data.get('thumbnail').replace('&#39;', '\'\''), 
                    data.get('fanart').replace('&#39;', '\'\''), 
                    data.get('banner').replace('&#39;', '\'\''), 
                    data.get('url'), 
                    data.get('description').replace('\'', '\'\''), 
                    data.get('birthday'), 
                    data.get('birthplace'))))
            self._dbcon.commit()
            return True
        return False

    def _remove(self, mixed):
        logger.logDebug(mixed)
        ids = [str(data['id']) for data in mixed if 'id' in data]
        if len(ids) > 0:
            dbcur = self.getCursor()
            try: 
                dbcur.execute(logger.logDebug("DELETE FROM ACTOR WHERE ID in (%s)" % ','.join(ids)))
                self._dbcon.commit()
                return True
            except: pass
        return False

    def _drop(self):
        dbcur = self.getCursor()
        try: 
            dbcur.execute(logger.logDebug("DROP TABLE ACTOR"))
            self._dbcon.commit()
            return True
        except: 
            return False

    def checkIfTableExists(self):
        dbcur = self.getCursor()
        dbcur.execute(logger.logDebug("CREATE TABLE IF NOT EXISTS ACTOR (\
            ID INTEGER PRIMARY KEY, \
            NAME TEXT, \
            THUMBNAIL TEXT, \
            FANART TEXT, \
            BANNER TEXT, \
            URL TEXT, \
            DESCRIPTION TEXT, \
            BIRTHDAY TEXT, \
            BIRTHPLACE TEXT)"))
        return self._dbcon.commit()
            
    def getStatistics(self):
        stats = {}
        dbcur = self.getCursor()
        dbcur.execute(logger.logDebug("SELECT COUNT(*) FROM ACTOR"))
        stats['count'] = dbcur.fetchone()
        return stats