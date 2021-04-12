#!/usr/bin/python
# -*- coding: utf-8 -*-

# for localized messages
from . import _

# from Components.config import *
from Plugins.Plugin import PluginDescriptor
from enigma import getDesktop, addFont

import os

screenwidth = getDesktop(0).size()

try:
    cfg = config.plugins.JediMakerXtream
except:
    cfg = ""
    pass

epg_file = '/etc/enigma2/jediepgxtream/epglist.txt'
sourcelist = '/etc/enigma2/jediepgxtream/sources'
json_file = '/etc/enigma2/jediepgxtream/epg.json'

dir_plugins = "/usr/lib/enigma2/python/Plugins/Extensions/JediEPGXtream/"
fontfolder = "/usr/lib/enigma2/python/Plugins/Extensions/JediEPGXtream/fonts/"

if screenwidth.width() > 1280:
    skin_directory = "/usr/lib/enigma2/python/Plugins/Extensions/JediEPGXtream/skin/fhd/"
else:
    skin_directory = "/usr/lib/enigma2/python/Plugins/Extensions/JediEPGXtream/skin/hd/"


hdr = {'User-Agent': 'Enigma2 - Jedi EPG XStream Plugin'}


if os.path.isdir('/usr/lib/enigma2/python/Plugins/Extensions/EPGImport'):
    has_epg_importer = True
    if not os.path.exists('/etc/epgimport'):
        os.makedirs('/etc/epgimport')
else:
    has_epg_importer = False


def main(session, **kwargs):
    from . import main
    session.open(main.JediEPGXtream_Main)
    return


def Plugins(**kwargs):
    addFont(fontfolder + 'm-plus-rounded-1c-regular.ttf', 'jediepgregular', 100, 0)

    iconFile = 'icons/JediEPGXtream.png'
    if screenwidth.width() > 1280:
        iconFile = 'icons/JediEPGXtreamFHD.png'

    description = (_('Assign 3rd Party EPG to IPTV Bouquets'))
    pluginname = (_('JediEPGXtream'))

    result = PluginDescriptor(name=pluginname, description=description, where=PluginDescriptor.WHERE_PLUGINMENU, icon=iconFile, fnc=main)

    return result
