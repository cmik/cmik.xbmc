# -*- coding: utf-8 -*-

'''
    Tfc.tv Add-on
    Copyright (C) 2018 cmik
'''

class ExecutionCache:
    _execCache = {}
    
    def __init__(self, dict):
        self._execCache = dict
        return None

    def cacheFunction(self, funct=False, *args):
        hash = ''
        for p in args:
            if isinstance(p, dict):
                for key in sorted(p.iterkeys()):
                    hash += "'%s'='%s'" % (key, p[key])
            elif isinstance(p, list):
                hash += ",".join(["%s" % el for el in p])
            else:
                try:
                    hash += p
                except:
                    hash += str(p)
        self._execCache[hash] = funct(*args)
        return self._execCache[hash]

    def set(self, name, data):
        self._execCache[name] = data

    def get(self, name):
        if name in self._execCache:
            return self._execCache[name]
        return ""
        
    def delete(self, name):
        if name in self._execCache:
            del self._execCache[name]

    def setMulti(self, name, data):
        for k, v in data.iteritems():
            key = name + k
            self._execCache[key] = v
        return ""

    def getMulti(self, name, items):
        res = []
        for k in items:
            key = name + k
            if key in self._execCache:
                res.append(self._execCache[key])
            else:
                res.append('')
        return res

    def lock(self, name):
        return False

    def unlock(self, name):
        return False