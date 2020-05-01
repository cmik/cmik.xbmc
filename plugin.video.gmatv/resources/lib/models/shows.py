# -*- coding: utf-8 -*-

'''
    GMA.tv Add-on
    Copyright (C) 2020 cmik
'''

from resources.lib.models import model
from resources.lib.libraries import control

logger = control.logger

class Show(model.Model):
    
    def _getStructure(self, data):
        logger.logDebug(len(data))
        logger.logDebug(data)
        if len(data) == 17:
            return {
                'id' : int(data[0]),
                'name' : data[1],
                'parentid' : int(data[2]),
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
                'duration' : int(data[13]),
                'views' : int(data[14]),
                'rating' : int(data[15]),
                'votes' : int(data[16]),
                'type' : 'show'
                }
        return {}
    
    def _search(self, search, limit):
        dbcur = self.getCursor()
        where = ["%s LIKE '%%%s%%'" % (str(k), str(v)) for k,v in search.iteritems()]
        first = 'LIMIT %d' % int(limit) if limit != False else ''
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
            TYPE, \
            DURATION, \
            VIEWS, \
            RATING, \
            VOTES \
            FROM SHOW \
            WHERE %s %s" % (' AND '.join(where), first)))
        return logger.logDebug(dbcur.fetchall())

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
            TYPE, \
            DURATION, \
            VIEWS, \
            RATING, \
            VOTES \
            FROM SHOW"))
        return logger.logDebug(dbcur.fetchall())
         
    def _retrieve(self, mixed, key):
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
            TYPE, \
            DURATION, \
            VIEWS, \
            RATING, \
            VOTES \
            FROM SHOW \
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
                    query = "UPDATE SHOW SET "
                    query += "TITLE = '%s', " % data.get('name') if data.get('name', False) else "TITLE = TITLE, "
                    query += "PARENTID = '%s', " % data.get('parentid') if data.get('parentid', False) else "PARENTID = PARENTID, "
                    query += "PARENTNAME = '%s', " % data.get('parentname') if data.get('parentname', False) else "PARENTNAME = PARENTNAME, "
                    query += "THUMBNAIL = '%s', " % data.get('logo') if data.get('logo', False) else "THUMBNAIL = THUMBNAIL, "
                    query += "FANART = '%s', " % data.get('image') if data.get('image', False) else "FANART = FANART, "
                    query += "IMAGE = '%s', " % data.get('fanart') if data.get('fanart', False) else "IMAGE = IMAGE, "
                    query += "BANNER = '%s', " % data.get('banner') if data.get('banner', False) else "BANNER = BANNER, "
                    query += "URL = '%s', " % data.get('url') if data.get('url', False) else "URL = URL, "
                    query += "DESCRIPTION = '%s', " % data.get('description') if data.get('description', False) else "DESCRIPTION = DESCRIPTION, "
                    query += "SHORTDESCRIPTION = '%s', " % data.get('shortdescription') if data.get('shortdescription', False) else "SHORTDESCRIPTION = SHORTDESCRIPTION, "
                    query += "YEAR = '%s', " % data.get('year') if data.get('year', False) else "YEAR = YEAR, "
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
        logger.logDebug(mixed)
        ids = [str(data['id']) for data in mixed if 'id' in data]
        if len(ids) > 0:
            self.checkIfTableExists()
            dbcur = self.getCursor()
            dbcur.execute('PRAGMA encoding="UTF-8";')
            dbcur.execute(logger.logDebug("DELETE FROM SHOW WHERE ID in (%s)" % ','.join(ids)))
            for data in mixed:
                dbcur.execute(logger.logDebug("INSERT INTO SHOW VALUES (%d, '%s', %d, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', %d, %d, %d, %d)" % (
                    data.get('id'), 
                    data.get('name').replace('\'', '\'\''), 
                    data.get('parentid'), 
                    data.get('parentname').replace('\'', '\'\''), 
                    data.get('logo').replace('&#39;', '\'\''), 
                    data.get('image').replace('&#39;', '\'\''), 
                    data.get('fanart').replace('&#39;', '\'\''), 
                    data.get('banner').replace('&#39;', '\'\''), 
                    data.get('url'), 
                    data.get('description').replace('\'', '\'\''), 
                    data.get('shortdescription').replace('\'', '\'\''), 
                    data.get('year'), 
                    data.get('ltype'), 
                    data.get('duration', 0), 
                    data.get('views', 0), 
                    data.get('rating', 0), 
                    data.get('votes', 0))))
            self._dbcon.commit()
            return True
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
                self._dbcon.commit()
                return True
            except: pass
        return False

    def _drop(self):
        dbcur = self.getCursor()
        try: 
            dbcur.execute(logger.logDebug("DROP TABLE SHOW"))
            self._dbcon.commit()
            return True
        except: 
            return False

    def searchByTitle(self, title, limit=100):
        return self.search({'TITLE' : title}, limit)

    def searchByCategory(self, category, limit=100):
        return self.search({'PARENTNAME' : category}, limit)

    def searchByYear(self, year, limit=100):
        return self.search({'YEAR' : year}, limit)

    def checkIfTableExists(self):
        dbcur = self.getCursor()
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
            TYPE TEXT, \
            DURATION INTEGER NOT NULL DEFAULT 0, \
            VIEWS INTEGER NOT NULL DEFAULT 0, \
            RATING INTEGER NOT NULL DEFAULT 0, \
            VOTES INTEGER NOT NULL DEFAULT 0)"))
        self._dbcon.commit()
        return True
            
    def getStatistics(self):
        stats = {}
        dbcur = self.getCursor()
        dbcur.execute(logger.logDebug("SELECT COUNT(*) FROM SHOW"))
        stats['count'] = dbcur.fetchone()
        return stats


