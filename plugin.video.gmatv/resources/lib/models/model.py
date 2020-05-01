# -*- coding: utf-8 -*-

'''
    GMA.tv Add-on
    Copyright (C) 2020 cmik
'''

try:
    from sqlite3 import dbapi2 as database
except:
    from pysqlite2 import dbapi2 as database

from resources.lib.libraries import control
logger = control.logger
    
class Model():
    
    _dbcon = None

    def __init__(self, databasePath):
        self._dbcon = database.connect(logger.logDebug(databasePath))
        return None
        
    def _getStructure(self, data):
        return {}
        
    def _search(self, limit):
        return []

    def _retrieveAll(self):
        return []
        
    def _retrieve(self, mixed):
        return []
        
    def _save(self, mixed):
        return False        

    def _replace(self, mixed):
        return False
       
    def getCursor(self):
        return self._dbcon.cursor()
    
    def search(self, search, limit=False):
        items = []
        if isinstance(search, dict):
            try:
                results = self._search(search, limit)
                for d in results:
                    items.append(self._getStructure(d))
            except (Exception) as e:
                logger.logError('Exception: %s for data %s' % (str(e), repr(search)))
                pass

        return items

    def getAll(self):
        items = []
        try:
            results = self._retrieveAll()
            for d in results:
                items.append(self._getStructure(d))
        except (Exception) as e:
            logger.logError('Exception: %s' % str(e))
            pass

        return items

    def get(self, mixed, key='ID'):
        search = mixed if isinstance(mixed, list) else [mixed]
        items = []
        try:
            results = self._retrieve(search, key)
            for d in results:
                items.append(self._getStructure(d))
        except (Exception) as e:
            logger.logError('Exception: %s for data %s' % (str(e), repr(mixed)))
            pass

        return items
        
    def set(self, mixed):
        data = mixed if isinstance(mixed, list) else [mixed]
        try:            
            return self._replace(data)
        except (Exception) as e:
            logger.logError('Exception: %s for data %s' % (str(e), repr(mixed)))
            return False
        
    def update(self, mixed):
        data = mixed if isinstance(mixed, list) else [mixed]
        try:            
            return self._save(data)
        except (Exception) as e:
            logger.logError('Exception: %s for data %s' % (str(e), repr(mixed)))
            return False

    def delete(self, mixed):
        search = mixed if isinstance(mixed, list) else [mixed]
        try:
            return self._remove(search)
        except:
            return False
            
    def drop(self):
        try:
            return self._drop()
        except:
            return False

    def execute(self, mixed):
        queries = mixed if isinstance(mixed, list) else [mixed]
        results = []
        try: 
            dbcur = self.getCursor()
            for query in queries:
                dbcur.execute(logger.logDebug(query))
                results.append(dbcur.fetchall())
            return results
        except: 
            return False 

    def executeUpdate(self, mixed):
        queries = mixed if isinstance(mixed, list) else [mixed]
        try: 
            dbcur = self.getCursor()
            for query in queries:
                dbcur.execute(logger.logDebug(query))
            return self._dbcon.commit()
        except: 
            return False 


