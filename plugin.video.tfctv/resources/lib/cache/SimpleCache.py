import xbmc, xbmcaddon, os, time
try:
    import cPickle as pickle
except ImportError:
    import pickle as pickle


class SimpleCache(object):

    _cachePath = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
    _fileSuffix = os.extsep + 'cache'
    _expirySeconds = 0
    
    def __init__(self, expirySeconds):
        self._expirySeconds = expirySeconds
        
    def set(self, key, value):
        o = (time.time(), value)
        with(open(os.path.join(self._cachePath, key + self._fileSuffix), 'wb')) as f:
            pickle.dump(o, f)
        
    def get(self, key):
        o = (0, None)
        cacheFile = os.path.join(self._cachePath, key + self._fileSuffix)
        if os.path.exists(cacheFile):
            with(open(cacheFile, 'rb')) as f:
                o = pickle.load(f)
            expiry = o[0] + self._expirySeconds
            if expiry > time.time():
                return o[1]
            else:
                self.delete(key)
                return None
        else:
            return None
        
    def delete(self, key):
        os.remove(os.path.join(self._cachePath, key + self._fileSuffix))
        
    def clear(self):
        filelist = [ f for f in os.listdir(self._cachePath) if f.endswith(self._fileSuffix) ]
        for f in filelist:
            os.remove(os.path.join(self._cachePath, f))
            
    def cleanCache(self, sinceSeconds):
        lastPurgeFile = os.path.join(self._cachePath, 'lastPurge.cache')
        o = None
        if os.path.exists(lastPurgeFile):
            with(open(lastPurgeFile, 'rb')) as f:
                o = pickle.load(f)
        if o == None:
            with(open(lastPurgeFile, 'wb')) as f:
                pickle.dump(time.time(), f)
        else:
            if (o + sinceSeconds) < time.time():
                self.clear()
                with(open(lastPurgeFile, 'wb')) as f:
                    pickle.dump(time.time(), f)