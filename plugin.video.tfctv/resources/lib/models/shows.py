# -*- coding: utf-8 -*-

'''
    Tfc.tv Add-on
    Copyright (C) 2018 cmik
'''

from resources.lib.models import model
from resources.lib.libraries import control

logger = control.logger

class Show(model.Model):
    
    def _getStructure(self, data):
        logger.logDebug(len(data))
        logger.logDebug(data)
        if len(data) == 13:
            return {
                'id' : int(data[0]),
                'name' : data[1],
                'parentid' : data[2],
                'parentname' : data[3],
                'logo' : data[4],
                'image' : data[5],
                'fanart' : data[6],
                'banner' : data[7],
                'url' : data[8],
                'description' : data[9],
                'shortdescription' : data[10],
                'year' : data[11],
                'ltype' : data[12],
                'type' : 'show'
                }
        return {}
         
    def _retrieveAll(self):
        dbcur = self.getCursor()
        dbcur.execute(logger.logDebug("SELECT ID, \
            TITLE, \
            PARENTID, \
            PARENTNAME, \
            THUMBNAIL, \
            IMAGE, \
            FANART, \
            BANNER, \
            URL, \
            DESCRIPTION, \
            SHORTDESCRIPTION, \
            YEAR, \
            TYPE \
            FROM SHOW"))
        return logger.logDebug(dbcur.fetchall())
         
    def _retrieve(self, mixed):
        dbcur = self.getCursor()
        dbcur.execute(logger.logDebug("SELECT ID, \
            TITLE, \
            PARENTID, \
            PARENTNAME, \
            THUMBNAIL, \
            IMAGE, \
            FANART, \
            BANNER, \
            URL, \
            DESCRIPTION, \
            SHORTDESCRIPTION, \
            YEAR, \
            TYPE \
            FROM SHOW \
            WHERE ID IN (%s)" % ','.join(str(v) for v in mixed)))
        return logger.logDebug(dbcur.fetchall())
        
    def _save(self, mixed):
        ids = []
        logger.logDebug(mixed)
        for data in mixed:
            if 'id' in data:
                ids.append(str(data.get('id')))
        if len(ids) > 0:
            dbcur = self.getCursor()
            dbcur.execute('PRAGMA encoding="UTF-8";')
            dbcur.execute(logger.logDebug("CREATE TABLE IF NOT EXISTS SHOW (\
                ID INTEGER PRIMARY KEY, \
                TITLE TEXT, \
                PARENTID INTEGER, \
                PARENTNAME TEXT, \
                THUMBNAIL TEXT, \
                IMAGE TEXT, \
                FANART TEXT, \
                BANNER TEXT, \
                URL TEXT, \
                DESCRIPTION TEXT, \
                SHORTDESCRIPTION TEXT, \
                YEAR TEXT, \
                TYPE TEXT)"))
            dbcur.execute(logger.logDebug("DELETE FROM SHOW WHERE ID in (%s)" % ','.join(ids)))
            for data in mixed:
                dbcur.execute(logger.logDebug("INSERT INTO SHOW VALUES (%d, '%s', %d, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (
                    data.get('id'), 
                    data.get('name').replace('\'', '\'\''), 
                    data.get('parentid'), 
                    data.get('parentname').replace('\'', '\'\''), 
                    data.get('logo'), 
                    data.get('image'), 
                    data.get('fanart'), 
                    data.get('banner'), 
                    data.get('url'), 
                    data.get('description').replace('\'', '\'\''), 
                    data.get('shortdescription').replace('\'', '\'\''), 
                    data.get('year'), 
                    data.get('ltype'))))
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
                dbcur.execute(logger.logDebug("DELETE FROM SHOW WHERE ID in (%s)" % ','.join(ids)))
                return self._dbcon.commit()
            except: 
                return False

    def _drop(self):
        dbcur = self.getCursor()
        try: 
            dbcur.execute(logger.logDebug("DROP TABLE SHOW"))
            return self._dbcon.commit()
        except: 
            return False
            
    def getStatistics(self):
        stats = {}
        dbcur = self.getCursor()
        dbcur.execute(logger.logDebug("SELECT COUNT(*) FROM SHOW"))
        stats['count'] = dbcur.fetchone()
        return stats


