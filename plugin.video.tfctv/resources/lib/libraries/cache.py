# -*- coding: utf-8 -*-

'''
    Tfc.tv Add-on
    Copyright (C) 2016 cmik

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import hashlib
from resources import config
from resources.lib.libraries import control

logger = control.logger

shortCache = None
sCacheFunction = None
longCache = None
lCacheFunction = None
 # execution cache
execCache = {}

# Cache
cacheActive = True if control.setting('cacheActive') == 'true' else False
logger.logInfo('cacheActive : %s' % (cacheActive))
if cacheActive: 
    logger.logInfo('Storage cache enabled')
    try:
       import StorageServer
    except:
       from ressources.lib.dummy import storageserverdummy as StorageServer
    # Short TTL cache
    shortCache = StorageServer.StorageServer(config.shortCache['name'], config.shortCache['ttl']) 
    sCacheFunction = shortCache.cacheFunction
    # Long TTL cache
    longCache = StorageServer.StorageServer(config.longCache['name'], config.longCache['ttl']) 
    lCacheFunction = longCache.cacheFunction
else:
    logger.logInfo('Execution cache enabled')
    from resources.lib.libraries import executioncache
    # Execution cache
    shortCache = executioncache.ExecutionCache(execCache) 
    sCacheFunction = shortCache.cacheFunction
    longCache = shortCache
    lCacheFunction = longCache.cacheFunction
    
    
def generateHashKey(string):
    return hashlib.md5(string).hexdigest()