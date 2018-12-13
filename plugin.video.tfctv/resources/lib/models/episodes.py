# -*- coding: utf-8 -*-

'''
    Tfc.tv Add-on
    Copyright (C) 2018 cmik
'''

from resources.lib.models import model
from resources.lib.libraries import control
from datetime import datetime

logger = control.logger

class Episode(model.Model):
    
    def _getStructure(self, data):
        logger.logDebug(len(data))
        if len(data) == 13:
            return {
                'id' : int(data[0]), 
                'title' : data[1], 
                'parentid' : data[2],
                'parentname' : data[3],
                'show' : data[3], 
                'image' : data[4], 
                'fanart' : data[5],
                'episodenumber' : data[6],
                'url' : data[7], 
                'description' : data[8],
                'shortdescription' : data[9],
                'dateaired' : datetime.strptime(data[10], '%Y-%m-%d').strftime('%b %d, %Y'),
                'date' : data[10],
                'year' : data[11],
                'parentalAdvisory' : data[12],
                'type' : 'episode'
                }
        return {}
         
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
            PARENTALADVISORY \
            FROM EPISODE \
            WHERE ID IN (%s)" % ','.join(str(v) for v in mixed)))
        return logger.logDebug(dbcur.fetchall())
        # return []
        
    def _save(self, mixed):
        ids = []
        for data in mixed:
            if 'id' in data:
                ids.append(str(data.get('id')))
        if len(ids) > 0:
            dbcur = self.getCursor()
            dbcur.execute('PRAGMA encoding="UTF-8";')
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
                PARENTALADVISORY TEXT)"))
            dbcur.execute(logger.logDebug("DELETE FROM EPISODE WHERE ID in (%s)" % ','.join(ids)))
            for data in mixed:
                dbcur.execute(logger.logDebug("INSERT INTO EPISODE VALUES (%d, '%s', %d, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (
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
                    data.get('parentalAdvisory'))))
            return self._dbcon.commit()
        return False

    def _remove(mixed):
        dbcur = self.getCursor()
        try: 
            dbcur.execute("DELETE FROM EPISODE WHERE id = '%s'" % (content, meta['imdb']))
            return self._dbcon.commit()
        except: 
            return False


