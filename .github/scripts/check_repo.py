#!/usr/bin/env python3
"""Consistency checks on the Kodi repository files.

- addons.xml is valid XML and every <addon> has an id and a version
- addons.xml.md5 holds the md5 of addons.xml and nothing else (Kodi can't read the
  "MD5 (file) = hash" output of the md5 command: use `md5 -q`)
- every add-on listed in addons.xml has its zip in downloads/<id>/<id>-<version>.zip,
  the zip contains an addon.xml with the same id and version, and <id>-latest.zip is the same file
"""
import hashlib
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

errors = []


def fail(message):
    errors.append(message)
    print('ERROR: %s' % message)


try:
    root = ET.parse('addons.xml').getroot()
except Exception as e:
    print('ERROR: addons.xml is not valid XML (%s)' % e)
    sys.exit(1)

with open('addons.xml', 'rb') as f:
    expected = hashlib.md5(f.read()).hexdigest()
with open('addons.xml.md5', encoding='utf-8') as f:
    actual = f.read()
if not re.fullmatch(r'[0-9a-f]{32}\n?', actual):
    fail('addons.xml.md5 must contain only the 32 characters of the hash; regenerate it with: '
         'md5 -q addons.xml | tr -d "\\n" > addons.xml.md5')
elif actual.strip() != expected:
    fail('addons.xml.md5 is %s but addons.xml has the md5 %s' % (actual.strip(), expected))


def sha(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


addons = root.findall('addon')
if not addons:
    fail('addons.xml lists no add-on')
for addon in addons:
    addonId, version = addon.get('id'), addon.get('version')
    if not addonId or not version:
        fail('an <addon> of addons.xml has no id or version')
        continue
    zipPath = os.path.join('downloads', addonId, '%s-%s.zip' % (addonId, version))
    latestPath = os.path.join('downloads', addonId, '%s-latest.zip' % addonId)
    if not os.path.isfile(zipPath):
        fail('%s %s is listed in addons.xml but %s does not exist' % (addonId, version, zipPath))
        continue
    if not os.path.isfile(latestPath):
        fail('%s does not exist' % latestPath)
    elif sha(latestPath) != sha(zipPath):
        fail('%s is not the same file as %s' % (latestPath, zipPath))
    try:
        with zipfile.ZipFile(zipPath) as z:
            names = [n for n in z.namelist() if re.fullmatch(r'[^/]+/addon\.xml', n)]
            if len(names) != 1:
                fail('%s should contain exactly one <folder>/addon.xml (found %d)' % (zipPath, len(names)))
                continue
            inner = ET.fromstring(z.read(names[0]))
    except (zipfile.BadZipFile, ET.ParseError) as e:
        fail('%s is not a valid zip/addon.xml (%s)' % (zipPath, e))
        continue
    if inner.get('id') != addonId or inner.get('version') != version:
        fail('%s contains %s %s but addons.xml lists %s %s' % (
            zipPath, inner.get('id'), inner.get('version'), addonId, version))

if errors:
    sys.exit(1)
print('OK: %d add-ons, md5, zips and latest zips are consistent' % len(addons))
