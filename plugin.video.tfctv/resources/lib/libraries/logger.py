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

import xbmc,inspect

LOGDEBUG = 7
LOGINFO = 6
LOGNOTICE = 5
LOGWARNING = 4
LOGERROR = 3
LOGSEVERE = 2
LOGFATAL = 1
LOGNONE = 0

# Default log level
defaultLogLevel = LOGNONE
plugin = ''
status = False
logLevel = defaultLogLevel

def enable(bool):
    global status
    status = True if bool else False
    
def setLevel(level):
    if (level in (LOGNONE, LOGDEBUG, LOGINFO, LOGNOTICE, LOGWARNING, LOGERROR, LOGSEVERE, LOGFATAL)):
        global logLevel
        logLevel = level
        return True
    return False
    
def log(mixed, level=defaultLogLevel, subFonc=False):
    stackSubLevel = 1 if not subFonc else 2
    if status and logLevel >= level:
        try:
            xbmc.log((u"[%s] %s : '%s'" % (plugin, inspect.stack()[stackSubLevel][3], mixed)).decode("utf-8"), xbmc.LOGNOTICE)
        except:
            xbmc.log(u"[%s] %s : '%s'" % (plugin, inspect.stack()[stackSubLevel][3], repr(mixed)), xbmc.LOGNOTICE)
    return mixed
            
def logDebug(mixed):
    log(mixed, LOGDEBUG, True)
    return mixed

def logInfo(mixed):
    log(mixed, LOGINFO, True)
    return mixed

def logNotice(mixed):
    log(mixed, LOGNOTICE, True)
    return mixed

def logWarning(mixed):
    log(mixed, LOGWARNING, True)
    return mixed
    
def logError(mixed):
    log(mixed, LOGERROR, True)
    return mixed
    
def logSevere(mixed):
    log(mixed, LOGSEVERE, True)
    return mixed
    
def logFatal(mixed):
    log(mixed, LOGFATAL, True)
    return mixed
    
    
