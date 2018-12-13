# -*- coding: utf-8 -*-

'''
    Tfc.tv Add-on
    Copyright (C) 2018 cmik
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
        self._dbcon = database.connect(databasePath)
        return None
        
    def _getStructure(self, data):
        return {}
        
    def _retrieve(self, mixed):
        return []
        
    def _save(self, mixed):
        return False
       
    def getCursor(self):
        return self._dbcon.cursor()
    
    def get(self, mixed):
        search = mixed if isinstance(mixed, list) else [mixed]
        items = []
        try:
            results = self._retrieve(search)
            for d in results:
                items.append(self._getStructure(d))
        except (Exception) as e:
            logger.logError('Exception: %s for data %s' % (str(e), repr(mixed)))
            pass

        return items
        
    def set(self, mixed):
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
        return False


