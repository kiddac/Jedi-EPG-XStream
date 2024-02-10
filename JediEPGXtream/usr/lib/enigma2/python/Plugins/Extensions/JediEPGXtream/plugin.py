#!/usr/bin/python
# -*- coding: utf-8 -*-

# for localized messages
from . import _

# from Components.config import *
from Plugins.Plugin import PluginDescriptor
from enigma import getDesktop, addFont

import os
import shutil

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

if os.path.isdir('/usr/lib/enigma2/python/Plugins/Extensions/XStreamityPro/'):
    try:
        shutil.rmtree('/usr/lib/enigma2/python/Plugins/Extensions/XStreamityPro/')
    except:
        pass

if screenwidth.width() <= 1280:
    skin_directory = "/usr/lib/enigma2/python/Plugins/Extensions/JediEPGXtream/skin/hd/"
elif screenwidth.width() <= 1920:
    skin_directory = "/usr/lib/enigma2/python/Plugins/Extensions/JediEPGXtream/skin/fhd/"
else:
    skin_directory = "/usr/lib/enigma2/python/Plugins/Extensions/JediEPGXtream/skin/uhd/"

# hdr = {'User-Agent': 'Enigma2 - Jedi EPG XStream Plugin'}
hdr = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'}

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
